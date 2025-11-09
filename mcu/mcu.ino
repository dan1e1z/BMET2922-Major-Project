/*
** Author: Harneet Kaur Dhaliwal, Gladys De Euphrates, Daniel Lindsay-Shad
*/

#include "switch.h"
#include "pulse_sim.h"
#include <BluetoothSerial.h>
#include <PeakDetection.h>
#include <Filters.h>

// === Pin definitions ===
#define PULSE_LED_PIN 32
#define BLE_LED_PIN   14
#define MODE_LED_PIN  12
#define PPG_PIN       25
#define BUTTON_PIN    33

// === Timing ===
#define TICK_20MS 20000  // microseconds

// === Sampling constants ===
#define SAMPLE_FREQ    50
#define LAG            30
#define THRESHOLD      2.5
#define INFLUENCE      0.5

// === Adaptive thresholding constants ===
#define ADAPTIVE_WINDOW_SAMPLES 100  // 2 seconds at 50Hz
#define ADAPTIVE_RATIO           70

// === Heart rate limits ===
#define MIN_HEART_RATE 40
#define MAX_HEART_RATE 200

// === Bandpass filter ===
#define CUTOFF_FREQ_LOW 0.5      // Hz - filters out DC offset & baseline wander (30 BPM)
#define CUTOFF_FREQ_HIGH 4.0     // Hz - filters out high frequency noise (240 BPM)
#define SAMPLING_FREQ 50.0       // Hz (20ms per sample)

BluetoothSerial SerialBT;

struct __attribute__((packed)) heartpacket {
  uint32_t sequenceNumber;     // 4 bytes
  uint16_t rawData[50];        // 2 bytes * 50 = 100 bytes
  float bpm;                   // 4 bytes
  uint8_t mode;                // 1 byte
};                             // Total = 4 + 100 + 4 + 1 = 109 bytes

heartpacket packet;

// === Bandpass filters ===
FilterOnePole highpass_filter(HIGHPASS, CUTOFF_FREQ_LOW);
FilterOnePole lowpass_filter(LOWPASS, CUTOFF_FREQ_HIGH);

// === Timing variables ===
unsigned long last_tick_time = 0;
unsigned long last_blink_time = 0;

// === Sample index ===
uint16_t SampleIndex = 0;
bool heart_packet_ready = false;

// === Detection variables ===
float bpm = 0;
unsigned long last_beat_time = 0;
bool mode = false;   // false = Adaptive, true = PeakDetection

// === BLE LED ===
bool bt_led_state = false;

// === Adaptive buffer ===
uint16_t adaptive_buf[ADAPTIVE_WINDOW_SAMPLES];
uint16_t adaptive_buf_index = 0;

// === Helpers ===
Switch button(1, 5);
Switch pulse(1, 1);
PeakDetection peakDetection;

// === Timing function ===
bool tick_20ms() {
    if ((micros() - last_tick_time) >= TICK_20MS) {
        last_tick_time += TICK_20MS;
        return true;
    }
    return false;
}

// === Get adaptive threshold ===
uint16_t get_threshold() {
    uint16_t min_val = 4095;
    uint16_t max_val = 0;
    
    for (int i = 0; i < ADAPTIVE_WINDOW_SAMPLES; i++) {
        if (adaptive_buf[i] < min_val) min_val = adaptive_buf[i];
        if (adaptive_buf[i] > max_val) max_val = adaptive_buf[i];
    }
    
    return min_val + (uint16_t)((max_val - min_val) * ADAPTIVE_RATIO / 100.0);
}

// === Calculate heart rate ===
void calculate_heart_rate() {
    if (pulse.changed() && pulse.state()) {
        unsigned long now = millis();
        if (last_beat_time > 0) {
            unsigned long period = now - last_beat_time;
            if (period > 0) {
                float calculated_bpm = 60000.0 / period;
                if (calculated_bpm >= MIN_HEART_RATE && calculated_bpm <= MAX_HEART_RATE) {
                    bpm = calculated_bpm;
                }
            }
        }
        last_beat_time = now;
    }
}

// === Adaptive threshold-based pulse rate detection ===
void updatePulseRate(uint16_t raw, uint16_t filtered) {
    adaptive_buf[adaptive_buf_index] = filtered;
    adaptive_buf_index = (adaptive_buf_index + 1) % ADAPTIVE_WINDOW_SAMPLES;

    uint16_t adaptive_threshold = get_threshold();
    bool beat_detected = false;
    pulse.update(filtered > adaptive_threshold);
    
    // Detect rising edge for beat
    if (pulse.changed() && pulse.state()) {
        beat_detected = true;
    }
    
    calculate_heart_rate();
    
    // Print to serial plotter
    Serial.print("Raw:");
    Serial.print(raw);
    Serial.print(" ");
    Serial.print("Filtered:");
    Serial.print(filtered);
    Serial.print(" ");
    Serial.print("Threshold:");
    Serial.print(adaptive_threshold);
    Serial.print(" ");
    Serial.print("Beat:");
    Serial.print(beat_detected ? filtered : 0);
    Serial.print(" ");
    Serial.print("HR:");
    Serial.println(bpm);
}

// === Peak detection method ===
void z_peak_detection(uint16_t raw, uint16_t filtered) {
    double processed_signal = ((double)filtered / 4095.0);
    peakDetection.add(processed_signal);
    
    bool peak = (peakDetection.getPeak() == 1);
    pulse.update(peak);
    
    calculate_heart_rate();
    
    // Print to serial plotter
    Serial.print("Raw:");
    Serial.print(raw);
    Serial.print(" ");
    Serial.print("Filtered:");
    Serial.print(filtered);
    Serial.print(" ");
    Serial.print("Beat:");
    Serial.print(peak ? filtered : 0);
    Serial.print(" ");
    Serial.print("HR:");
    Serial.println(bpm);
}

// === Update pulse ===
void update_pulse() {
    // uint16_t PPG_Reader = analogRead(PPG_PIN);
    uint16_t PPG_Reader = pulse_sim();

    // Apply bandpass filter (highpass first to remove DC, then lowpass to remove noise)
    float filtered = (float)PPG_Reader;
    filtered = highpass_filter.input(filtered);
    filtered = lowpass_filter.input(filtered);
    uint16_t filtered_raw = (uint16_t)constrain(filtered, 0, 4095);

    // Store raw data in packet
    packet.rawData[SampleIndex] = PPG_Reader;
    SampleIndex++;
    
    if (SampleIndex >= 50) {
        SampleIndex = 0;
        packet.bpm = bpm;
        packet.mode = mode ? 1 : 0;
        packet.sequenceNumber++;
        heart_packet_ready = true;
    }

    // Run chosen detection method with filtered data
    if (!mode) {
        updatePulseRate(PPG_Reader, filtered_raw);
    } else {
        z_peak_detection(PPG_Reader, filtered_raw);
    }
    
    // Update pulse LED - follows pulse state
    digitalWrite(PULSE_LED_PIN, pulse.state() ? HIGH : LOW);
}

// === Button handling ===
void update_button() {
    bool reading = digitalRead(BUTTON_PIN);
    bool changed = button.update(reading);
    bool state = button.state();
    
    if (changed && state) {
        // Button pressed (rising edge)
        mode = !mode;
        digitalWrite(MODE_LED_PIN, mode ? HIGH : LOW);
        Serial.print("Mode changed to: ");
        Serial.println(mode ? "PeakDetection" : "Adaptive");
    }
}

// === BLE LED ===
void update_bluetooth_led() {
    if (SerialBT.hasClient()) {
        digitalWrite(BLE_LED_PIN, HIGH);
    } else {
        // Blink every 500ms when disconnected
        if (millis() - last_blink_time >= 500) {
            last_blink_time = millis();
            bt_led_state = !bt_led_state;
            digitalWrite(BLE_LED_PIN, bt_led_state ? HIGH : LOW);
        }
    }
}

// === Send packet ===
void sendHeartPacket() {
    if (SerialBT.hasClient()) {
        SerialBT.write((uint8_t*)&packet, sizeof(packet));
    }
}

// === Setup ===
void setup() {
    pinMode(PPG_PIN, INPUT);
    pinMode(BUTTON_PIN, INPUT_PULLDOWN);
    pinMode(PULSE_LED_PIN, OUTPUT);
    pinMode(BLE_LED_PIN, OUTPUT);
    pinMode(MODE_LED_PIN, OUTPUT);

    digitalWrite(BLE_LED_PIN, LOW);
    digitalWrite(PULSE_LED_PIN, LOW);
    digitalWrite(MODE_LED_PIN, LOW);

    Serial.begin(115200);
    delay(1000);
    Serial.println("\nPPG Heart Rate Monitor");
    SerialBT.begin("PPG_HeartRate_Monitor");

    peakDetection.begin(LAG, THRESHOLD, INFLUENCE);
    
    last_tick_time = micros();
    memset(adaptive_buf, 0, sizeof(adaptive_buf));
    memset(&packet, 0, sizeof(packet));

    Serial.println("System initialized.");
}

// === Main loop ===
void loop() {
    if (tick_20ms()) {
        update_button();
        update_bluetooth_led();
        update_pulse();
        
        if (heart_packet_ready) {
            sendHeartPacket();
            heart_packet_ready = false;
        }
    }
}