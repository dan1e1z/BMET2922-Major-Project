"""
Live monitor tab UI component.

Provides real-time PPG signal monitoring with live plotting and BPM calculation.

Author: Daniel Lindsay-Shad
Note: The Docstrings for methods were generated using Generative AI based on the method functionality.
"""

from PyQt5 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
import numpy as np
from datetime import datetime
from scipy import signal
from collections import deque

from gui.utils import (
    PlotNavigationMixin,
    PlotStyleHelper,
    SignalProcessingUtils,
    SessionInfoFormatter,
    HRVTooltipUtils
)


class LiveMonitorTab(QtWidgets.QWidget, PlotNavigationMixin):
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
        
        self.system_log = system_log
        
        # Session management
        self.current_user = None
        self.session_start_time = None
        self.session_raw_ppg = []
        self.session_bpm = []
        
        # Signal processing
        self.sampling_rate = 50
        self.buffer_duration = 60
        self.buffer_size = self.sampling_rate * self.buffer_duration
        
        self.ppg_buffer = deque(maxlen=self.buffer_size)
        self.ppg_times = deque(maxlen=self.buffer_size)
        
        # Visualization data
        self.visual_ppg_data = []
        self.visual_bpm_data = [0]
        self.time_ppg_data = []
        self.time_bpm_data = [0]
        
        # Physiological metrics
        self.ibi_data = deque([0], maxlen=1000)
        self.ibi_times = deque([0], maxlen=1000)
        self.rr_data = deque([0], maxlen=300)
        self.rr_times = deque([0], maxlen=300)
        self.peak_times = deque(maxlen=500)
        self.peak_amplitudes = deque(maxlen=500)
        self.hrv_metrics = {}
        
        self.current_ibi = 0
        self.current_rr = 0
        
        # Timing
        self.last_packet_time = 0
        self.last_hrv_update = 0
        self.last_peak_time = -1
        self.last_ibi_time = -1
        
        # UI state
        self.current_bpm = 0
        self.avg_bpm = 0
        self.bpm_low = 40
        self.bpm_high = 200
        self.alarm_active = False
        
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
        self.bpm_plot = pg.PlotWidget()
        PlotStyleHelper.configure_plot_widget(
            self.bpm_plot,
            title="Heart Rate (BPM)",
            y_label="BPM",
            grid=True,
            mouse_enabled=False,
            menu_enabled=False
        )

        self.bpm_legend = PlotStyleHelper.create_legend(self.bpm_plot)
        self.bpm_curve = self.bpm_plot.plot(pen=pg.mkPen('r', width=2), name='Heart Rate')

        # Average line
        self.avg_bpm_line = pg.InfiniteLine(
            angle=0, 
            pen=pg.mkPen(QtGui.QColor("#FFA726"), width=2, style=QtCore.Qt.DashLine)
        )
        self.bpm_plot.addItem(self.avg_bpm_line)

        # Add custom legend entry for the average line
        sample_item = pg.PlotDataItem(pen=pg.mkPen("#FFA726", width=2, style=QtCore.Qt.DashLine))
        self.bpm_legend.addItem(sample_item, "Average BPM")
        plots_layout.addWidget(self.bpm_plot, stretch=2)

        # --- Raw PPG Plot ---
        self.raw_ppg_plot = pg.PlotWidget()
        PlotStyleHelper.configure_plot_widget(
            self.raw_ppg_plot,
            title="Raw PPG Signal",
            y_label="PPG Amplitude",
            grid=True,
            mouse_enabled=False,
            menu_enabled=False
        )
        
        self.ppg_legend = PlotStyleHelper.create_legend(self.raw_ppg_plot)
        self.raw_ppg_curve = self.raw_ppg_plot.plot(pen=pg.mkPen('b', width=2), name='PPG Signal')
        
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
        PlotStyleHelper.configure_plot_widget(
            self.ibi_plot,
            title="Inter-Beat Intervals (IBI)",
            y_label="IBI",
            y_units="ms",
            grid=True,
            mouse_enabled=False,
            menu_enabled=False
        )
        
        self.ibi_legend = PlotStyleHelper.create_legend(self.ibi_plot)
        
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
        PlotStyleHelper.configure_plot_widget(
            self.rr_plot,
            title="Respiratory Rate",
            y_label="Breaths/min",
            grid=True,
            mouse_enabled=False,
            menu_enabled=False
        )
        
        self.rr_legend = PlotStyleHelper.create_legend(self.rr_plot)
        self.rr_curve = self.rr_plot.plot(
            pen=pg.mkPen(QtGui.QColor("#00695C"), width=2),
            name='Respiratory Rate'
        )
        self.rr_plot.setVisible(False)
        plots_layout.addWidget(self.rr_plot, stretch=2)

        # === PLOT NAVIGATION === 
        self.setup_plot_navigation(plots_layout, default_window_seconds=10)
        
        # === CONTROLS PANEL ===
        controls_widget = self._create_controls_panel()
        
        # Assemble layout
        content_layout = QtWidgets.QHBoxLayout()
        content_layout.addLayout(plots_layout, 3)
        content_layout.addWidget(controls_widget, 1)
        
        main_layout.addLayout(content_layout)
        main_layout.addWidget(self.system_log)
        self.setLayout(main_layout)
        
        # Timers
        self.alarm_timer = QtCore.QTimer()
        self.alarm_timer.timeout.connect(self.blink_alarm)
        self.alarm_visible = True
        
        # Initialize legend visibility
        self.toggle_legends(QtCore.Qt.Checked)

    def _create_controls_panel(self):
        """Create the right-side controls panel."""
        controls_widget = QtWidgets.QWidget()
        controls_layout = QtWidgets.QVBoxLayout()
        controls_layout.setSpacing(15)

        # --- Heart Rate Panel ---
        bpm_group = QtWidgets.QGroupBox("Heart Rate")
        bpm_layout = QtWidgets.QVBoxLayout(bpm_group)
        
        self.bpm_display = QtWidgets.QLabel("-- BPM")
        self.bpm_display.setAlignment(QtCore.Qt.AlignCenter)
        self.bpm_display.setStyleSheet("font-size: 28px; font-weight: bold; color: #2E7D32;")
        bpm_layout.addWidget(self.bpm_display)
        
        self.avg_bpm_display = QtWidgets.QLabel("Avg: -- BPM")
        self.avg_bpm_display.setAlignment(QtCore.Qt.AlignCenter)
        self.avg_bpm_display.setStyleSheet("font-size: 18px; color: #2E7D32;")
        bpm_layout.addWidget(self.avg_bpm_display)
        
        self.bpm_status = QtWidgets.QLabel("Monitoring...")
        self.bpm_status.setAlignment(QtCore.Qt.AlignCenter)
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
        self.legend_toggle.setChecked(True)
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
        self.high_slider.setRange(40, 250)
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
        self.alarm_widget.setStyleSheet(
            "QLabel { background-color: #ff0000; color: white; font-weight: bold; padding: 10px; }"
        )
        self.alarm_widget.setVisible(False)
        controls_layout.addWidget(self.alarm_widget)

        controls_layout.addStretch()
        controls_widget.setLayout(controls_layout)
        return controls_widget
    
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
        """Process PPG signal using SignalProcessingUtils for consistency."""
        ppg_signal = np.array(self.ppg_buffer)
        ppg_times_array = np.array(self.ppg_times)
        
        # signal cleaning
        ppg_cleaned = SignalProcessingUtils.clean_ppg_signal(
            ppg_signal,
            sampling_rate=self.sampling_rate,
            method="elgendi"
        )
        
        # peak detection
        peaks, info = SignalProcessingUtils.detect_ppg_peaks(
            ppg_cleaned,
            sampling_rate=self.sampling_rate,
            method="elgendi"
        )
        
        if len(peaks) == 0:
            return
        
        peak_times = ppg_times_array[peaks]
        peak_amplitudes = ppg_signal[peaks]
        
        self._update_peaks(peak_times, peak_amplitudes)
        self._update_ibis(peak_times)
        
        # Update HRV every 5 seconds
        if self.last_packet_time - self.last_hrv_update >= 5:
            self.calculate_hrv_metrics()
            self.last_hrv_update = self.last_packet_time
        
        self.estimate_respiratory_rate(ppg_cleaned, peaks)

    def estimate_respiratory_rate(self, ppg_signal, peaks):
        """
        Estimate respiratory rate using R-R interval variability analysis (Welch method on IBI signal).

        Implements the algorithm from: https://pmc.ncbi.nlm.nih.gov/articles/PMC9056464/#Sec2

        1. Detect PPG peaks → These represent heartbeats
        2. Calculate IBI → Time intervals between consecutive peaks
        3. Remove false peaks → Drop peaks where IBI < 30% of mean IBI
        4. Apply Welch's method to cleaned IBI signal → Find frequency components
        5. Find respiratory frequency → Maximum power in 0.1-0.5 Hz band
        6. Convert to breaths/min → Respiratory rate = frequency x 60
        """

        if len(peaks) < 3:
            return

        # Calculate R-R intervals (inter-beat intervals in seconds)
        rr_intervals = np.diff(peaks) / self.sampling_rate

        if len(rr_intervals) == 0:
            return

        # Remove false peaks: drop peaks where RR interval < 30% of mean
        threshold = 0.3 * np.mean(rr_intervals)
        valid_peak_mask = np.ones(len(peaks), dtype=bool)

        for i in range(len(rr_intervals)):
            if rr_intervals[i] < threshold:
                valid_peak_mask[i + 1] = False

        valid_peaks = peaks[valid_peak_mask]

        if len(valid_peaks) < 3:
            return

        # Recalculate RR intervals with valid peaks
        rr_intervals_clean = np.diff(valid_peaks) / self.sampling_rate

        if len(rr_intervals_clean) < 10:
            return

        # Apply Welch's method to RR intervals
        sampling_freq = 1.0 / np.mean(rr_intervals_clean)
        # sampling_freq = self.sampling_rate 
        nperseg = len(rr_intervals_clean)
        noverlap = int(nperseg * 0.5)

        f, Pxx = signal.welch(rr_intervals_clean,
                            fs=sampling_freq,
                            window='hann',
                            nperseg=nperseg,
                            noverlap=noverlap,
                            nfft=nperseg,
                            scaling='density',
                            average='mean')

        # Find peak in respiratory frequency band (0.1-0.5 Hz)
        # Lower limit 6 breaths/min ⇒ 6 ÷ 60 ≈ 0.10 Hz
        # Upper limit 30 breaths/min ⇒ 30 ÷ 60 = 0.50 Hz
        band_mask = (0.1 <= f) & (f <= 0.5)

        if not np.any(band_mask) or np.max(Pxx[band_mask]) == 0:
            return

        # Get frequency with maximum PSD and convert to breaths/min
        rr_estimate = f[band_mask][np.argmax(Pxx[band_mask])] * 60
        
        # Validate physiological range
        if not (6 <= rr_estimate <= 30):
            return

        # PRQ range based on: https://pmc.ncbi.nlm.nih.gov/articles/PMC6465339/
        hr_to_rr_ratio = self.current_bpm / rr_estimate if rr_estimate > 0 else 0
        if not (2.0 <= hr_to_rr_ratio <= 10.0):
            return
        
        # Adaptive smoothing
        delta = abs(rr_estimate - self.current_rr)
        alpha = 0.6 if delta > 5 else 0.4 if delta > 2 else 0.2
        self.current_rr = (1 - alpha) * self.current_rr + alpha * rr_estimate

        self.rr_display.setText(f"{self.current_rr:.1f} breaths/min")

    
    def update_physiological_metrics(self):
        """Update IBI and RR data points every second for live monitoring."""
        # Add current IBI value every second (even if no new calculation)
        self.ibi_data.append(self.current_ibi)
        self.ibi_times.append(self.last_packet_time)
        
        # Add current RR value every second (even if no new calculation)
        self.rr_data.append(self.current_rr)
        self.rr_times.append(self.last_packet_time)

    def calculate_hrv_metrics(self):
        """Calculate HRV metrics using SignalProcessingUtils for consistency."""
        if len(self.ibi_data) < 10:
            return

        rr_intervals = np.array(self.ibi_data)

        # HRV calculation
        self.hrv_metrics = SignalProcessingUtils.calculate_hrv_time_domain(rr_intervals)

        if not self.hrv_metrics:
            return

        # Get the parent layout that contains hrv_display
        parent_layout = self.hrv_display.parent().layout()
        if parent_layout:
            # Find and remove the old hrv_display
            for i in range(parent_layout.count()):
                if parent_layout.itemAt(i).widget() == self.hrv_display:
                    parent_layout.removeWidget(self.hrv_display)
                    self.hrv_display.setParent(None)
                    self.hrv_display.deleteLater()
                    break

        # Create a container widget to hold individual metric labels
        hrv_container = QtWidgets.QWidget()
        hrv_layout = QtWidgets.QVBoxLayout(hrv_container)
        hrv_layout.setContentsMargins(0, 0, 0, 0)
        hrv_layout.setSpacing(0)  # No spacing to mimic original compact look

        # Define metrics to display with individual tooltips
        metrics_to_display = [
            ("RMSSD", self.hrv_metrics.get('rmssd', 0), "ms"),
            ("SDNN", self.hrv_metrics.get('sdnn', 0), "ms"),
            ("pNN50", self.hrv_metrics.get('pnn50', 0), "%"),
            ("Mean IBI", self.hrv_metrics.get('mean_rr', 0), "ms"),
            ("SD1", self.hrv_metrics.get('sd1', 0), "ms"),
            ("SD2", self.hrv_metrics.get('sd2', 0), "ms"),
        ]

        for metric_name, value, unit in metrics_to_display:
            # Create label styled to match original appearance with individual tooltip
            display_text = f"<span style='font-size:12px; font-weight:bold; color:#2E7D32; font-family:monospace;'>{metric_name}:</span> <span style='font-size:12px; color:black; font-family:monospace;'>{value:.1f} {unit}</span>"
            label = QtWidgets.QLabel(display_text)
            label.setStyleSheet("background-color: transparent;")
            label.setAlignment(QtCore.Qt.AlignCenter)  # Match original center alignment

            # Add individual tooltip using HRVTooltipUtils
            tooltip = HRVTooltipUtils.get_hrv_metric_tooltips().get(metric_name, "")
            if tooltip:
                label.setToolTip(f"<b>{metric_name}:</b> {value:.1f} {unit}<br>{tooltip}")

            hrv_layout.addWidget(label)

        # Add the container to the parent layout
        parent_layout.addWidget(hrv_container)

        # Update the reference for future use
        self.hrv_display = hrv_container

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
        """Update plot data and view using PlotNavigationMixin methods."""
        # Update plot data
        if self.bpm_plot.isVisible() and self.time_bpm_data and self.visual_bpm_data:
            self.bpm_curve.setData(self.time_bpm_data, self.visual_bpm_data)
        
        if self.raw_ppg_plot.isVisible() and self.time_ppg_data and self.visual_ppg_data:
            self.raw_ppg_curve.setData(self.time_ppg_data, self.visual_ppg_data)
        
        if self.ibi_plot.isVisible() and self.ibi_data and self.ibi_times:
            self.ibi_curve.setData(list(self.ibi_times), list(self.ibi_data))
        
        if self.rr_plot.isVisible() and self.rr_data and self.rr_times:
            self.rr_curve.setData(list(self.rr_times), list(self.rr_data))
        
        self.update_average_bpm_line()
        self.update_plot_view()
        self.update_slider()

    def update_plot_view(self):
        """
        Update plot view:
        - Sync x-axis range across plots based on visible window.
        - Auto-scale y-axis using PlotStyleHelper with clinical ranges where applicable:
            - BPM: 30–220 bpm
            - IBI: 250–2000 ms
            - RR: 0–50 breaths/min
            - PPG: dynamic scaling (no limits)
        """
        if not self.time_ppg_data:
            return

        max_time = self.time_ppg_data[-1]
        start_time, end_time = self.get_plot_view_range(max_time)
        x_range = (start_time, end_time)

        # BPM plot
        self.bpm_plot.setXRange(start_time, end_time, padding=0)
        if self.bpm_plot.isVisible() and self.time_bpm_data and self.visual_bpm_data:
            PlotStyleHelper.auto_scale_y_axis(
                self.bpm_plot,
                self.time_bpm_data,
                self.visual_bpm_data,
                x_range,
                scale_mode="auto"
            )

        # Raw PPG plot
        self.raw_ppg_plot.setXRange(start_time, end_time, padding=0)
        if self.raw_ppg_plot.isVisible() and self.time_ppg_data and self.visual_ppg_data:
            PlotStyleHelper.auto_scale_y_axis(
                self.raw_ppg_plot,
                self.time_ppg_data,
                self.visual_ppg_data,
                x_range,
                # min_limit=0,
                # max_limit=4095,
                scale_mode="auto"
            )

        # IBI plot
        self.ibi_plot.setXRange(start_time, end_time, padding=0)
        if self.ibi_plot.isVisible() and self.ibi_times and self.ibi_data:
            PlotStyleHelper.auto_scale_y_axis(
                self.ibi_plot,
                list(self.ibi_times),
                list(self.ibi_data),
                x_range,
                scale_mode="auto"
            )

        # RR plot
        self.rr_plot.setXRange(start_time, end_time, padding=0)
        if self.rr_plot.isVisible() and self.rr_times and self.rr_data:
            PlotStyleHelper.auto_scale_y_axis(
                self.rr_plot,
                list(self.rr_times),
                list(self.rr_data),
                x_range,
                scale_mode="auto"
            )



    def update_slider(self):
        """Update slider using PlotNavigationMixin method."""
        if not self.time_ppg_data:
            return
        
        max_time = self.time_ppg_data[-1]
        self.update_plot_slider(max_time)

    def start_session(self, username):
        """Start a new monitoring session for the specified user."""
        self.current_user = username
        self.session_start_time = datetime.now()
        self.update_session_info()

    def update_session_info(self):
        """Update the session information display using SessionInfoFormatter."""
        if self.current_user and self.session_start_time:
            duration = datetime.now() - self.session_start_time
            minutes = duration.total_seconds() / 60
            
            if self.session_bpm:
                # session statistics
                stats = SessionInfoFormatter.calculate_session_stats(self.session_bpm)
                
                # Get health status
                health_status, status_color = SessionInfoFormatter.format_bpm_status(
                    stats['avg'],
                    low_threshold=self.bpm_low,
                    high_threshold=self.bpm_high
                )
                
                # Update BPM status with colored health indicator
                self.bpm_status.setText(
                    f"<span style='color: {status_color}; font-weight: bold;'>{health_status}</span>"
                )
        else:
            self.bpm_status.setText("Monitoring...")

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
        self.alarm_active = False
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

    def update_average_bpm_line(self):
        """Update the average BPM reference line using SessionInfoFormatter."""
        if len(self.visual_bpm_data) > 1:
            # Use SessionInfoFormatter to calculate statistics
            stats = SessionInfoFormatter.calculate_session_stats(self.visual_bpm_data)
            
            if stats['count'] > 0:
                avg_bpm = stats['avg']
                self.avg_bpm_display.setText(f"Avg: {avg_bpm:.1f} BPM")
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
        """Toggle legends using PlotStyleHelper for consistency."""
        show_legends = (state == QtCore.Qt.Checked)
        
        PlotStyleHelper.toggle_legend_visibility(self.bpm_legend, show_legends)
        PlotStyleHelper.toggle_legend_visibility(self.ppg_legend, show_legends)
        PlotStyleHelper.toggle_legend_visibility(self.ibi_legend, show_legends)
        PlotStyleHelper.toggle_legend_visibility(self.rr_legend, show_legends)