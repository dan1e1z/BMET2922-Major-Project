from PyQt5 import QtWidgets, QtCore
from datetime import datetime

class AccountTab(QtWidgets.QWidget):
    """
    Tab widget for user account management.
    Handles login, signup, and logout functionality, and displays user stats.
    """
    login_successful = QtCore.pyqtSignal(str, str)
    logout_requested = QtCore.pyqtSignal()

    def __init__(self, user_manager):
        """
        Initialize the AccountTab with a user manager.
        Sets up UI and initializes user state.
        Args:
            user_manager: The user manager object for handling authentication.
        """
        super().__init__()
        self.user_manager = user_manager
        self.current_user = None
        self.setup_ui()

    def setup_ui(self):
        """
        Set up the UI for the account tab, including stacked widgets for login, signup, and logged-in views.
        Also sets up tab buttons and status label.
        """
        layout = QtWidgets.QVBoxLayout()

        # Title label
        title = QtWidgets.QLabel("Account Management")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)

        # Stacked widget for switching between login, signup, and logged-in views
        self.stacked = QtWidgets.QStackedWidget()
        self.login_widget = self.create_login_form()
        self.signup_widget = self.create_signup_form()
        self.logged_in_widget = self.create_logged_in_widget()
        self.stacked.addWidget(self.login_widget)
        self.stacked.addWidget(self.signup_widget)
        self.stacked.addWidget(self.logged_in_widget)
        layout.addWidget(self.stacked)

        # Tab buttons for switching between login and signup
        self.tab_buttons_widget = QtWidgets.QWidget()
        btn_layout = QtWidgets.QHBoxLayout()
        self.login_tab_btn = QtWidgets.QPushButton("Login")
        self.signup_tab_btn = QtWidgets.QPushButton("Sign Up")

        self.login_tab_btn.setStyleSheet("QPushButton { padding: 8px; margin: 2px; }")
        self.signup_tab_btn.setStyleSheet("QPushButton { padding: 8px; margin: 2px; }")

        self.login_tab_btn.clicked.connect(self.show_login)
        self.signup_tab_btn.clicked.connect(self.show_signup)
        btn_layout.addWidget(self.login_tab_btn)
        btn_layout.addWidget(self.signup_tab_btn)
        self.tab_buttons_widget.setLayout(btn_layout)
        layout.addWidget(self.tab_buttons_widget)

        # Status label for displaying messages
        self.status_label = QtWidgets.QLabel("")
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)
        self.status_label.setStyleSheet("color: blue; font-weight: bold; margin: 10px;")
        layout.addWidget(self.status_label)

        self.setLayout(layout)
        self.show_login()

    def show_login(self):
        """
        Show the login form and update tab button states.
        """
        self.stacked.setCurrentWidget(self.login_widget)
        self.login_tab_btn.setEnabled(False)
        self.signup_tab_btn.setEnabled(True)

    def show_signup(self):
        """
        Show the signup form and update tab button states.
        """
        self.stacked.setCurrentWidget(self.signup_widget)
        self.login_tab_btn.setEnabled(True)
        self.signup_tab_btn.setEnabled(False)

    def create_login_form(self):
        """
        Create and return the login form widget.
        """
        w = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout()
        layout.setSpacing(15)

        self.login_user = QtWidgets.QLineEdit()
        self.login_pass = QtWidgets.QLineEdit()
        self.login_pass.setEchoMode(QtWidgets.QLineEdit.Password)

        self.login_user.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 4px;")
        self.login_pass.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 4px;")

        btn = QtWidgets.QPushButton("Login")
        btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 10px; border: none; border-radius: 4px; font-weight: bold; }")
        btn.clicked.connect(self.handle_login)

        layout.addRow("Username:", self.login_user)
        layout.addRow("Password:", self.login_pass)
        layout.addRow("", btn)

        w.setLayout(layout)
        return w
    
    def create_signup_form(self):
        """
        Create and return the signup form widget with Personal/Advanced user types.
        """
        w = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout()
        layout.setSpacing(15)
        
        # --- Input Fields ---
        self.signup_user = QtWidgets.QLineEdit()
        self.signup_pass = QtWidgets.QLineEdit()
        self.signup_pass.setEchoMode(QtWidgets.QLineEdit.Password)
        self.signup_confirm = QtWidgets.QLineEdit()
        self.signup_confirm.setEchoMode(QtWidgets.QLineEdit.Password)
        
        # --- User Type Selection ---
        # --- Create the radio buttons ---
        self.personal_radio = QtWidgets.QRadioButton("Personal")
        self.advanced_radio = QtWidgets.QRadioButton("Advanced")
        self.personal_radio.setChecked(True)  # Set "Personal" as the default
        
        # --- Create the helper text labels ---
        personal_label = QtWidgets.QLabel("Best for tracking daily health and viewing your history.")
        advanced_label = QtWidgets.QLabel("For researchers and enthusiasts. Includes history viewing and tools for raw signal analysis.")
        
        # Style the helper text consistently
        helper_style = "color: #666; font-size: 11px;"
        personal_label.setStyleSheet(helper_style)
        advanced_label.setStyleSheet(helper_style)
        
        personal_layout = QtWidgets.QVBoxLayout()
        personal_layout.setContentsMargins(0, 0, 0, 0)  # Remove extra spacing
        personal_layout.addWidget(self.personal_radio)
        personal_layout.addWidget(personal_label)
        
        advanced_layout = QtWidgets.QVBoxLayout()
        advanced_layout.setContentsMargins(0, 0, 0, 0)
        advanced_layout.addWidget(self.advanced_radio)
        advanced_layout.addWidget(advanced_label)
        
        # --- Add the layouts to the main radio button container ---
        radio_button_layout = QtWidgets.QHBoxLayout()
        radio_button_layout.addLayout(personal_layout)
        radio_button_layout.addLayout(advanced_layout)
        radio_button_layout.addStretch()
        
        radio_container = QtWidgets.QWidget()
        radio_container.setLayout(radio_button_layout)
        
        # --- Consistent Styling ---
        # Input field styling
        input_style = "padding: 10px; border: 1px solid #ccc; border-radius: 4px; font-size: 14px;"
        for field in [self.signup_user, self.signup_pass, self.signup_confirm]:
            field.setStyleSheet(input_style)
        
        # Button styling
        btn = QtWidgets.QPushButton("Sign Up")
        btn_style = """
            QPushButton { 
                background-color: #008CBA; 
                color: white; 
                padding: 10px 20px; 
                border: none; 
                border-radius: 4px; 
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { 
                background-color: #007B9A; 
            }
        """
        btn.setStyleSheet(btn_style)
        btn.clicked.connect(self.handle_signup)
        
        # --- Add Widgets to Form Layout ---
        layout.addRow("Username:", self.signup_user)
        layout.addRow("Password:", self.signup_pass)
        layout.addRow("Confirm Password:", self.signup_confirm)
        layout.addRow("Account Type:", radio_container)
        layout.addRow("", btn)
        
        w.setLayout(layout)
        return w
    
    def create_logged_in_widget(self):
        """
        Create and return the widget shown when the user is logged in.
        Displays welcome message, user stats, and logout button.
        """
        w = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(20)

        self.welcome_label = QtWidgets.QLabel("")
        self.welcome_label.setAlignment(QtCore.Qt.AlignCenter)
        self.welcome_label.setStyleSheet("font-size: 16px; color: #2E7D32; font-weight: bold; margin: 20px;")


        # User stats label
        self.stats_label = QtWidgets.QLabel("")
        self.stats_label.setAlignment(QtCore.Qt.AlignCenter)
        self.stats_label.setStyleSheet("color: #555; margin: 10px;")

        logout_btn = QtWidgets.QPushButton("Logout")
        logout_btn.clicked.connect(self.handle_logout)
        logout_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; padding: 10px; border: none; border-radius: 4px; font-weight: bold; }")


        layout.addWidget(self.welcome_label)
        layout.addWidget(self.stats_label)
        layout.addStretch()
        layout.addWidget(logout_btn)

        w.setLayout(layout)
        return w
    
    def handle_login(self):
        """
        Handle login button click event.
        Validates input, attempts login, and updates UI on success or failure.
        """
        username = self.login_user.text().strip()
        password = self.login_pass.text()

        if not username or not password:
            self.status_label.setText("Please enter both username and password")
            return

        success, msg = self.user_manager.login(username, password)
        if success:
            self.current_user = username
            self.welcome_label.setText(f"Welcome back, {username}!")

            # Show user stats
            user_data = self.user_manager.users[username]
            total_sessions = user_data.get("total_sessions", 0)
            total_duration = user_data.get("total_duration_minutes", 0)
            first_session = user_data.get("first_session", "Never")

            if first_session != "Never" and first_session is not None and isinstance(first_session, str):
                try:
                    first_session = datetime.fromisoformat(first_session).strftime("%B %d, %Y")
                except (ValueError, TypeError):
                    first_session = "Invalid date"

            stats_text = f"Total Sessions: {total_sessions}\nTotal Recording Time: {total_duration:.1f} minutes\nMember Since: {first_session}"
            self.stats_label.setText(stats_text)

            self.stacked.setCurrentWidget(self.logged_in_widget)
            self.tab_buttons_widget.setVisible(False)
            self.status_label.setText("")
            print("user type:", user_data.get("account_type", "personal"))
            self.login_successful.emit(username, user_data.get("account_type", "personal"))

            # Clear login fields
            self.login_user.clear()
            self.login_pass.clear()
        else:
            self.status_label.setText(msg)
            self.status_label.setStyleSheet("color: red; font-weight: bold; margin: 10px;")
    
    def handle_signup(self):
        """
        Handle signup button click event.
        Validates input, attempts account creation, and updates UI on success or failure.
        """
        username = self.signup_user.text().strip()
        password = self.signup_pass.text()
        confirm = self.signup_confirm.text()
        
        # Get the selected account type
        if self.personal_radio.isChecked():
            account_type = "personal"
        elif self.advanced_radio.isChecked():
            account_type = "advanced"

        # Validation
        if not username or not password:
            self.status_label.setText("Please fill in all fields")
            self.status_label.setStyleSheet("color: red; font-weight: bold; margin: 10px;")
            return
            
        if password != confirm:
            self.status_label.setText("Passwords do not match")
            self.status_label.setStyleSheet("color: red; font-weight: bold; margin: 10px;")
            return
        
        success, msg = self.user_manager.signup(username, password, account_type)
        
        if success:
            self.status_label.setText("Account created! Please login.")
            self.status_label.setStyleSheet("color: green; font-weight: bold; margin: 10px;")
            # Clear signup fields and switch to login
            self.signup_user.clear()
            self.signup_pass.clear()
            self.signup_confirm.clear()
            # Reset to default selection
            self.personal_radio.setChecked(True)
            self.show_login()
        else:
            self.status_label.setText(msg)
            self.status_label.setStyleSheet("color: red; font-weight: bold; margin: 10px;")
        
    def handle_logout(self):
        """
        Handle logout button click event.
        Emits logout signal, resets user state, and updates UI.
        """
        self.logout_requested.emit()
        self.current_user = None
        self.stacked.setCurrentWidget(self.login_widget)
        self.tab_buttons_widget.setVisible(True)
        self.status_label.setText("Logged out successfully")
        self.status_label.setStyleSheet("color: blue; font-weight: bold; margin: 10px;")
        self.show_login()
    