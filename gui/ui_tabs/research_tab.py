from PyQt5 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
import numpy as np
import neurokit2 as nk
from scipy.signal import butter, filtfilt, freqz, savgol_filter
import pandas as pd
import os
from datetime import datetime

from gui.utils import (
    PlotStyleHelper,
    PlotNavigationMixin,
    DataValidationUtils,
    SignalProcessingUtils,
    SessionInfoFormatter
)

class ResearchTab(QtWidgets.QWidget, PlotNavigationMixin):
    """Advanced research tab for PPG signal analysis with comprehensive filtering and HRV analysis."""
    
    def __init__(self):
        super().__init__()
        
        # Core data
        self.user_manager = None
        self.current_user = None
        self.raw_ppg_signal = np.array([])
        self.filtered_ppg_signal = np.array([])
        self.peaks = np.array([])
        self.time_axis = np.array([])
        self.session_metadata = {}
        
        # Analysis parameters
        self.sampling_rate = 50
        self.filter_applied = False
        
        # Results storage
        self.hrv_metrics = {}
        self.signal_quality_metrics = {}
        
        self.setup_ui()

    def setup_ui(self):
        """Create and configure the user interface layout."""
        layout = QtWidgets.QVBoxLayout()

        # Title and metadata
        title_layout = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("Advanced PPG Signal Analysis")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        
        self.metadata_label = QtWidgets.QLabel("")
        self.metadata_label.setStyleSheet("font-size: 10px; color: gray; margin: 5px;")
        self.metadata_label.setAlignment(QtCore.Qt.AlignRight)
        
        title_layout.addWidget(title)
        title_layout.addWidget(self.metadata_label)
        layout.addLayout(title_layout)

        # Main splitter
        main_splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        plots_widget = self.create_plots_widget()
        controls_widget = self.create_controls_widget()
        
        main_splitter.addWidget(plots_widget)
        main_splitter.addWidget(controls_widget)
        main_splitter.setStretchFactor(0, 7)
        main_splitter.setStretchFactor(1, 3)
        
        layout.addWidget(main_splitter)
        self.setLayout(layout)
        self.update_control_visibility()

    def create_plots_widget(self):
        """Create the plotting area with tabbed views."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        self.plot_tabs = QtWidgets.QTabWidget()
        
        # Time domain tab
        time_tab = self.create_time_domain_tab()
        self.plot_tabs.addTab(time_tab, "Time Domain")
        
        # HRV analysis tab
        hrv_tab = self.create_hrv_tab()
        self.plot_tabs.addTab(hrv_tab, "HRV Analysis")
        
        layout.addWidget(self.plot_tabs)
        
        # Plot controls using PlotNavigationMixin
        controls_layout = self.create_plot_controls()
        layout.addLayout(controls_layout)
        
        return widget

    def create_time_domain_tab(self):
        """Create time domain plotting tab."""
        time_tab = QtWidgets.QWidget()
        time_layout = QtWidgets.QVBoxLayout(time_tab)
        
        # Original signal plot
        self.original_plot = pg.PlotWidget()
        PlotStyleHelper.configure_plot_widget(
            self.original_plot, 
            title="Original Raw PPG Signal", 
            x_label="Time", 
            x_units="s", 
            y_label="Amplitude", 
            y_units="ADC units",
            grid=True,
            mouse_enabled=False,
            menu_enabled=False
        )
        self.original_curve = self.original_plot.plot(pen=pg.mkPen('b', width=1))
        time_layout.addWidget(self.original_plot)

        # Filtered signal with peaks
        self.filtered_plot = pg.PlotWidget()
        PlotStyleHelper.configure_plot_widget(
            self.filtered_plot, 
            title="Filtered PPG Signal & Peak Detection", 
            x_label="Time", 
            x_units="s", 
            y_label="Amplitude", 
            y_units="normalized",
            grid=True,
            mouse_enabled=False,
            menu_enabled=False
        )
        self.filtered_curve = self.filtered_plot.plot(pen=pg.mkPen('g', width=1.5))
        
        self.peak_scatter = pg.ScatterPlotItem(
            size=8, brush=pg.mkBrush(255, 0, 0, 200), 
            symbol='o', pen=pg.mkPen('r', width=2)
        )
        self.filtered_plot.addItem(self.peak_scatter)
        self.rr_lines = []
        time_layout.addWidget(self.filtered_plot)
        
        return time_tab

    def create_hrv_tab(self):
        """Create HRV analysis tab."""
        hrv_tab = QtWidgets.QWidget()
        hrv_layout = QtWidgets.QVBoxLayout(hrv_tab)
        
        self.hrv_plot = pg.PlotWidget()    
        PlotStyleHelper.configure_plot_widget(
            self.hrv_plot,
            title="R-R Interval Time Series (Tachogram)",
            x_label="Beat Number",
            x_units="",
            y_label="R-R Interval",
            y_units="ms",
            grid=True,
            mouse_enabled=False,
            menu_enabled=False
        )
        self.hrv_curve = self.hrv_plot.plot(pen=pg.mkPen('c', width=2), symbol='o', symbolSize=4)
        hrv_layout.addWidget(self.hrv_plot)
        
        return hrv_tab

    def create_plot_controls(self):
        """Create plot navigation controls using PlotNavigationMixin."""
        controls_layout = QtWidgets.QHBoxLayout()
        widget_refs = self.setup_plot_navigation(
            parent_layout=controls_layout,
            default_window_seconds=10
        )
        
        self.jump_to_end_checkbox = widget_refs['checkbox']
        self.plot_slider = widget_refs['slider']
        self.window_selector = widget_refs['selector']
        
        return controls_layout

    def create_controls_widget(self):
        """Create the control panel with tabs."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        
        self.control_tabs = QtWidgets.QTabWidget()
        
        # Control tabs
        self.control_tabs.addTab(self.create_data_tab(), "Data")
        self.control_tabs.addTab(self.create_filter_tab(), "Filtering")
        self.analysis_tab = self.create_analysis_tab()
        self.control_tabs.addTab(self.analysis_tab, "Analysis")
        self.control_tabs.addTab(self.create_export_tab(), "Export")
        
        # Initially disable analysis tab
        self.control_tabs.setTabEnabled(2, False)
        
        layout.addWidget(self.control_tabs)
        
        # Status log
        self.status_text = QtWidgets.QTextEdit()
        self.status_text.setMaximumHeight(100)
        self.status_text.setReadOnly(True)
        self.status_text.setStyleSheet("background-color: #f0f0f0; font-family: Courier; font-size: 10px;")
        layout.addWidget(QtWidgets.QLabel("Analysis Log:"))
        layout.addWidget(self.status_text)
        
        return widget

    def create_data_tab(self):
        """Create data loading tab."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(widget)
        
        # Session selector
        self.session_selector = QtWidgets.QComboBox()
        self.session_selector.addItem("Select a session to load...")
        self.session_selector.currentIndexChanged.connect(self.load_selected_session)
        layout.addRow("Load Session:", self.session_selector)
        
        # Quality metrics
        quality_group = QtWidgets.QGroupBox("Data Quality Metrics")
        quality_layout = QtWidgets.QFormLayout(quality_group)
        
        self.samples_label = QtWidgets.QLabel("-")
        self.duration_label = QtWidgets.QLabel("-")
        self.missing_label = QtWidgets.QLabel("-")
        self.snr_label = QtWidgets.QLabel("-")
        
        quality_layout.addRow("Total Samples:", self.samples_label)
        quality_layout.addRow("Duration:", self.duration_label)
        quality_layout.addRow("Missing/Invalid:", self.missing_label)
        quality_layout.addRow("Estimated SNR:", self.snr_label)
        
        layout.addRow(quality_group)
        return widget

    def create_filter_tab(self):
        """Create signal filtering controls tab."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        
        # Filter method selection
        method_layout = QtWidgets.QFormLayout()
        self.filter_method_combo = QtWidgets.QComboBox()
        self.filter_method_combo.addItems([
            "NeuroKit Elgendi", 
            "Custom Butterworth", 
            "Savitzky-Golay",
            "No Filter"
        ])
        self.filter_method_combo.currentIndexChanged.connect(self.update_control_visibility)
        method_layout.addRow("Filter Method:", self.filter_method_combo)
        layout.addLayout(method_layout)
        
        # Filter parameters
        filter_group = QtWidgets.QGroupBox("Filter Parameters & Application")
        filter_group_layout = QtWidgets.QVBoxLayout(filter_group)
        
        self.butterworth_controls = self.create_butterworth_controls()
        self.savgol_controls = self.create_savgol_controls()
        filter_group_layout.addWidget(self.butterworth_controls)
        filter_group_layout.addWidget(self.savgol_controls)
        
        # Apply button
        apply_btn = QtWidgets.QPushButton("Apply Filter")
        apply_btn.clicked.connect(self.apply_filter)
        apply_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 8px; }")
        filter_group_layout.addWidget(apply_btn)
        
        layout.addWidget(filter_group)
        layout.addStretch()
        
        # Filter response
        response_label = QtWidgets.QLabel("Filter Frequency Response:")
        response_label.setStyleSheet("font-weight: bold; margin-top: 15px; margin-bottom: 5px;")
        layout.addWidget(response_label)
        
        self.filter_response_plot = pg.PlotWidget()
        self.filter_response_plot.setLabel('left', 'Magnitude (dB)')
        self.filter_response_plot.setLabel('bottom', 'Frequency (Hz)')
        self.filter_response_plot.setMaximumHeight(150)
        self.filter_response_curve = self.filter_response_plot.plot(pen='r')
        layout.addWidget(self.filter_response_plot)
        
        return widget

    def create_butterworth_controls(self):
        """Create Butterworth filter controls."""
        controls = QtWidgets.QGroupBox("Butterworth Parameters")
        layout = QtWidgets.QFormLayout(controls)
        
        # Filter type
        self.filter_type_combo = QtWidgets.QComboBox()
        self.filter_type_combo.addItems(["Bandpass", "Low-pass", "High-pass"])
        self.filter_type_combo.currentIndexChanged.connect(self.update_control_visibility)
        layout.addRow("Filter Type:", self.filter_type_combo)
        
        # Cutoff controls
        self.low_cutoff_slider = self.create_slider(1, 200, 50, lambda v: f"{v/100:.2f} Hz")
        self.high_cutoff_slider = self.create_slider(100, 1500, 400, lambda v: f"{v/100:.2f} Hz")
        self.order_slider = self.create_slider(1, 10, 4, str)
        
        self.low_cutoff_widget = self.create_slider_widget("Low Cutoff:", self.low_cutoff_slider)
        self.high_cutoff_widget = self.create_slider_widget("High Cutoff:", self.high_cutoff_slider)
        
        layout.addRow(self.low_cutoff_widget)
        layout.addRow(self.high_cutoff_widget)
        layout.addRow(self.create_slider_widget("Filter Order:", self.order_slider))
        
        return controls

    def create_savgol_controls(self):
        """Create Savitzky-Golay controls."""
        controls = QtWidgets.QGroupBox("Savitzky-Golay Parameters")
        layout = QtWidgets.QFormLayout(controls)
        
        self.window_length_spin = QtWidgets.QSpinBox()
        self.window_length_spin.setRange(3, 101)
        self.window_length_spin.setSingleStep(2)
        self.window_length_spin.setValue(11)
        layout.addRow("Window Length:", self.window_length_spin)
        
        self.poly_order_spin = QtWidgets.QSpinBox()
        self.poly_order_spin.setRange(1, 10)
        self.poly_order_spin.setValue(3)
        layout.addRow("Polynomial Order:", self.poly_order_spin)
        
        return controls

    def create_slider(self, min_val, max_val, default, formatter):
        """Helper to create slider with label."""
        slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(default)
        
        label = QtWidgets.QLabel(formatter(default))
        slider.valueChanged.connect(lambda v: label.setText(formatter(v)))
        slider.label = label
        
        return slider

    def create_slider_widget(self, label_text, slider):
        """Create labeled slider widget."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QtWidgets.QLabel(label_text))
        layout.addWidget(slider, 1)
        layout.addWidget(slider.label)
        widget.setLayout(layout)
        return widget

    def create_analysis_tab(self):
        """Create analysis tools tab."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        
        # Peak detection
        peak_group = QtWidgets.QGroupBox("Peak Detection")
        peak_layout = QtWidgets.QVBoxLayout(peak_group)
        
        info_label = QtWidgets.QLabel("Note: Apply filtering first before peak detection")
        info_label.setStyleSheet("color: #666; font-style: italic; margin-bottom: 10px;")
        peak_layout.addWidget(info_label)
        
        method_layout = QtWidgets.QFormLayout()
        self.peak_method_combo = QtWidgets.QComboBox()
        self.peak_method_combo.addItems(["NeuroKit Elgendi", "NeuroKit Bishop", "NeuroKit Charlton"])
        method_layout.addRow("Detection Method:", self.peak_method_combo)
        peak_layout.addLayout(method_layout)
        
        detect_peaks_btn = QtWidgets.QPushButton("Detect Peaks")
        detect_peaks_btn.clicked.connect(self.detect_peaks)
        peak_layout.addWidget(detect_peaks_btn)
        layout.addWidget(peak_group)
        
        # HRV analysis
        hrv_group = QtWidgets.QGroupBox("Heart Rate Variability Analysis")
        hrv_layout = QtWidgets.QVBoxLayout(hrv_group)
        
        analyze_hrv_btn = QtWidgets.QPushButton("Compute HRV Metrics")
        analyze_hrv_btn.clicked.connect(self.analyze_hrv)
        hrv_layout.addWidget(analyze_hrv_btn)
        
        self.hrv_results = QtWidgets.QTextEdit()
        self.hrv_results.setMaximumHeight(150)
        self.hrv_results.setReadOnly(True)
        self.hrv_results.setStyleSheet("font-family: monospace; font-size: 10px;")
        hrv_layout.addWidget(self.hrv_results)
        layout.addWidget(hrv_group)
        
        # Signal quality
        quality_group = QtWidgets.QGroupBox("Signal Quality Assessment")
        quality_layout = QtWidgets.QVBoxLayout(quality_group)
        
        assess_quality_btn = QtWidgets.QPushButton("Assess Signal Quality")
        assess_quality_btn.clicked.connect(self.assess_signal_quality)
        quality_layout.addWidget(assess_quality_btn)
        
        self.quality_results = QtWidgets.QTextEdit()
        self.quality_results.setMaximumHeight(100)
        self.quality_results.setReadOnly(True)
        self.quality_results.setStyleSheet("font-family: monospace; font-size: 10px;")
        quality_layout.addWidget(self.quality_results)
        layout.addWidget(quality_group)
        
        layout.addStretch()
        return widget

    def create_export_tab(self):
        """Create data export tab."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(widget)
        
        # Export options
        export_group = QtWidgets.QGroupBox("Export Content Selection")
        export_layout = QtWidgets.QVBoxLayout(export_group)
        
        self.export_raw_check = QtWidgets.QCheckBox("Raw PPG signal")
        self.export_filtered_check = QtWidgets.QCheckBox("Filtered PPG signal")
        self.export_peaks_check = QtWidgets.QCheckBox("Peak locations and times")
        self.export_hrv_check = QtWidgets.QCheckBox("HRV metrics and analysis")
        self.export_metadata_check = QtWidgets.QCheckBox("Session metadata")
        
        # Default selections
        for checkbox in [self.export_raw_check, self.export_filtered_check, 
                        self.export_peaks_check, self.export_hrv_check]:
            checkbox.setChecked(True)
            export_layout.addWidget(checkbox)
        export_layout.addWidget(self.export_metadata_check)
            
        layout.addRow(export_group)
        
        # Format selection
        self.export_format_combo = QtWidgets.QComboBox()
        self.export_format_combo.addItems(["CSV", "TXT (Tab-separated)"])
        layout.addRow("Export Format:", self.export_format_combo)
        
        # Export button
        export_btn = QtWidgets.QPushButton("Export Selected Data")
        export_btn.clicked.connect(self.export_data)
        export_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 8px; }")
        layout.addRow(export_btn)
        
        return widget

    def log_status(self, message):
        """Add timestamped message to status log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.append(f"[{timestamp}] {message}")
        scrollbar = self.status_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def start_session(self, username, user_manager):
        """Initialize research tab for user session."""
        self.current_user = username
        self.user_manager = user_manager
        self.populate_session_selector()
        self.log_status(f"Research session started for user: {username}")

    def populate_session_selector(self):
        """Populate session selector with available sessions."""
        self.session_selector.clear()
        self.session_selector.addItem("Select a session to load...")
        
        if not self.user_manager or not self.current_user:
            return

        user_data = self.user_manager.users.get(self.current_user, {})
        history = user_data.get("history", [])

        for i, session in enumerate(reversed(history)):
            if "raw_ppg" in session and session["raw_ppg"]:
                start_time = session.get("start", f"Session {len(history)-i}")
                duration = session.get("duration", "Unknown")
                sample_count = len(session["raw_ppg"])
                
                display_text = f"{start_time} | {duration}s | {sample_count} samples"
                self.session_selector.addItem(display_text, userData=session)

    def load_selected_session(self, index):
        """Load and initialize analysis for selected session."""
        if index <= 0:
            self.clear_all_data()
            return

        session_data = self.session_selector.itemData(index)
        self.raw_ppg_signal = np.array(session_data.get("raw_ppg", []))
        self.session_metadata = session_data
        
        if self.raw_ppg_signal.size == 0:
            self.log_status("Warning: No PPG data found in selected session")
            return
            
        # Update displays
        self.update_metadata_display()
        self.calculate_data_quality()
        
        # Initialize time axis
        self.time_axis = np.arange(len(self.raw_ppg_signal)) / self.sampling_rate
        
        # Display raw signal
        self.original_curve.setData(self.time_axis, self.raw_ppg_signal)
        
        # Reset analysis results
        self.filtered_curve.clear()
        self.peak_scatter.clear()
        self.clear_rr_lines()
        
        # Update navigation
        self.update_slider()
        self.update_plot_view()
        
        self.log_status(f"Loaded session: {len(self.raw_ppg_signal)} samples, {self.time_axis[-1]:.1f}s duration")

    def update_metadata_display(self):
        """Update session metadata display using SessionInfoFormatter."""
        if self.session_metadata:
            start_time = self.session_metadata.get("start", "Unknown")
            duration_minutes = self.session_metadata.get("duration_minutes", 0)
            duration = SessionInfoFormatter.format_duration(duration_minutes)
            samples = len(self.raw_ppg_signal)
            
            # Format the datetime 
            if isinstance(start_time, str) and start_time != "Unknown":
                start_time = SessionInfoFormatter.format_datetime(start_time)
            
            metadata_text = (f"Session: {start_time} | Duration: {duration} | "
                           f"Samples: {samples} | Sampling Rate: {self.sampling_rate}Hz")
            self.metadata_label.setText(metadata_text)

    def calculate_data_quality(self):
        """Calculate and display basic data quality metrics using DataValidationUtils."""
        if self.raw_ppg_signal.size == 0:
            return
            
        metrics = DataValidationUtils.calculate_signal_quality_metrics(self.raw_ppg_signal)
        
        # Extract calculated values
        samples = metrics.get('samples', 0)
        invalid_count = metrics.get('invalid_count', 0)
        invalid_percent = metrics.get('invalid_percent', 0)
        snr_db = metrics.get('snr_db', 0)

        duration_minutes = self.session_metadata.get("duration_minutes", 0)
        duration = SessionInfoFormatter.format_duration(duration_minutes)
        
        # Update displays
        self.samples_label.setText(f"{samples:,}")
        self.duration_label.setText(duration)
        self.missing_label.setText(f"{invalid_count} ({invalid_percent:.1f}%)")
        self.snr_label.setText(f"{snr_db:.1f} dB")

    def update_control_visibility(self):
        """Update visibility of filter controls."""
        method = self.filter_method_combo.currentText()
        
        self.butterworth_controls.setVisible("Butterworth" in method)
        self.savgol_controls.setVisible("Savitzky-Golay" in method)
        
        if "Butterworth" in method:
            filter_type = self.filter_type_combo.currentText()
            self.low_cutoff_widget.setVisible(filter_type in ["Bandpass", "High-pass"])
            self.high_cutoff_widget.setVisible(filter_type in ["Bandpass", "Low-pass"])

    def apply_filter(self):
        """Apply selected filtering method using SignalProcessingUtils where appropriate."""
        if self.raw_ppg_signal.size == 0:
            self.log_status("Error: No signal loaded to filter")
            return

        method = self.filter_method_combo.currentText()
        signal = self.raw_ppg_signal.copy()
        
        if method == "Custom Butterworth":
            self.filtered_ppg_signal = self.apply_butterworth_filter(signal)
        elif method == "Savitzky-Golay":
            window_length = self.window_length_spin.value()
            poly_order = self.poly_order_spin.value()
            if window_length <= poly_order:
                window_length = poly_order + 1
                self.window_length_spin.setValue(window_length)
                self.log_status(f"Adjusted window length to {window_length}")
            self.filtered_ppg_signal = savgol_filter(signal, window_length, poly_order)
        elif "NeuroKit" in method:
            self.filtered_ppg_signal = SignalProcessingUtils.clean_ppg_signal(
                signal, 
                sampling_rate=self.sampling_rate, 
                method="elgendi"
            )
        else:  # No filter
            self.filtered_ppg_signal = signal.copy()
        
        # Normalize for display
        if self.filtered_ppg_signal.size > 0:
            signal_min = np.min(self.filtered_ppg_signal)
            signal_max = np.max(self.filtered_ppg_signal)
            if signal_max > signal_min:
                self.filtered_ppg_signal = ((self.filtered_ppg_signal - signal_min) / (signal_max - signal_min))
        
        self.update_filtered_plot()
        
        # Enable analysis tab
        self.filter_applied = True
        self.control_tabs.setTabEnabled(2, True)
        
        self.log_status(f"Applied {method} filter successfully - Analysis tab now enabled")

    def apply_butterworth_filter(self, signal):
        """Apply Butterworth filter with current settings."""
        filter_type = self.filter_type_combo.currentText().lower()
        order = self.order_slider.value()
        
        # Get frequencies in Hz
        lowcut_hz = self.low_cutoff_slider.value() / 100.0
        highcut_hz = self.high_cutoff_slider.value() / 100.0
        
        # Validate against Nyquist
        nyquist = self.sampling_rate / 2
        if highcut_hz >= nyquist:
            highcut_hz = nyquist * 0.95
            self.log_status(f"Warning: High cutoff reduced to {highcut_hz:.2f}Hz")
        
        # Design filter (pass Hz values, normalization happens inside)
        b, a = self.design_butter_filter(lowcut_hz, highcut_hz, order, filter_type)
        self.update_filter_response(b, a)
        
        return filtfilt(b, a, signal)

    def design_butter_filter(self, lowcut_hz, highcut_hz, order, btype):
        """
        Design Butterworth filter.
        
        Args:
            lowcut_hz: Low cutoff frequency in Hz
            highcut_hz: High cutoff frequency in Hz
            order: Filter order
            btype: Filter type ('low-pass', 'high-pass', 'bandpass')
        
        Returns:
            tuple: (b, a) filter coefficients
        """
        nyquist = self.sampling_rate / 2
        
        # Normalize frequencies by Nyquist (butter expects 0-1 range)
        if btype in ['low-pass', 'lowpass', 'low']:
            return butter(order, highcut_hz / nyquist, btype='low')
        elif btype in ['high-pass', 'highpass', 'high']:
            return butter(order, lowcut_hz / nyquist, btype='high')
        else:  # bandpass
            return butter(order, [lowcut_hz / nyquist, highcut_hz / nyquist], btype='band')

    def update_filter_response(self, b, a):
        """Update filter frequency response plot."""
        w, h = freqz(b, a, worN=2048, fs=self.sampling_rate)
        magnitude_db = 20 * np.log10(np.abs(h) + 1e-10)
        self.filter_response_curve.setData(w, magnitude_db)
        self.filter_response_plot.setXRange(0, min(10, self.sampling_rate/2))
        self.filter_response_plot.setYRange(-60, 5)

    def detect_peaks(self):
        """Detect cardiac peaks in filtered signal using SignalProcessingUtils."""
        if self.filtered_ppg_signal.size == 0:
            QtWidgets.QMessageBox.warning(
                self, "No Filtered Signal", 
                "No filtered signal available. Please apply filtering first."
            )
            return
            
        method = self.peak_method_combo.currentText()
        
        # Map method names
        method_map = {
            "NeuroKit Elgendi": "elgendi",
            "NeuroKit Bishop": "bishop", 
            "NeuroKit Charlton": "charlton"
        }
        
        nk_method = method_map.get(method, "elgendi")
        
        self.peaks, _ = SignalProcessingUtils.detect_ppg_peaks(
            self.filtered_ppg_signal,
            sampling_rate=self.sampling_rate,
            method=nk_method
        )
        
        self.log_status(f"Detected {len(self.peaks)} peaks using {method}")
        self.update_filtered_plot()

    def update_filtered_plot(self):
        """Update filtered signal plot with peak markers."""
        if self.filtered_ppg_signal.size == 0:
            return
            
        time_axis = np.arange(len(self.filtered_ppg_signal)) / self.sampling_rate
        self.filtered_curve.setData(time_axis, self.filtered_ppg_signal)
        
        # Update peak markers
        if self.peaks.size > 0:
            peak_times = time_axis[self.peaks]
            peak_amplitudes = self.filtered_ppg_signal[self.peaks]
            self.peak_scatter.setData(peak_times, peak_amplitudes)
            self.update_rr_interval_display(peak_times)
        else:
            self.peak_scatter.clear()
            self.clear_rr_lines()

    def update_rr_interval_display(self, peak_times):
        """Add visual indicators for R-R intervals."""
        self.clear_rr_lines()
        
        if len(peak_times) < 2:
            return
            
        # Draw lines between consecutive peaks
        for i in range(len(peak_times) - 1):
            line = pg.PlotDataItem([peak_times[i], peak_times[i+1]], 
                                 [0, 0], pen=pg.mkPen('orange', width=3))
            self.filtered_plot.addItem(line)
            self.rr_lines.append(line)

    def clear_rr_lines(self):
        """Remove all R-R interval visual indicators."""
        for line in self.rr_lines:
            self.filtered_plot.removeItem(line)
        self.rr_lines.clear()

    def analyze_hrv(self):
        """Perform comprehensive heart rate variability analysis using SignalProcessingUtils."""
        if self.peaks.size < 10:
            msg = "No peaks detected" if self.peaks.size == 0 else f"Only {len(self.peaks)} peaks detected"
            QtWidgets.QMessageBox.warning(self, "Insufficient Peaks", 
                f"{msg}. HRV analysis requires at least 10 peaks.")
            return
            
        # Calculate R-R intervals
        rr_intervals = SignalProcessingUtils.calculate_rr_intervals(
            self.peaks, 
            self.sampling_rate
        )
        
        if len(rr_intervals) < 5:
            self.hrv_results.setText("Error: Insufficient R-R intervals for analysis")
            return
        
        # Calculate time domain and nonlinear HRV metrics
        # handles filtering (300-2000ms) internally
        time_nonlinear_metrics = SignalProcessingUtils.calculate_hrv_time_domain(rr_intervals)
        
        if not time_nonlinear_metrics:
            self.hrv_results.setText("Error: Insufficient valid R-R intervals for analysis")
            return
        
        # Extract metrics from utility results
        rr_mean = time_nonlinear_metrics.get('mean_rr', 0)
        rr_std = time_nonlinear_metrics.get('sdnn', 0)
        rmssd = time_nonlinear_metrics.get('rmssd', 0)
        pnn50 = time_nonlinear_metrics.get('pnn50', 0)
        sd1 = time_nonlinear_metrics.get('sd1', 0)
        sd2 = time_nonlinear_metrics.get('sd2', 0)
        sd_ratio = time_nonlinear_metrics.get('sd_ratio', 0)

        # Frequency domain analysis using NeuroKit
        # We need to filter RR intervals again for NeuroKit's frequency analysis
        valid_mask = (rr_intervals > 300) & (rr_intervals < 2000)
        valid_rr = rr_intervals[valid_mask]
        
        vlf_power = lf_power = hf_power = lf_hf_ratio = 0
        
        try:
            # Filter the original peaks to match valid RR intervals
            valid_peaks = self.peaks[:-1][valid_mask]
            
            # Append the corresponding last peak for the last valid interval
            if len(valid_peaks) > 0 and len(valid_peaks) < len(self.peaks):
                # Find the index of the last valid peak in the original array
                last_valid_idx = np.where(valid_mask)[0][-1] + 1
                if last_valid_idx < len(self.peaks):
                    valid_peaks = np.append(valid_peaks, self.peaks[last_valid_idx])

            valid_peaks = SignalProcessingUtils.remove_duplicate_peaks(valid_peaks)
            
            if len(valid_peaks) > 20:  # Minimum for frequency analysis
                hrv_freq = nk.hrv_frequency(valid_peaks, sampling_rate=self.sampling_rate, show=False)
                
                # Extract frequency domain metrics
                vlf_power = hrv_freq.get('HRV_VLF', [0]).iloc[0] if 'HRV_VLF' in hrv_freq.columns else 0
                lf_power = hrv_freq.get('HRV_LF', [0]).iloc[0] if 'HRV_LF' in hrv_freq.columns else 0
                hf_power = hrv_freq.get('HRV_HF', [0]).iloc[0] if 'HRV_HF' in hrv_freq.columns else 0
                lf_hf_ratio = lf_power / hf_power if hf_power > 0 else 0
                
        except Exception as e:
            self.log_status(f"Frequency domain analysis failed: {str(e)}")

        # Store results
        self.hrv_metrics = {
            'time_domain': {
                'mean_rr': rr_mean, 'sdnn': rr_std, 'rmssd': rmssd,
                'pnn50': pnn50, 'heart_rate': 60000 / rr_mean if rr_mean > 0 else 0
            },
            'frequency_domain': {
                'vlf_power': vlf_power, 'lf_power': lf_power,
                'hf_power': hf_power, 'lf_hf_ratio': lf_hf_ratio
            },
            'nonlinear': {'sd1': sd1, 'sd2': sd2, 'sd_ratio': sd_ratio}
        }
        
        # Display results
        results_text = "<br>".join([
            f"<span style='font-size:14px; color:#37474F; font-weight:bold;'>TIME DOMAIN METRICS</span>",
            (f"<span style='font-size:12px; color:#2E7D32;'>Mean R-R: </span>"
            f"<span style='font-size:12px; color:#263238;'>{rr_mean:.1f} ms</span>"),
            (f"<span style='font-size:12px; color:#2E7D32;'>SDNN: </span>"
            f"<span style='font-size:12px; color:#263238;'>{rr_std:.1f} ms</span>"),
            (f"<span style='font-size:12px; color:#2E7D32;'>RMSSD: </span>"
            f"<span style='font-size:12px; color:#263238;'>{rmssd:.1f} ms</span>"),
            (f"<span style='font-size:12px; color:#2E7D32;'>pNN50: </span>"
            f"<span style='font-size:12px; color:#263238;'>{pnn50:.1f}%</span>"),
            (f"<span style='font-size:12px; color:#2E7D32;'>Heart Rate: </span>"
            f"<span style='font-size:12px; color:#263238;'>{60000/rr_mean if rr_mean > 0 else 0:.1f} bpm</span>"),
            "", 

            f"<span style='font-size:14px; color:#37474F; font-weight:bold;'>FREQUENCY DOMAIN</span>",
            (f"<span style='font-size:12px; color:#2E7D32;'>VLF Power: </span>"
            f"<span style='font-size:12px; color:#263238;'>{vlf_power:.3f} ms²</span>"),
            (f"<span style='font-size:12px; color:#2E7D32;'>LF Power: </span>"
            f"<span style='font-size:12px; color:#263238;'>{lf_power:.3f} ms²</span>"),
            (f"<span style='font-size:12px; color:#2E7D32;'>HF Power: </span>"
            f"<span style='font-size:12px; color:#263238;'>{hf_power:.3f} ms²</span>"),
            (f"<span style='font-size:12px; color:#2E7D32;'>LF/HF Ratio: </span>"
            f"<span style='font-size:12px; color:#263238;'>{lf_hf_ratio:.2f}</span>"),
            "", 

            f"<span style='font-size:14px; color:#37474F; font-weight:bold;'>NONLINEAR METRICS</span>",
            (f"<span style='font-size:12px; color:#2E7D32;'>SD1: </span>"
            f"<span style='font-size:12px; color:#263238;'>{sd1:.2f} ms</span>"),
            (f"<span style='font-size:12px; color:#2E7D32;'>SD2: </span>"
            f"<span style='font-size:12px; color:#263238;'>{sd2:.2f} ms</span>"),
            (f"<span style='font-size:12px; color:#2E7D32;'>SD1/SD2 Ratio: </span>"
            f"<span style='font-size:12px; color:#263238;'>{sd_ratio:.3f}</span>")
        ])
        
        self.hrv_results.setText(results_text)
        
        # Update tachogram
        beat_numbers = np.arange(len(valid_rr))
        self.hrv_curve.setData(beat_numbers, valid_rr)
        
        self.log_status(f"HRV analysis completed: {len(valid_rr)} intervals analyzed")

    def assess_signal_quality(self):
        """Perform signal quality assessment using NeuroKit and DataValidationUtils."""
        if self.raw_ppg_signal.size == 0:
            self.quality_results.setText("No signal loaded for quality assessment")
            return
            
        if self.filtered_ppg_signal.size == 0:
            self.quality_results.setText("No filtered signal available. Please apply filtering first.")
            return
        
        # NeuroKit quality assessment
        if self.peaks.size > 0:
            quality_scores = nk.ppg_quality(
                self.filtered_ppg_signal, 
                peaks=self.peaks,
                sampling_rate=self.sampling_rate, 
                method='templatematch'
            )
        else:
            quality_scores = nk.ppg_quality(
                self.filtered_ppg_signal, 
                sampling_rate=self.sampling_rate, 
                method='templatematch'
            )
        
        # Calculate statistics
        mean_quality = np.mean(quality_scores)
        std_quality = np.std(quality_scores)
        min_quality = np.min(quality_scores)
        max_quality = np.max(quality_scores)
        
        high_quality_pct = np.sum(quality_scores > 0.7) / len(quality_scores) * 100
        poor_quality_pct = np.sum(quality_scores < 0.3) / len(quality_scores) * 100
        
        # additional metrics
        raw_signal_metrics = DataValidationUtils.calculate_signal_quality_metrics(self.raw_ppg_signal)
        filtered_signal_metrics = DataValidationUtils.calculate_signal_quality_metrics(self.filtered_ppg_signal)
        
        samples = raw_signal_metrics.get('samples', 0)
        invalid_count = raw_signal_metrics.get('invalid_count', 0)
        snr_db = filtered_signal_metrics.get('snr_db', 0)
        duration = samples / self.sampling_rate if self.sampling_rate > 0 else 0
        
        # Quality rating
        if mean_quality >= 0.8:
            quality_rating = "Excellent"
        elif mean_quality >= 0.6:
            quality_rating = "Good"
        elif mean_quality >= 0.4:
            quality_rating = "Fair"
        else:
            quality_rating = "Poor"
        
        # Store metrics
        self.signal_quality_metrics = {
            'nk_mean_quality': mean_quality,
            'overall_rating': quality_rating,
            'high_quality_pct': high_quality_pct,
            'poor_quality_pct': poor_quality_pct,
            'snr_db': snr_db,
            'invalid_data_pct': invalid_count/samples*100 if samples > 0 else 0,
        }
        
        # Display results
        results_text = "<br>".join([
            f"<span style='font-size:14px; color:#37474F; font-weight:bold;'>PPG SIGNAL QUALITY ASSESSMENT</span>",
            f"<span style='font-size:12px; color:#2E7D32;'>Overall Quality:</span> "
            f"<span style='font-size:12px; color:#263238;'>{mean_quality:.3f} ({quality_rating})</span>",
            "",
            f"<span style='font-size:12px; color:#455A64; font-weight:bold;'>NEUROKIT TEMPLATE MATCHING:</span>",
            f"<span style='font-size:12px; color:#2E7D32;'>Mean Quality Score:</span> "
            f"<span style='font-size:12px; color:#263238;'>{mean_quality:.3f}</span>",
            f"<span style='font-size:12px; color:#2E7D32;'>Quality Range:</span> "
            f"<span style='font-size:12px; color:#263238;'>{min_quality:.3f} - {max_quality:.3f}</span>",
            f"<span style='font-size:12px; color:#2E7D32;'>Standard Deviation:</span> "
            f"<span style='font-size:12px; color:#263238;'>{std_quality:.3f}</span>",
            "",
            f"<span style='font-size:12px; color:#455A64; font-weight:bold;'>QUALITY DISTRIBUTION:</span>",
            f"<span style='font-size:12px; color:#2E7D32;'>High Quality (&gt;0.7):</span> "
            f"<span style='font-size:12px; color:#263238;'>{high_quality_pct:.1f}%</span>",
            f"<span style='font-size:12px; color:#2E7D32;'>Poor Quality (&lt;0.3):</span> "
            f"<span style='font-size:12px; color:#263238;'>{poor_quality_pct:.1f}%</span>",
            "",
            f"<span style='font-size:12px; color:#455A64; font-weight:bold;'>ADDITIONAL METRICS:</span>",
            f"<span style='font-size:12px; color:#2E7D32;'>SNR:</span> "
            f"<span style='font-size:12px; color:#263238;'>{snr_db:.1f} dB</span>",
            f"<span style='font-size:12px; color:#2E7D32;'>Invalid Data:</span> "
            f"<span style='font-size:12px; color:#263238;'>{invalid_count/samples*100 if samples > 0 else 0:.1f}%</span>",
            f"<span style='font-size:12px; color:#2E7D32;'>Duration:</span> "
            f"<span style='font-size:12px; color:#263238;'>{duration:.1f}s</span>",
            f"<span style='font-size:12px; color:#2E7D32;'>Samples:</span> "
            f"<span style='font-size:12px; color:#263238;'>{samples:,}</span>"
        ])
        
        self.quality_results.setText(results_text)
        self.log_status(f"Signal quality assessed: {quality_rating} (score: {mean_quality:.3f})")

    def export_data(self):
        """Export selected analysis data."""
        if self.raw_ppg_signal.size == 0:
            QtWidgets.QMessageBox.warning(self, "No Data", "No data available for export")
            return
        
        # Determine export content
        export_items = []
        if self.export_raw_check.isChecked():
            export_items.append("raw")
        if self.export_filtered_check.isChecked() and self.filtered_ppg_signal.size > 0:
            export_items.append("filtered")
        if self.export_peaks_check.isChecked() and self.peaks.size > 0:
            export_items.append("peaks")
        if self.export_hrv_check.isChecked() and self.hrv_metrics:
            export_items.append("hrv")
        if self.export_metadata_check.isChecked():
            export_items.append("metadata")
        
        if not export_items:
            QtWidgets.QMessageBox.warning(self, "No Selection", "Please select data to export")
            return
        
        # File dialog
        session_name = self.session_selector.currentText().split(" | ")[0]
        default_name = f"ppg_analysis_{self.current_user}_{session_name}"
        
        file_format = self.export_format_combo.currentText()
        ext = "csv" if file_format == "CSV" else "txt"
        file_filter = f"{ext.upper()} Files (*.{ext});;All Files (*)"
        
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, f"Export Data ({file_format})", 
            f"{default_name}.{ext}", file_filter
        )
        
        if not filename:
            return
        
        self._export_to_file(filename, export_items, file_format)
        QtWidgets.QMessageBox.information(
            self, "Export Successful", 
            f"Data exported successfully to:\n{os.path.basename(filename)}"
        )
        self.log_status(f"Data exported to {filename}")

    def _export_to_file(self, filename, export_items, file_format):
        """Handle actual file writing."""
        time_axis = np.arange(len(self.raw_ppg_signal)) / self.sampling_rate
        separator = ',' if file_format == "CSV" else '\t'
        
        # Main data
        data_dict = {'Time_s': time_axis}
        
        if "raw" in export_items:
            data_dict['Raw_PPG'] = self.raw_ppg_signal
        if "filtered" in export_items:
            data_dict['Filtered_PPG'] = self.filtered_ppg_signal
        
        df = pd.DataFrame(data_dict)
        
        # Peak markers
        if "peaks" in export_items:
            peak_column = np.zeros(len(time_axis))
            peak_column[self.peaks] = 1
            df['Peak_Marker'] = peak_column
        
        df.to_csv(filename, sep=separator, index=False)
        
        # Export HRV metrics separately
        if "hrv" in export_items and self.hrv_metrics:
            hrv_filename = filename.replace(f'.{filename.split(".")[-1]}', f'_hrv.{filename.split(".")[-1]}')
            self._export_hrv_data(hrv_filename, separator)
        
        # Export metadata separately
        if "metadata" in export_items and self.session_metadata:
            meta_filename = filename.replace(f'.{filename.split(".")[-1]}', f'_metadata.{filename.split(".")[-1]}')
            self._export_metadata(meta_filename, separator)

    def _export_hrv_data(self, filename, separator):
        """Export HRV metrics to separate file."""
        rows = []
        for category, metrics in self.hrv_metrics.items():
            for metric, value in metrics.items():
                rows.append({'Category': category, 'Metric': metric, 'Value': value})
        pd.DataFrame(rows).to_csv(filename, sep=separator, index=False)

    def _export_metadata(self, filename, separator):
        """Export session metadata to separate file."""
        rows = []
        for key, value in self.session_metadata.items():
            rows.append({'Parameter': key, 'Value': str(value)})
        pd.DataFrame(rows).to_csv(filename, sep=separator, index=False)

    def clear_all_data(self):
        """Clear all data and reset interface."""
        # Reset data
        self.raw_ppg_signal = np.array([])
        self.filtered_ppg_signal = np.array([])
        self.peaks = np.array([])
        self.time_axis = np.array([])
        self.session_metadata = {}
        self.filter_applied = False
        
        # Disable analysis tab
        self.control_tabs.setTabEnabled(2, False)
        
        # Reset results
        self.hrv_metrics = {}
        self.signal_quality_metrics = {}
        
        # Clear plots
        self.original_curve.clear()
        self.filtered_curve.clear()
        self.peak_scatter.clear()
        self.hrv_curve.clear()
        self.filter_response_curve.clear()
        self.clear_rr_lines()
        
        # Clear displays
        self.hrv_results.clear()
        self.quality_results.clear()
        self.metadata_label.setText("")
        
        for label in [self.samples_label, self.duration_label, self.missing_label, self.snr_label]:
            label.setText("-")

    def update_plot_view(self):
        """Update visible time range of plots using PlotNavigationMixin."""
        if self.time_axis.size == 0:
            return

        max_time = self.time_axis[-1]
        start_time, end_time = self.get_plot_view_range(max_time)
        
        self.original_plot.setXRange(start_time, end_time, padding=0)
        self.filtered_plot.setXRange(start_time, end_time, padding=0)
        self.hrv_plot.setXRange(start_time, end_time, padding=0)

    def update_slider(self):
        """Update plot navigation slider using PlotNavigationMixin."""
        if self.time_axis.size == 0:
            self.plot_slider.setMaximum(0)
            return

        max_time = self.time_axis[-1]
        self.update_plot_slider(max_time=max_time)