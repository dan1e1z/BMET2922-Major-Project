from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg
class LiveMonitorTab(QtWidgets.QWidget):
    def __init__(self, system_log):
        super().__init__()
        self.current_user = None
        self.session_raw_ppg = []
        self.session_start_time = None
        self.current_bpm = 0
        self.system_log = system_log

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
        self.bpm_plot.enableAutoRange(False)  # Prevent auto-scaling
        self.bpm_curve = self.bpm_plot.plot(pen=pg.mkPen('r', width=2))  # Red curve for BPM
        plots_layout.addWidget(self.bpm_plot)

        # Raw PPG Plot: shows raw photoplethysmogram signal
        self.raw_ppg_plot = pg.PlotWidget()
        self.raw_ppg_plot.setLabel('left', 'PPG Raw')  # Y-axis label
        self.raw_ppg_plot.setLabel('bottom', 'Time', units='s')  # X-axis label
        self.raw_ppg_plot.showGrid(True, True)  # Show grid lines
        self.raw_ppg_plot.setMouseEnabled(x=False, y=False)  # Disable mouse interaction
        self.raw_ppg_plot.setMenuEnabled(False)  # Disable context menu
        self.raw_ppg_plot.enableAutoRange(False)  # Prevent auto-scaling
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

    pass