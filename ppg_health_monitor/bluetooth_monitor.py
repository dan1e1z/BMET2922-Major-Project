from PyQt5 import QtCore
import struct
import serial
import time

TIMEOUT = 2

class BluetoothMonitor(QtCore.QObject):
    """
    Monitors a single serial port (Bluetooth SPP on ESP32) for incoming data packets.
    """
    packet_received = QtCore.pyqtSignal(dict)
    connection_status_changed = QtCore.pyqtSignal(bool, str)
    connection_timeout = QtCore.pyqtSignal()

    def __init__(self, port="COM8", baudRate=115200):
        super().__init__()
        self.port = port
        self.baudRate = baudRate
        self.serialPort = None
        self.running = True
        self.STRUCT_FORMAT = "<L50HBB"
        self.STRUCT_SIZE = struct.calcsize(self.STRUCT_FORMAT)
        self.last_packet_time = 0

    def connect(self, retry_interval=1, max_duration=10):
        """
        Attempt to open the serial port repeatedly for up to max_duration seconds.
        """
        start_time = time.time()
        while time.time() - start_time < max_duration:
            print(f"** Attempting to connect to {self.port}...")
            try:
                self.serialPort = serial.Serial(
                    port=self.port,
                    baudrate=self.baudRate,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=1
                )
                if self.serialPort.is_open:
                    print("**************************************")
                    print(f"** Serial port opened: {self.port}")
                    print("**************************************")
                    self.connection_status_changed.emit(True, f"Connected to {self.port}")
                    self.last_packet_time = time.time()
                    return True
            except serial.SerialException as e:
                print(f"Error opening port {self.port}: {e}. Retrying in {retry_interval} seconds...")
                self.connection_status_changed.emit(False, f"Failed to connect: {e}")
                time.sleep(retry_interval)
        print(f"Failed to connect to {self.port} within {max_duration} seconds.")
        return False

    def monitor(self):
        """
        Main loop: reads packets, handles timeouts, and reconnects if needed.
        """
        while self.running:
            if not self.serialPort or not self.serialPort.is_open:
                if not self.connect():
                    time.sleep(1)
                    continue

            try:
                if self.serialPort.in_waiting >= self.STRUCT_SIZE:
                    packet = self.serialPort.read(self.STRUCT_SIZE)
                    if len(packet) == self.STRUCT_SIZE:
                        data = struct.unpack(self.STRUCT_FORMAT, packet)
                        packet_dict = {
                            "sequence": data[0],
                            "ppg_values": data[1:51],
                            "bpm": data[51],
                            "temp": data[52]
                        }
                        # TESTING DEBUGGING PRINTS
                        # print(f"Received packet: {packet_dict['sequence']}")
                        # print(f"Received packet: {packet_dict['bpm']}")
                        self.packet_received.emit(packet_dict)
                        self.last_packet_time = time.time()
                    else:
                        print("Incomplete packet received. Discarding.")
                        self.serialPort.reset_input_buffer()

                # Timeout check
                if time.time() - self.last_packet_time > TIMEOUT:
                    print(f"No data received for {TIMEOUT}s. Reconnecting...")
                    self.connection_timeout.emit()
                    if self.serialPort and self.serialPort.is_open:
                        self.serialPort.close()
                    self.connection_status_changed.emit(False, "Disconnected: Timeout")
                    self.connect()

            except Exception as e:
                print(f"Unexpected error: {e}")
                if self.serialPort and self.serialPort.is_open:
                    self.serialPort.close()
                self.connection_status_changed.emit(False, f"Error: {e}")
                time.sleep(1)
