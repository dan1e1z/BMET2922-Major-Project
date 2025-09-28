from PyQt5 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
import numpy as np
from datetime import datetime
import neurokit2 as nk
from scipy import signal
from collections import deque

class LiveMonitorTab(QtWidgets.QWidget):
    """
    A PyQt5 widget for real-time physiological monitoring.

    This tab provides a user interface for visualizing live photoplethysmography (PPG)
    data, from which it calculates and displays heart rate (BPM), heart rate
    variability (HRV) metrics, and respiratory rate (RR). It includes features
    for session management, data logging, and configurable BPM alarm thresholds.
    """
    
    def __init__(self, system_log):
        """
        Initializes the LiveMonitorTab widget.

        Args:
            system_log: A logging object for displaying system messages.
        """
        super().__init__()

        # Core system references
        self.system_log = system_log

        # Session management
        self.current_user = None
        self.session_start_time = None
        self.session_raw_ppg = []
        self.session_bpm = []

        # Signal processing - Fixed 60-second buffer for efficiency
        self.sampling_rate = 50
        self.buffer_duration = 60  # seconds
        self.buffer_size = self.sampling_rate * self.buffer_duration  # 3000 samples
        
        # Use deque for O(1) append/popleft operations
        self.ppg_buffer = deque(maxlen=self.buffer_size)
        self.ppg_times = deque(maxlen=self.buffer_size)
        
        # Visualization data - separate from processing buffer
        self.visual_ppg_data = []
        self.visual_bpm_data = [0]
        self.time_ppg_data = []
        self.time_bpm_data = [0]
        
        # Physiological metrics - Initialize with starting values for live monitoring
        self.ibi_data = deque([0], maxlen=1000)  # Start with 0 at time=0
        self.ibi_times = deque([0], maxlen=1000)
        self.rr_data = deque([0], maxlen=300)    # Start with 0 at time=0
        self.rr_times = deque([0], maxlen=300)
        self.peak_times = deque(maxlen=500)
        self.peak_amplitudes = deque(maxlen=500)
        self.hrv_metrics = {}
        
        # Current values for live updating
        self.current_ibi = 0
        self.current_rr = 0

        # Timing and state
        self.last_packet_time = 0
        self.last_hrv_update = 0
        self.last_peak_time = -1
        self.last_ibi_time = -1
        
        # UI state - only essential settings
        self.plot_window_seconds = 10
        self.is_auto_scrolling = True
        self.current_bpm = 0
        self.bpm_low = 40
        self.bpm_high = 200
        self.alarm_active = False

        # Initialize UI
        self.setup_ui()

    def setup_ui(self):
        """
        Configures and arranges all UI elements for the monitoring tab.
        
        This method initializes the plot widgets, control panels, sliders,
        and labels that make up the tab's interface.
        """
        main_layout = QtWidgets.QVBoxLayout()

        # === PLOTS PANEL ===
        plots_layout = QtWidgets.QVBoxLayout()

        # --- BPM Plot ---
        # Create the plot widget and the main heart rate curve
        self.bpm_plot = pg.PlotWidget()
        self.bpm_plot.setTitle("Heart Rate (BPM)")
        self.bpm_plot.setLabel('left', 'BPM')
        self.bpm_plot.setLabel('bottom', 'Time', units='s')
        self.bpm_plot.showGrid(True, True)
        self.bpm_plot.setMouseEnabled(x=False, y=False)
        self.bpm_plot.setMenuEnabled(False)

        # Add legend
        self.bpm_legend = self.bpm_plot.addLegend(offset=(-1, -1))

        self.bpm_curve = self.bpm_plot.plot(
            pen=pg.mkPen('r', width=2),
            name='Heart Rate'
        )

        # Average line
        self.avg_bpm_line = pg.InfiniteLine(
            angle=0, 
            pen=pg.mkPen(QtGui.QColor("#FFA726"), width=2, style=QtCore.Qt.DashLine)
        )
        self.bpm_plot.addItem(self.avg_bpm_line)

        # Add custom legend entry for the average line
        sample_item = pg.PlotDataItem(pen=pg.mkPen("#FFA726", width=2, style=QtCore.Qt.DashLine))
        self.bpm_legend.addItem(sample_item, "Average BPM")

        # Add the plot to layout
        plots_layout.addWidget(self.bpm_plot, stretch=2)
        # --- Raw PPG Plot ---
        self.raw_ppg_plot = pg.PlotWidget()
        self.raw_ppg_plot.setTitle("Raw PPG Signal")
        self.raw_ppg_plot.setLabel('left', 'PPG Amplitude')
        self.raw_ppg_plot.setLabel('bottom', 'Time', units='s')
        self.raw_ppg_plot.showGrid(True, True)
        self.raw_ppg_plot.setMouseEnabled(x=False, y=False)
        self.raw_ppg_plot.setMenuEnabled(False)
        
        # Add legend positioned alongside the title (top-left, higher up)
        self.ppg_legend = self.raw_ppg_plot.addLegend(offset=(-1, -1))
        
        self.raw_ppg_curve = self.raw_ppg_plot.plot(
            pen=pg.mkPen('b', width=2),
            name='PPG Signal'
        )
        
        # Add scatter plot item to mark detected R-peaks on the PPG signal.
        self.peak_scatter = pg.ScatterPlotItem(
            pen=pg.mkPen(color='red'), 
            brush=pg.mkBrush(color='red'), 
            size=8, 
            symbol='o',
            name='Detected Peaks'
        )
        self.raw_ppg_plot.addItem(self.peak_scatter)
        plots_layout.addWidget(self.raw_ppg_plot, stretch=2)

        # --- IBI Tachogram Plot (Initially Hidden) ---
        self.ibi_plot = pg.PlotWidget()
        self.ibi_plot.setTitle("Inter-Beat Intervals (IBI)")
        self.ibi_plot.setLabel('left', 'IBI', units='ms') 
        self.ibi_plot.setLabel('bottom', 'Time', units='s')
        self.ibi_plot.showGrid(True, True)
        self.ibi_plot.setMouseEnabled(x=False, y=False)
        self.ibi_plot.setMenuEnabled(False)
        
        # Add legend positioned alongside the title (top-left, higher up)
        self.ibi_legend = self.ibi_plot.addLegend(offset=(-1, -1))
        
        self.ibi_curve = self.ibi_plot.plot(
            pen=pg.mkPen(QtGui.QColor("#6A1B9A"), width=2), 
            symbol='o', 
            symbolSize=6,
            symbolBrush=pg.mkBrush(QtGui.QColor("#6A1B9A")),
            name='Inter-Beat Intervals'
        )
        self.ibi_plot.setVisible(False)
        plots_layout.addWidget(self.ibi_plot, stretch=2)

        # --- Respiratory Rate Plot (Initially Hidden) ---
        self.rr_plot = pg.PlotWidget()
        self.rr_plot.setTitle("Respiratory Rate")
        self.rr_plot.setLabel('left', 'Breaths/min')
        self.rr_plot.setLabel('bottom', 'Time', units='s')
        self.rr_plot.showGrid(True, True)
        self.rr_plot.setMouseEnabled(x=False, y=False)
        self.rr_plot.setMenuEnabled(False)
        
        # Add legend positioned alongside the title (top-left, higher up)
        self.rr_legend = self.rr_plot.addLegend(offset=(-1, -1))
        
        self.rr_curve = self.rr_plot.plot(
            pen=pg.mkPen(QtGui.QColor("#00695C"), width=2), 
            name='Respiratory Rate'
        )
        self.rr_plot.setVisible(False)
        plots_layout.addWidget(self.rr_plot, stretch=2)

        # --- Plot Controls (Slider, Checkbox, and Time Window Selector) ---
        plot_controls_layout = QtWidgets.QHBoxLayout()

        # Checkbox to enable or disable auto-scrolling.
        self.auto_scroll_checkbox = QtWidgets.QCheckBox("Auto-Scroll")
        self.auto_scroll_checkbox.setChecked(self.is_auto_scrolling)
        self.auto_scroll_checkbox.stateChanged.connect(self.toggle_auto_scroll)
        plot_controls_layout.addWidget(self.auto_scroll_checkbox)

        # Slider for manually scrolling through the plot history.
        self.plot_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.plot_slider.setRange(0, 0)
        self.plot_slider.valueChanged.connect(self.scroll_plots)
        self.plot_slider.sliderPressed.connect(self.disable_auto_scroll)
        plot_controls_layout.addWidget(self.plot_slider)

        # Dropdown to select the visible time window duration.
        window_label = QtWidgets.QLabel("Time Window:")
        window_label.setStyleSheet("QLabel { font-weight: bold; }")
        self.window_selector = QtWidgets.QComboBox()
        self.window_selector.addItems(["5s", "10s", "30s", "60s"])
        self.window_selector.setCurrentText("10s")
        self.window_selector.currentTextChanged.connect(self.update_time_window)
        plot_controls_layout.addWidget(window_label)
        plot_controls_layout.addWidget(self.window_selector)
        plots_layout.addLayout(plot_controls_layout)

        # Label to display current session information.
        self.session_info = QtWidgets.QLabel("Not logged in")
        self.session_info.setAlignment(QtCore.Qt.AlignRight)
        plots_layout.addWidget(self.session_info)

        # === CONTROLS & INFO PANEL ===
        controls_widget = QtWidgets.QWidget()
        controls_layout = QtWidgets.QVBoxLayout()
        controls_layout.setSpacing(15)

        # --- Heart Rate Panel ---
        bpm_group = QtWidgets.QGroupBox("Heart Rate")
        bpm_layout = QtWidgets.QVBoxLayout(bpm_group)
        self.bpm_display = QtWidgets.QLabel("-- BPM")
        self.bpm_display.setAlignment(QtCore.Qt.AlignCenter)
        self.bpm_display.setStyleSheet("font-size: 28px; font-weight: bold; color: #2E7D32;")
        self.bpm_status = QtWidgets.QLabel("Monitoring...")
        self.bpm_status.setAlignment(QtCore.Qt.AlignCenter)
        bpm_layout.addWidget(self.bpm_display)
        bpm_layout.addWidget(self.bpm_status)
        controls_layout.addWidget(bpm_group)

        # --- HRV Metrics Panel ---
        hrv_group = QtWidgets.QGroupBox("HRV Metrics")
        hrv_layout = QtWidgets.QVBoxLayout(hrv_group)
        self.hrv_display = QtWidgets.QLabel("Calculating...")
        self.hrv_display.setAlignment(QtCore.Qt.AlignCenter)
        self.hrv_display.setStyleSheet("font-family: monospace; font-size: 10px;")
        self.hrv_display.setWordWrap(True)
        hrv_layout.addWidget(self.hrv_display)
        controls_layout.addWidget(hrv_group)

        # --- Respiratory Rate Panel ---
        rr_group = QtWidgets.QGroupBox("Respiratory Rate")
        rr_layout = QtWidgets.QVBoxLayout(rr_group)
        self.rr_display = QtWidgets.QLabel("-- breaths/min")
        self.rr_display.setAlignment(QtCore.Qt.AlignCenter)
        self.rr_display.setStyleSheet("font-size: 18px; font-weight: bold; color: #00695C;")
        rr_layout.addWidget(self.rr_display)
        controls_layout.addWidget(rr_group)

        # --- Display Options Panel ---
        display_group = QtWidgets.QGroupBox("Display Options")
        display_layout = QtWidgets.QVBoxLayout(display_group)
        
        self.ibi_toggle = QtWidgets.QCheckBox("Show IBI Plot")
        self.ibi_toggle.stateChanged.connect(self.toggle_ibi_plot)
        display_layout.addWidget(self.ibi_toggle)
        
        self.rr_toggle = QtWidgets.QCheckBox("Show RR Plot")
        self.rr_toggle.stateChanged.connect(self.toggle_rr_plot)
        display_layout.addWidget(self.rr_toggle)
        
        self.legend_toggle = QtWidgets.QCheckBox("Show Plot Legends")
        self.legend_toggle.setChecked(True)  # Default to showing legends
        self.legend_toggle.stateChanged.connect(self.toggle_legends)
        display_layout.addWidget(self.legend_toggle)
        
        controls_layout.addWidget(display_group)

        # --- Alarm Thresholds Panel ---
        thresholds_group = QtWidgets.QGroupBox("BPM Thresholds")
        thresholds_layout = QtWidgets.QVBoxLayout(thresholds_group)
        self.low_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.low_slider.setRange(20, 100)
        self.low_slider.setValue(self.bpm_low)
        self.low_slider.valueChanged.connect(self.update_thresholds)
        self.high_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.high_slider.setRange(120, 250)
        self.high_slider.setValue(self.bpm_high)
        self.high_slider.valueChanged.connect(self.update_thresholds)
        self.low_label = QtWidgets.QLabel(f"Low BPM Warning: {self.bpm_low}")
        self.high_label = QtWidgets.QLabel(f"High BPM Warning: {self.bpm_high}")
        thresholds_layout.addWidget(self.low_label)
        thresholds_layout.addWidget(self.low_slider)
        thresholds_layout.addWidget(self.high_label)
        thresholds_layout.addWidget(self.high_slider)
        controls_layout.addWidget(thresholds_group)
        
        # --- Alarm Display Widget ---
        self.alarm_widget = QtWidgets.QLabel("")
        self.alarm_widget.setAlignment(QtCore.Qt.AlignCenter)
        self.alarm_widget.setStyleSheet("QLabel { background-color: #ff0000; color: white; font-weight: bold; padding: 10px; }")
        self.alarm_widget.setVisible(False)
        controls_layout.addWidget(self.alarm_widget)

        # --- Current Statistics Display ---
        self.current_stats = QtWidgets.QLabel("")
        self.current_stats.setAlignment(QtCore.Qt.AlignCenter)
        self.current_stats.setWordWrap(True)
        controls_layout.addWidget(self.current_stats)
        
        controls_layout.addStretch()
        controls_widget.setLayout(controls_layout)

        # --- Main Layout Assembly ---
        content_layout = QtWidgets.QHBoxLayout()
        content_layout.addLayout(plots_layout, 3)
        content_layout.addWidget(controls_widget, 1)
        
        main_layout.addLayout(content_layout)
        main_layout.addWidget(self.system_log)
        self.setLayout(main_layout)

        # --- Timers ---
        self.alarm_timer = QtCore.QTimer()
        self.alarm_timer.timeout.connect(self.blink_alarm)
        self.alarm_visible = True

        self.update_timer = QtCore.QTimer()
        self.update_timer.timeout.connect(self.update_session_info)
        self.update_timer.start(1000)
        
        # Initialize legends state
        self.toggle_legends(QtCore.Qt.Checked)  # Show legends by default

    def new_data_received(self, packet):
        """
        Process new data packet, generate timestamps, and update plots.
        """
        bpm = packet['bpm']
        self.current_bpm = bpm
        
        current_time = self.last_packet_time
        self.last_packet_time += 1

        # Handle BPM display and alarm logic
        alarm_msg = None
        if bpm > 0:
            self.bpm_display.setText(f"{bpm:.1f} BPM")
            alarm_msg = self.check_bpm_alarm()
            
            if self.current_user:
                self.session_bpm.append(bpm)
                self.session_raw_ppg.extend(packet["ppg_values"])
        else:
            self.bpm_display.setText("-- BPM")

        # Store BPM data point for visualization
        self.visual_bpm_data.append(bpm)
        self.time_bpm_data.append(self.last_packet_time)
        
        # Store PPG data for the interval [t, t+1)
        ppg_values = packet["ppg_values"]
        ppg_times = np.linspace(current_time, self.last_packet_time, len(ppg_values), endpoint=False)

        # Add PPG data to visualization buffers
        self.visual_ppg_data.extend(ppg_values)
        self.time_ppg_data.extend(ppg_times)

        # Add PPG data to processing buffer (deque automatically maintains size)
        self.ppg_buffer.extend(ppg_values)
        self.ppg_times.extend(ppg_times)

        # Process PPG signal for HRV and RR analysis
        if len(self.ppg_buffer) > self.sampling_rate * 5:  # Need at least 5 seconds of data
            self.process_ppg_signal()
        
        # Update IBI and RR plots every second for live monitoring
        self.update_physiological_metrics()

        self.update_plots()
        
        return alarm_msg 

    def process_ppg_signal(self):
        """Process PPG signal to extract R-peaks, calculate IBI, HRV, and estimate RR."""
        ppg_signal = np.array(self.ppg_buffer)
        ppg_times_array = np.array(self.ppg_times)
        
        # Clean and find peaks using the more comprehensive method
        ppg_cleaned = nk.ppg_clean(ppg_signal, sampling_rate=self.sampling_rate, method="elgendi")
        _, info = nk.ppg_peaks(ppg_cleaned, sampling_rate=self.sampling_rate, method="elgendi")
        
        peak_indices = info.get("PPG_Peaks", [])
        if len(peak_indices) == 0:
            return
            
        peak_times = ppg_times_array[peak_indices]
        peak_amplitudes = ppg_signal[peak_indices]

        self._update_peaks(peak_times, peak_amplitudes)
        self._update_ibis(peak_times)

        # Update HRV every 5 seconds
        if self.last_packet_time - self.last_hrv_update >= 5:
            self.calculate_hrv_metrics()
            self.last_hrv_update = self.last_packet_time

        # Estimate respiratory rate
        self.estimate_respiratory_rate(ppg_cleaned)

    def estimate_respiratory_rate(self, ppg_cleaned):
        """Estimate respiratory rate from PPG signal using frequency analysis."""
        
        # Apply bandpass filter for respiratory frequencies (0.1-0.5 Hz = 6-30 breaths/min)
        sos = signal.butter(2, [0.1, 0.5], btype='band', fs=self.sampling_rate, output='sos')
        filtered = signal.sosfilt(sos, ppg_cleaned)
        
        # Find peaks in the filtered signal (min 2 seconds between breaths)
        peaks, _ = signal.find_peaks(filtered, distance=self.sampling_rate * 2)
        
        if len(peaks) < 2:
            # Keep current RR value when insufficient peaks detected
            self.current_rr = 0
            self.rr_display.setText("0.0 breaths/min")
            return
        
        # Calculate respiratory rate from peak intervals
        peak_intervals = np.diff(peaks) / self.sampling_rate  # Convert to seconds
        mean_interval = np.mean(peak_intervals)
        rr = 60 / mean_interval  # Convert to breaths/min
        
        # Update current RR value
        self.current_rr = rr
        self.rr_display.setText(f"{rr:.1f} breaths/min")
    
    def update_physiological_metrics(self):
        """Update IBI and RR data points every second for live monitoring."""
        # Add current IBI value every second (even if no new calculation)
        self.ibi_data.append(self.current_ibi)
        self.ibi_times.append(self.last_packet_time)
        
        # Add current RR value every second (even if no new calculation)
        self.rr_data.append(self.current_rr)
        self.rr_times.append(self.last_packet_time)

    def calculate_hrv_metrics(self):
        """Calculate HRV metrics from IBI data."""
        if len(self.ibi_data) < 10:  # Need minimum IBIs for meaningful calculation
            return
            
        # Use available IBI data (deque automatically limits size)
        rr_intervals = np.array(self.ibi_data)
        
        # Calculate HRV metrics
        rmssd = np.sqrt(np.mean(np.diff(rr_intervals)**2))
        sdnn = np.std(rr_intervals)
        mean_rr = np.mean(rr_intervals)
        
        # Calculate pNN50
        diff_rr = np.abs(np.diff(rr_intervals))
        if len(diff_rr) > 0:
            nn50 = np.sum(diff_rr > 50)
            pnn50 = (nn50 / len(diff_rr)) * 100
        else:
            pnn50 = 0
        
        # Poincare plot parameters
        sd1 = np.sqrt(0.5 * rmssd**2)
        sd2 = max(np.sqrt(2 * sdnn**2 - 0.5 * rmssd**2), 0)
        
        # Store metrics
        self.hrv_metrics = {
            'RMSSD': rmssd,
            'SDNN': sdnn,
            'Mean_RR': mean_rr,
            'pNN50': pnn50,
            'SD1': sd1,
            'SD2': sd2
        }
        
        # Update display
        hrv_text = "<br>".join([
            f"<span style='font-size:12px; font-weight:bold; color:#2E7D32;'>RMSSD:</span> "
            f"<span style='font-size:12px; color:black;'>{rmssd:.1f} ms</span>",

            f"<span style='font-size:12px; font-weight:bold; color:#2E7D32;'>SDNN:</span> "
            f"<span style='font-size:12px; color:black;'>{sdnn:.1f} ms</span>",

            f"<span style='font-size:12px; font-weight:bold; color:#2E7D32;'>pNN50:</span> "
            f"<span style='font-size:12px; color:black;'>{pnn50:.1f}%</span>",

            f"<span style='font-size:12px; font-weight:bold; color:#2E7D32;'>Mean RR:</span> "
            f"<span style='font-size:12px; color:black;'>{mean_rr:.1f} ms</span>",

            f"<span style='font-size:12px; font-weight:bold; color:#2E7D32;'>SD1:</span> "
            f"<span style='font-size:12px; color:black;'>{sd1:.1f} ms</span>",

            f"<span style='font-size:12px; font-weight:bold; color:#2E7D32;'>SD2:</span> "
            f"<span style='font-size:12px; color:black;'>{sd2:.1f} ms</span>"
        ])

        self.hrv_display.setText(hrv_text)




    def _update_peaks(self, peak_times, peak_amplitudes):
        """Update peak data with new peaks and visualize them."""
        for time, amp in zip(peak_times, peak_amplitudes):
            if time > self.last_peak_time:
                self.peak_times.append(time)
                self.peak_amplitudes.append(amp)

        if self.peak_times:
            self.last_peak_time = self.peak_times[-1]
            # Update scatter plot to show peaks on PPG signal
            self.peak_scatter.setData(list(self.peak_times), list(self.peak_amplitudes))

    def _update_ibis(self, peak_times):
        """Update IBI data from peak times."""
        if len(peak_times) < 2:
            return
            
        ibis = np.diff(peak_times) * 1000  # Convert to ms
        
        for i, ibi in enumerate(ibis):
            ibi_time = peak_times[i + 1]
            if ibi_time > self.last_ibi_time:
                # Update current IBI value for live monitoring
                self.current_ibi = ibi
                self.last_ibi_time = ibi_time

    def update_plots(self):
        """Update plot data and view window."""
        # Only update if we have data
        if self.bpm_plot.isVisible() and self.time_bpm_data and self.visual_bpm_data:
            self.bpm_curve.setData(self.time_bpm_data, self.visual_bpm_data)
        
        if self.raw_ppg_plot.isVisible() and self.time_ppg_data and self.visual_ppg_data:
            self.raw_ppg_curve.setData(self.time_ppg_data, self.visual_ppg_data)
        
        # Update IBI plot if visible
        if self.ibi_plot.isVisible() and self.ibi_data and self.ibi_times:
            self.ibi_curve.setData(list(self.ibi_times), list(self.ibi_data))
        
        # Update RR plot if visible
        if self.rr_plot.isVisible() and self.rr_data and self.rr_times:
            self.rr_curve.setData(list(self.rr_times), list(self.rr_data))

        # Update average BPM line and display
        self.update_average_bpm_line()
        
        self.update_plot_view()
        self.update_slider()

    def update_plot_view(self):
        """Sets the visible range of the plots based on slider position or auto-scroll."""
        max_time = self.time_ppg_data[-1] if self.time_ppg_data else 0
        
        if self.is_auto_scrolling:
            start_time = max(0, max_time - self.plot_window_seconds)
        else:
            start_time = self.plot_slider.value() / 100.0
            
        end_time = start_time + self.plot_window_seconds
        self.bpm_plot.setXRange(start_time, end_time, padding=0)
        self.raw_ppg_plot.setXRange(start_time, end_time, padding=0)
        
        if self.ibi_plot.isVisible():
            self.ibi_plot.setXRange(start_time, end_time, padding=0)
            
        if self.rr_plot.isVisible():
            self.rr_plot.setXRange(start_time, end_time, padding=0)

    def update_slider(self):
        """Updates the range and position of the time-scroll slider IF auto-scrolling."""
        if self.is_auto_scrolling:
            max_time = self.time_ppg_data[-1] if self.time_ppg_data else 0
            scrollable_duration = max_time - self.plot_window_seconds

            if scrollable_duration > 0:
                self.plot_slider.setMaximum(int(scrollable_duration * 100))
                self.plot_slider.blockSignals(True)
                self.plot_slider.setValue(self.plot_slider.maximum())
                self.plot_slider.blockSignals(False)
            else:
                self.plot_slider.setMaximum(0)

    def scroll_plots(self, value):
        """Update the plot view when the slider is moved manually."""
        if not self.is_auto_scrolling:
            self.update_plot_view()

    def disable_auto_scroll(self):
        """Disables auto-scrolling when the user interacts with the slider."""
        self.auto_scroll_checkbox.setChecked(False)

    def toggle_auto_scroll(self, state):
        """Enables or disables auto-scrolling based on the checkbox state."""
        self.is_auto_scrolling = (state == QtCore.Qt.Checked)
        if self.is_auto_scrolling:
            self.update_slider()
            self.update_plot_view()

    def start_session(self, username):
        """Start a new monitoring session for the specified user."""
        self.current_user = username
        self.session_start_time = datetime.now()
        self.update_session_info()

    def update_session_info(self):
        """Update the session information display."""
        if self.current_user and self.session_start_time:
            duration = datetime.now() - self.session_start_time
            minutes = duration.total_seconds() / 60
            self.session_info.setText(f"Recording: {minutes:.1f} min | Samples: {len(self.session_bpm)}")
            
            if self.session_bpm:
                current_bpm = self.session_bpm[-1] if self.session_bpm else 0
                avg_bpm = np.mean(self.session_bpm)
                stats_text = f"Current: {current_bpm:.1f} BPM\nAvg: {avg_bpm:.1f}"
                self.current_stats.setText(stats_text)
        else:
            self.session_info.setText("Not recording")
            self.current_stats.setText("Please log in to start recording session data")

    def update_thresholds(self):
        """Update BPM alarm thresholds."""
        self.bpm_low = self.low_slider.value()
        self.bpm_high = self.high_slider.value()
        self.low_label.setText(f"Low BPM Warning: {self.bpm_low}")
        self.high_label.setText(f"High BPM Warning: {self.bpm_high}")

    def blink_alarm(self):
        """Create blinking effect for alarm widget."""
        if self.alarm_active:
            self.alarm_visible = not self.alarm_visible
            self.alarm_widget.setVisible(self.alarm_visible)

    def check_bpm_alarm(self):
        """Check BPM against thresholds and trigger alarms if needed."""
        prev_state = self.alarm_active
        msg = None

        if self.current_bpm < self.bpm_low:
            self.alarm_active = True
            self.alarm_widget.setText(f"WARNING: PULSE LOW: {self.current_bpm:.1f} BPM")
            if not prev_state:
                self.alarm_timer.start(1000)
                msg = "Pulse Low"
                
        elif self.current_bpm > self.bpm_high:
            self.alarm_active = True
            self.alarm_widget.setText(f"WARNING: PULSE HIGH: {self.current_bpm:.1f} BPM")
            if not prev_state:
                self.alarm_timer.start(1000)
                msg = "Pulse High"
                
        else:
            if prev_state:
                self.alarm_active = False
                self.alarm_widget.setVisible(False)
                self.alarm_timer.stop()
                msg = "Pulse Normal"
                
        return msg
    
    def update_time_window(self, window_text):
        """Update the time window for plot display."""
        window_map = {"5s": 5, "10s": 10, "30s": 30, "60s": 60}
        self.plot_window_seconds = window_map.get(window_text, 10)
        self.update_plot_view()

    def update_average_bpm_line(self):
        """Update the average BPM reference line."""
        if len(self.visual_bpm_data) > 1:
            # Calculate average excluding zero values
            valid_bpm = [bpm for bpm in self.visual_bpm_data if bpm > 0]
            if valid_bpm:
                avg_bpm = np.mean(valid_bpm)
                self.avg_bpm_line.setValue(avg_bpm)
                self.avg_bpm_line.setVisible(True)
    
    def toggle_ibi_plot(self, state):
        """Toggle visibility of IBI plot."""
        show_ibi_plot = (state == QtCore.Qt.Checked)
        self.ibi_plot.setVisible(show_ibi_plot)

    def toggle_rr_plot(self, state):
        """Toggle visibility of Respiratory Rate plot."""
        show_rr_plot = (state == QtCore.Qt.Checked)
        self.rr_plot.setVisible(show_rr_plot)
    
    def toggle_legends(self, state):
        """Toggle visibility of plot legends."""
        show_legends = (state == QtCore.Qt.Checked)
        
        # Toggle BPM plot legend
        if hasattr(self, 'bpm_legend'):
            self.bpm_legend.setVisible(show_legends)
        
        # Toggle PPG plot legend
        if hasattr(self, 'ppg_legend'):
            self.ppg_legend.setVisible(show_legends)
        
        # Toggle IBI plot legend
        if hasattr(self, 'ibi_legend'):
            self.ibi_legend.setVisible(show_legends)
        
        # Toggle RR plot legend
        if hasattr(self, 'rr_legend'):
            self.rr_legend.setVisible(show_legends)