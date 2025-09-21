
from PyQt5 import QtWidgets, QtCore, QtGui
from datetime import datetime
from ui_components import UserManager, SystemLog, BluetoothConnectionStatus
from ui_tabs import AccountTab, LiveMonitorTab, HistoryTab

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
        self.setGeometry(100, 100, 1200, 800)

        # User/session management variables
        self.user_manager = UserManager()
        self.current_user = None
        self.session_start_time = None
        self.packet_sequence = 0
        self.expected_sequence = 0

        # System log widget
        self.system_log = SystemLog()
        self.connection_status = BluetoothConnectionStatus()

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
        layout.addWidget(title)

        layout.addWidget(self.connection_status)

        self.tabs = QtWidgets.QTabWidget()

        self.live_monitor_tab = LiveMonitorTab(self.system_log)
        self.login_tab = AccountTab(self.user_manager)
        self.history_tab = HistoryTab()

        self.tabs.addTab(self.live_monitor_tab, "Live Monitor")
        self.tabs.addTab(self.login_tab, "Account")
        self.tabs.addTab(self.history_tab, "Health History")
        
        # Connect signals
        self.login_tab.login_successful.connect(self.handle_login)
        self.login_tab.logout_requested.connect(self.handle_logout)
        
        layout.addWidget(self.tabs)

        # Status bar
        self.status_bar = QtWidgets.QLabel("Ready - Please log in to start recording session data")
        layout.addWidget(self.status_bar)

        # Exit button to close the application
        exit_btn = QtWidgets.QPushButton("Exit Application")
        exit_btn.clicked.connect(self.close)
        layout.addWidget(exit_btn)

        # Set the layout on the central widget
        central_widget.setLayout(layout)



    def handle_login(self, username):
        """
        Handle user login event.
        Updates session state, status bar, logs the event, and switches to the Live Monitor tab.
        Args:
            username (str): The username of the logged-in user.
        """
        self.current_user = username
        self.session_start_time = datetime.now()
        self.expected_sequence = 0

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
        # Log the logout event
        if self.current_user:
            self.system_log.add_log_entry(f"User '{self.current_user}' logged out")

        # Update status bar
        self.status_bar.setText("Logged out - Please log in to start recording session data")


    def close_window(self):
        """
        Handle closing the application and log the event.
        """
        self.system_log.add_log_entry("Application closed")
        QtWidgets.QApplication.quit()

        
