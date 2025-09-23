from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg
import numpy as np 
from datetime import datetime


class LiveMonitorTab(QtWidgets.QWidget):

    """
    A PyQt5 widget for real-time heart rate monitoring with visual plots and alarm system.
    
    This class provides:
    - Real-time BPM and raw PPG signal visualization with a sliding window
    - User session management and data logging
    - Configurable BPM alarm thresholds with visual/audio alerts
    - Live statistics display
    
    Attributes:
        current_user (str): Currently logged in user
        session_raw_ppg (list): Raw PPG data for current session
        session_start_time (datetime): When current session started
        session_bpm (list): BPM readings for current session
        visual_bpm_data (list): BPM data used for plotting
        visual_raw_pgg_data (list): Raw PPG data used for plotting
        time_bpm_data (list): Timestamps for BPM data points
        time_ppg_data (list): Timestamps for raw PPG data points
        last_packet_time (float): Time of the last received data packet
        plot_window_seconds (int): Duration of the visible plot window in seconds
        is_auto_scrolling (bool): Flag to control if plots auto-scroll to the latest data
        current_bpm (float): Most recent BPM reading
        bpm_low (int): Lower threshold for BPM alarm
        bpm_high (int): Upper threshold for BPM alarm
        alarm_active (bool): Whether alarm is currently triggered
    """
    def __init__(self, system_log):
        super().__init__()

        # User/session management variables
        self.current_user = None
        self.session_raw_ppg = []
        self.session_start_time = None
        self.session_bpm = []

        # System log widget
        self.system_log = system_log

        # Data arrays for visualization
        self.visual_bpm_data = []
        self.visual_raw_pgg_data = []
        self.time_bpm_data = []
        self.time_ppg_data = []
        self.last_packet_time = 0
        
        # Plot window settings
        self.plot_window_seconds = 5
        self.is_auto_scrolling = True

        # BPM and alarm variables
        self.current_bpm = 0
        self.bpm_low = 40
        self.bpm_high = 200
        self.alarm_active = False

        # Initialize the user interface
        self.setup_ui()

    def setup_ui(self):
        """
        Set up the UI for the live monitor tab, including plots, controls, and the new plot slider.
        """
        main_layout = QtWidgets.QVBoxLayout()
        plots_layout = QtWidgets.QVBoxLayout()

        # BPM Plot
        self.bpm_plot = pg.PlotWidget()
        self.bpm_plot.setLabel('left', 'BPM')
        self.bpm_plot.setLabel('bottom', 'Time', units='s')
        self.bpm_plot.showGrid(True, True)
        self.bpm_plot.setMouseEnabled(x=False, y=False)
        self.bpm_plot.setMenuEnabled(False)
        self.bpm_curve = self.bpm_plot.plot(pen=pg.mkPen('r', width=2))
        plots_layout.addWidget(self.bpm_plot)

        # Raw PPG Plot
        self.raw_ppg_plot = pg.PlotWidget()
        self.raw_ppg_plot.setLabel('left', 'PPG Raw')
        self.raw_ppg_plot.setLabel('bottom', 'Time', units='s')
        self.raw_ppg_plot.showGrid(True, True)
        self.raw_ppg_plot.setMouseEnabled(x=False, y=False)
        self.raw_ppg_plot.setMenuEnabled(False)
        self.raw_ppg_curve = self.raw_ppg_plot.plot(pen=pg.mkPen('b', width=2))
        plots_layout.addWidget(self.raw_ppg_plot)

        # Plot controls (slider and checkbox)
        plot_controls_layout = QtWidgets.QHBoxLayout()
        self.auto_scroll_checkbox = QtWidgets.QCheckBox("Auto-Scroll")
        self.auto_scroll_checkbox.setChecked(self.is_auto_scrolling)
        self.auto_scroll_checkbox.stateChanged.connect(self.toggle_auto_scroll)
        plot_controls_layout.addWidget(self.auto_scroll_checkbox)

        self.plot_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.plot_slider.setRange(0, 0)
        self.plot_slider.valueChanged.connect(self.scroll_plots)
        self.plot_slider.sliderPressed.connect(self.disable_auto_scroll)
        plot_controls_layout.addWidget(self.plot_slider)
        plots_layout.addLayout(plot_controls_layout)

        # Session info
        self.session_info = QtWidgets.QLabel("Not logged in")
        self.session_info.setAlignment(QtCore.Qt.AlignRight)

        # Right side controls
        controls_layout = QtWidgets.QVBoxLayout()
        controls_widget = QtWidgets.QWidget()
        controls_widget.setStyleSheet("background-color: #f0f0f0; border-radius: 10px; padding: 10px; border: 1px solid #ccc;")

        self.bpm_display = QtWidgets.QLabel("-- BPM")
        self.bpm_display.setAlignment(QtCore.Qt.AlignCenter)
        self.bpm_display.setStyleSheet("font-size: 48px; font-weight: bold; color: #2E7D32;")

        self.alarm_widget = QtWidgets.QLabel("")
        self.alarm_widget.setAlignment(QtCore.Qt.AlignCenter)
        self.alarm_widget.setVisible(False)
        self.alarm_widget.setStyleSheet("font-size: 16px; font-weight: bold; color: white; background-color: #f44336; border: 3px solid #d32f2f; border-radius: 10px; padding: 10px;")

        self.current_stats = QtWidgets.QLabel("")
        self.current_stats.setAlignment(QtCore.Qt.AlignCenter)
        self.current_stats.setStyleSheet("background-color: #e0e0e0; padding: 10px; border-radius: 5px; margin: 5px;")
        self.current_stats.setWordWrap(True)

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

        controls_layout.addWidget(self.bpm_display)
        controls_layout.addWidget(self.alarm_widget)
        controls_layout.addWidget(self.current_stats)
        controls_layout.addWidget(self.low_label)
        controls_layout.addWidget(self.low_slider)
        controls_layout.addWidget(self.high_label)
        controls_layout.addWidget(self.high_slider)
        controls_layout.addStretch()
        controls_widget.setLayout(controls_layout)

        content_layout = QtWidgets.QHBoxLayout()
        content_layout.addLayout(plots_layout, 3)
        content_layout.addWidget(controls_widget, 1)
        main_layout.addLayout(content_layout)
        main_layout.addWidget(self.system_log)
        self.setLayout(main_layout)

        self.alarm_timer = QtCore.QTimer()
        self.alarm_timer.timeout.connect(self.blink_alarm)
        self.alarm_visible = True

    def new_data_received(self, packet):
        """
        Process new data packet, generate timestamps, and update plots.
        """
        bpm = packet['bpm']
        self.current_bpm = bpm

        # Assumes packets arrive roughly 1 per second
        current_time = self.last_packet_time
        self.last_packet_time += 1

        if bpm > 0:
            self.bpm_display.setText(f"{bpm:.1f} BPM")
            alarm_msg = self.check_bpm_alarm()
            if alarm_msg:
                return alarm_msg
            
            if self.current_user:
                self.session_bpm.append(bpm)
                self.session_raw_ppg.extend(packet["ppg_values"])
        else:
            self.bpm_display.setText("-- BPM")

        # Store data for plotting
        self.visual_bpm_data.append(bpm)
        self.time_bpm_data.append(current_time)
        
        ppg_values = packet["ppg_values"]
        # Generate timestamps for the 50 PPG samples over the last second
        ppg_times = np.linspace(current_time - 1, current_time, len(ppg_values), endpoint=False)
        self.visual_raw_pgg_data.extend(ppg_values)
        self.time_ppg_data.extend(ppg_times)

        self.update_plots()
        return

    def update_plots(self):
        """
        Update plot data and view window.
        """
        if len(self.time_bpm_data) > 1:
            self.bpm_curve.setData(self.time_bpm_data, self.visual_bpm_data)
        if len(self.time_ppg_data) > 1:
            self.raw_ppg_curve.setData(self.time_ppg_data, self.visual_raw_pgg_data)
        
        self.update_plot_view()
        self.update_slider()

    def update_plot_view(self):
        """
        Sets the visible range of the plots based on slider position or auto-scroll.
        """
        max_time = self.time_ppg_data[-1] if self.time_ppg_data else 0
        
        if self.is_auto_scrolling:
            start_time = max(0, max_time - self.plot_window_seconds)
        else:
            start_time = self.plot_slider.value() / 100.0
            
        end_time = start_time + self.plot_window_seconds
        self.bpm_plot.setXRange(start_time, end_time, padding=0)
        self.raw_ppg_plot.setXRange(start_time, end_time, padding=0)

    def update_slider(self):
        """
        Updates the range and position of the time-scroll slider IF auto-scrolling.
        """
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
        """
        Update the plot view when the slider is moved manually.
        """
        if not self.is_auto_scrolling:
            self.update_plot_view()

    def disable_auto_scroll(self):
        """
        Disables auto-scrolling when the user interacts with the slider.
        """
        self.auto_scroll_checkbox.setChecked(False)

    def toggle_auto_scroll(self, state):
        """
        Enables or disables auto-scrolling based on the checkbox state.
        """
        self.is_auto_scrolling = (state == QtCore.Qt.Checked)
        if self.is_auto_scrolling:
            self.update_slider()
            self.update_plot_view()

    def start_session(self, username):
        self.current_user = username
        self.session_start_time = datetime.now()
        self.update_session_info()

    def update_session_info(self):
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
        self.bpm_low = self.low_slider.value()
        self.bpm_high = self.high_slider.value()
        self.low_label.setText(f"Low BPM Warning: {self.bpm_low}")
        self.high_label.setText(f"High BPM Warning: {self.bpm_high}")

    def blink_alarm(self):
        if self.alarm_active:
            self.alarm_visible = not self.alarm_visible
            self.alarm_widget.setVisible(self.alarm_visible)

    def check_bpm_alarm(self):
        prev_state = self.alarm_active
        msg = None

        if self.current_bpm < self.bpm_low:
            self.alarm_active = True
            self.alarm_widget.setText(f"WARNING: PULSE LOW: {self.current_bpm:.1f} BPM")
            if not prev_state:
                self.alarm_timer.start(500)
                msg = "Pulse Low"
                
        elif self.current_bpm > self.bpm_high:
            self.alarm_active = True
            self.alarm_widget.setText(f"WARNING: PULSE HIGH: {self.current_bpm:.1f} BPM")
            if not prev_state:
                self.alarm_timer.start(500)
                msg = "Pulse High"
                
        else:
            if prev_state:
                self.alarm_active = False
                self.alarm_widget.setVisible(False)
                self.alarm_timer.stop()
                msg = "Pulse Normal"
                
        return msg
