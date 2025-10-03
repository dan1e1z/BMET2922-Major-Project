
from PyQt5 import QtWidgets, QtCore, QtGui
from datetime import datetime
import numpy as np

from gui.ui_tabs import (
    AccountTab,
    HistoryTab,
    LiveMonitorTab,
    ResearchTab
)
from gui.ui_components import (
    BluetoothConnectionStatus,
    SystemLog,
    UserManager
)
from gui.bluetooth_monitor import BluetoothMonitor


class MainWindow(QtWidgets.QMainWindow):
    """
    Main application window for the PPG Health Monitor.
    Handles UI setup, user management, and system logging.
    """
    def __init__(self):
        """
        Initialize the main window, set up UI, and initialize user/session variables.
        """
        super().__init__()
        self.setWindowTitle("PPG Health Monitor")
        # self.setGeometry(100, 100, 1200, 800)

        # User/session management variables
        self.user_manager = UserManager()
        self.current_user = None
        self.session_start_time = None
        self.packet_sequence = 0
        self.expected_sequence = 0

        # System log widget
        self.system_log = SystemLog()

        # Bluetooth connection status widget
        self.connection_status = BluetoothConnectionStatus()

        # setup thread to run Bluetooth Monitor
        self.bluetooth_monitor = BluetoothMonitor()
        self.bluetooth_monitor_thread = QtCore.QThread()
        self.bluetooth_monitor.moveToThread(self.bluetooth_monitor_thread)
        self.bluetooth_monitor_thread.started.connect(self.bluetooth_monitor.monitor)

        # Receive signals (packets) from BluetoothMonitor
        self.bluetooth_monitor.packet_received.connect(self.handle_new_packet)
        self.bluetooth_monitor.connection_status_changed.connect(self.handle_connection_status)
        self.bluetooth_monitor.connection_timeout.connect(self.handle_connection_timeout)

        self.bluetooth_monitor_thread.start()

        # Set up the main window UI
        self.setup_ui()

        # Add initial log entry
        self.system_log.add_log_entry("Application started")

    def setup_ui(self):
        """
        Set up the main window's UI components and layout.
        Creates a central widget, adds a title, system log, and exit button.
        """
        # Create a central widget for the main window
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)

        # Create a vertical layout for the central widget
        layout = QtWidgets.QVBoxLayout()

        # Main title label
        title = QtWidgets.QLabel("PPG Health Monitor")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2E7D32; margin: 10px;")
        layout.addWidget(title)

        # Bluetooth connection status
        layout.addWidget(self.connection_status)

        self.serial_reader = BluetoothMonitor()

        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #C0C0C0;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #E0E0E0;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #4CAF50;
                color: white;
            }
        """)

        self.live_monitor_tab = LiveMonitorTab(self.system_log)
        self.account_tab = AccountTab(self.user_manager)
        self.history_tab = HistoryTab()
        self.research_tab = ResearchTab()

        self.tabs.addTab(self.live_monitor_tab, "Live Monitor")
        self.tabs.addTab(self.account_tab, "Account")
        self.tabs.addTab(self.history_tab, "Health History")
        self.tabs.addTab(self.research_tab, "Research")

        self.tabs.setTabEnabled(2, False) 
        self.tabs.setTabEnabled(3, False) 

        
        # Connect signals
        self.account_tab.login_successful.connect(self.handle_login)
        self.account_tab.logout_requested.connect(self.handle_logout)
        
        layout.addWidget(self.tabs)

        # Status bar
        self.status_bar = QtWidgets.QLabel("Ready - Please log in to start recording session data")
        self.status_bar.setStyleSheet("background-color: #f0f0f0; padding: 5px; border-top: 1px solid #ccc;")
        layout.addWidget(self.status_bar)

        # Exit button to close the application
        exit_btn = QtWidgets.QPushButton("Exit Application")
        exit_btn.setStyleSheet("QPushButton { background-color: #757575; color: white; padding: 8px; border: none; border-radius: 4px; }")
        exit_btn.clicked.connect(self.close_window)
        layout.addWidget(exit_btn)

        # Set the layout on the central widget
        central_widget.setLayout(layout)



    def handle_login(self, username, account_type):
        """
        Handle user login event.
        Updates session state, status bar, logs the event, and switches to the Live Monitor tab.
        Args:
            username (str): The username of the logged-in user.
        """
        self.current_user = username
        self.session_start_time = datetime.now()
        self.expected_sequence = 0

        # Enable history tab and update
        self.tabs.setTabEnabled(2, True)

        if account_type == "advanced":
            self.tabs.setTabEnabled(3, True)
            self.research_tab.start_session(username, self.user_manager)
        self.history_tab.start_session(username, self.user_manager)

        # Start session in live monitor tab
        self.live_monitor_tab.start_session(username)

        # Update status bar with session info
        self.status_bar.setText(f"Recording session for {username} - Session started at {self.session_start_time.strftime('%H:%M:%S')}")

        # Log the login event
        self.system_log.add_log_entry(f"User '{username}' logged in")

        # Switch to Live Monitor tab
        self.tabs.setCurrentIndex(0)
    
    def handle_logout(self):
        """
        Handle user logout event.
        Logs the event and updates the status bar.
        """

        if self.current_user and self.live_monitor_tab.session_bpm:
            self.save_current_session()

        # Log the logout event
        if self.current_user:
            self.system_log.add_log_entry(f"User '{self.current_user}' logged out")

        # Reset state
        self.current_user = None
        self.session_start_time = None
        self.tabs.setTabEnabled(2, False)
        self.tabs.setTabEnabled(3, False)

        
        # Reset live monitor tab
        self.live_monitor_tab.current_user = None
        self.live_monitor_tab.session_bpm = []
        self.live_monitor_tab.session_start_time = None
        
        # Update status
        self.status_bar.setText("Logged out - Please log in to start recording session data")

    def close_window(self):
        """
        Handle closing the application and log the event.
        """
        # DEBUG PRINTS
        # print("closing window")
        # print("self.current_user:", self.current_user)
        # print("self.live_monitor_tab.session_bpm:", self.live_monitor_tab.session_bpm)

        # Save current session if user is logged in & has session data
        if self.current_user and self.live_monitor_tab.session_bpm:
            # print("saving session")
            self.save_current_session()
        
        # Log application exit
        self.system_log.add_log_entry("Application closing")
        
        # Stop serial reader
        self.bluetooth_monitor.running = False
        self.bluetooth_monitor_thread.quit()
        self.bluetooth_monitor_thread.wait()

        QtWidgets.QApplication.quit()

    def closeEvent(self, event):
        """
        Overrides the close event to ask for confirmation before closing.
        """
        event.accept()
        # reply = QtWidgets.QMessageBox.question(self, 'Confirm Close',
        #     "Do you want to save your session and quit?",
        #     QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel)

        # if reply == QtWidgets.QMessageBox.Yes:
        #     print("Saving session and closing...")
        #     self.close_window() 
        #     event.accept()
        # elif reply == QtWidgets.QMessageBox.No:
        #     print("Closing without saving...")
        #     event.accept()
        # else:
        #     print("Close operation canceled.")
        #     event.ignore()


    def handle_new_packet(self, packet):
        sequence = packet.get('sequence', 0)
        self.expected_sequence = sequence
        if self.expected_sequence != sequence:
            self.system_log.add_log_entry(f"Packet sequence mismatch: expected {self.expected_sequence}, got {sequence}")
        self.expected_sequence += 1

        # Process the packet in PPG tab and check for alarms
        alarm_message = self.live_monitor_tab.new_data_received(packet)
        if alarm_message:
            self.system_log.add_log_entry(alarm_message)

        if self.current_user:
            bpm = packet.get('bpm', 0)
            current_samples = len(self.live_monitor_tab.session_bpm) * 50
            duration = (datetime.now() - self.session_start_time).total_seconds() / 60
            self.status_bar.setText(f"Recording for {self.current_user} | Current BPM: {bpm:.1f} | Duration: {duration:.1f}min | Samples: {current_samples}")

    def handle_connection_status(self, connected, message):
        self.connection_status.update_status(connected, message)
        pass

    def handle_connection_timeout(self):
        """Handle timeout when no packets received for 5+ seconds"""
        self.connection_status.show_timeout_alarm()
        self.system_log.add_log_entry("No data received for 5+ seconds - Check sensor power")

    def save_current_session(self):
        # print("save current session")

        session_raw_ppg = self.live_monitor_tab.session_raw_ppg
        session_bpm = self.live_monitor_tab.session_bpm
        end_time = datetime.now()
        duration = (end_time - self.session_start_time).total_seconds() / 60

        avg_bpm = float(np.mean(session_bpm))
        min_bpm = float(np.min(session_bpm))
        max_bpm = float(np.max(session_bpm))

        abnormal_low = sum(1 for x in session_bpm if x < self.live_monitor_tab.bpm_low)
        abnormal_high = sum(1 for x in session_bpm if x > self.live_monitor_tab.bpm_high)

        session_data = {
            "start": self.session_start_time.isoformat(),
            "end": end_time.isoformat(),
            "duration_minutes": duration,
            "avg_bpm": avg_bpm,
            "min_bpm": min_bpm,
            "max_bpm": max_bpm,
            "total_samples": len(session_bpm),
            "abnormal_low": abnormal_low,
            "abnormal_high": abnormal_high,
            "bpm_low_threshold": self.live_monitor_tab.bpm_low,
            "bpm_high_threshold": self.live_monitor_tab.bpm_high,
            "raw_ppg": session_raw_ppg
        }

        self.user_manager.save_session(self.current_user, session_data)

        if hasattr(self.history_tab, 'current_user') and self.history_tab.current_user == self.current_user:
            self.history_tab.update_history_view()

        self.system_log.add_log_entry(
            f"Session saved: {duration:.1f} min, {len(session_bpm)} samples, avg BPM: {avg_bpm:.1f}, "
            f"Thresholds: {self.live_monitor_tab.bpm_low}-{self.live_monitor_tab.bpm_high}"
        )
        print(f"Session saved for {self.current_user}: {duration:.1f} min, {len(session_bpm)} samples, "
              f"avg BPM: {avg_bpm:.1f}, thresholds {self.live_monitor_tab.bpm_low}-{self.live_monitor_tab.bpm_high}")