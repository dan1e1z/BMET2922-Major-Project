
from PyQt5 import QtWidgets, QtCore, QtGui
from ui_components import UserManager, SystemLog

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

        # Set up the main window UI
        self.setup_main_window_ui()

        # Add initial log entry
        self.system_log.add_log_entry("Application started")

    def setup_main_window_ui(self):
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

        # Add the system log widget
        self.system_log = SystemLog()
        layout.addWidget(self.system_log)

        # Exit button to close the application
        exit_btn = QtWidgets.QPushButton("Exit Application")
        exit_btn.clicked.connect(self.close)
        layout.addWidget(exit_btn)

        # Set the layout on the central widget
        central_widget.setLayout(layout)



    def close_window(self):
        """
        Handle closing the application and log the event.
        """
        self.system_log.add_log_entry("Application closed")
        QtWidgets.QApplication.quit()

        
