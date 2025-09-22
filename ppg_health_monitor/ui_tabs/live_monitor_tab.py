from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg
import numpy as np 
from datetime import datetime


class LiveMonitorTab(QtWidgets.QWidget):
    def __init__(self, system_log):
        super().__init__()

        # User/session management variables
        self.current_user = None
        self.session_raw_ppg = []
        self.session_start_time = None
        self.session_bpm = []

        # System log wdiget
        self.system_log = system_log

        # Data used for visualization
        self.visual_bpm_data = []
        self.visual_raw_pgg_data = []
        self.current_bpm = 0

        self.setup_ui()

    def setup_ui(self):
        """
        Set up the UI for the live monitor tab, including plots and controls with proper layout and stretch factors.
        """
        # Main vertical layout for the tab
        main_layout = QtWidgets.QVBoxLayout()

        # --- Plots layout ---
        # This layout will stack the BPM and raw PPG plots vertically
        plots_layout = QtWidgets.QVBoxLayout()

        # BPM Plot: shows heart rate over time
        self.bpm_plot = pg.PlotWidget()
        self.bpm_plot.setLabel('left', 'BPM')  # Y-axis label
        self.bpm_plot.setLabel('bottom', 'Time', units='s')  # X-axis label
        self.bpm_plot.showGrid(True, True)  # Show grid lines
        self.bpm_plot.setMouseEnabled(x=False, y=False)  # Disable mouse interaction
        self.bpm_plot.setMenuEnabled(False)  # Disable context menu
        # self.bpm_plot.enableAutoRange(False)  # Prevent auto-scaling
        self.bpm_curve = self.bpm_plot.plot(pen=pg.mkPen('r', width=2))  # Red curve for BPM
        plots_layout.addWidget(self.bpm_plot)

        # Raw PPG Plot: shows raw photoplethysmogram signal
        self.raw_ppg_plot = pg.PlotWidget()
        self.raw_ppg_plot.setLabel('left', 'PPG Raw')  # Y-axis label
        self.raw_ppg_plot.setLabel('bottom', 'Time', units='s')  # X-axis label
        self.raw_ppg_plot.showGrid(True, True)  # Show grid lines
        self.raw_ppg_plot.setMouseEnabled(x=False, y=False)  # Disable mouse interaction
        self.raw_ppg_plot.setMenuEnabled(False)  # Disable context menu
        # self.raw_ppg_plot.enableAutoRange(False)  # Prevent auto-scaling
        self.raw_ppg_curve = self.raw_ppg_plot.plot(pen=pg.mkPen('b', width=2))  # Blue curve for PPG
        plots_layout.addWidget(self.raw_ppg_plot)

        # Session info label (aligned right, can show user/session status)
        self.session_info = QtWidgets.QLabel("Not logged in")
        self.session_info.setAlignment(QtCore.Qt.AlignRight)

        # --- Right side controls ---
        # Controls layout for widgets like BPM display and future controls
        controls_layout = QtWidgets.QVBoxLayout()
        controls_widget = QtWidgets.QWidget()

        # BPM display: shows current BPM value
        self.bpm_display = QtWidgets.QLabel("-- BPM")
        self.bpm_display.setAlignment(QtCore.Qt.AlignCenter)
        controls_layout.addWidget(self.bpm_display)
        controls_widget.setLayout(controls_layout)

        # Combine plots and controls horizontally
        content_layout = QtWidgets.QHBoxLayout()

        content_layout.addLayout(plots_layout, 3)
        content_layout.addWidget(controls_widget, 1)
        main_layout.addLayout(content_layout)

        # Add system log widget at the bottom
        main_layout.addWidget(self.system_log)

        # Set the main layout for this tab
        self.setLayout(main_layout)

        self.setLayout(main_layout)

    def new_data_received(self, packet):
        
        # DEBUGGING PRINTS
        # print("packet: ", packet)
        # print ("bpm: ", packet['bpm'])
        # print("ppg_values:", packet["ppg_values"])

        bpm = packet['bpm']
        self.current_bpm = packet['bpm']

        if  bpm > 0:
            self.bpm_display.setText(f"{bpm:.1f} BPM")

            # add bpm to logined user session data
            # print("self.current_user: ", self.current_user)
            if self.current_user:
                # print("adding bpm to session")
                self.session_bpm.append(bpm)
        else:
            self.bpm_display.setText("-- BPM")

        # Store data for plotting
        self.visual_bpm_data.append(bpm)
        self.visual_raw_pgg_data.extend(packet["ppg_values"])

        # update render plots
        self.update_plots()
        return

    def update_plots(self):
        if len(self.visual_bpm_data) > 1:
            self.bpm_curve.setData(np.arange(len(self.visual_bpm_data)), np.array(self.visual_bpm_data))
        if len(self.visual_raw_pgg_data) > 1:
            self.raw_ppg_curve.setData(np.arange(len(self.visual_raw_pgg_data)), np.array(self.visual_raw_pgg_data))


    def start_session(self, username):
        self.current_user = username
        self.session_start_time = datetime.now()
        self.update_session_info()

    def update_session_info(self):
        if self.current_user and self.session_start_time:
            duration = datetime.now() - self.session_start_time
            minutes = duration.total_seconds() / 60
            self.session_info.setText(f"Recording: {minutes:.1f} min | Samples: {len(self.session_bpm)}")
            
            # Update current stats
            if self.session_bpm:
                current_bpm = self.session_bpm[-1] if self.session_bpm else 0
                avg_bpm = np.mean(self.session_bpm)
                
                stats_text = f"Current: {current_bpm:.1f} BPM\nAvg: {avg_bpm:.1f}"
                self.current_stats.setText(stats_text)
        else:
            self.session_info.setText("Not recording")
            self.current_stats.setText("Please log in to start recording session data")
