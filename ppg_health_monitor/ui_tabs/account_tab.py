from PyQt5 import QtWidgets, QtCore
from datetime import datetime
class AccountTab(QtWidgets.QWidget):
    login_successful = QtCore.pyqtSignal(str)
    logout_requested = QtCore.pyqtSignal()

    def __init__(self, user_manager):
        super().__init__()
        self.user_manager = user_manager
        self.current_user = None
        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout()

        # Title
        title = QtWidgets.QLabel("Account Management")
        title.setAlignment(QtCore.Qt.AlignCenter)

        self.stacked = QtWidgets.QStackedWidget()
        self.login_widget = self.create_login_form()
        self.signup_widget = self.create_signup_form()
        self.logged_in_widget = self.create_logged_in_widget()
        
        self.stacked.addWidget(self.login_widget)
        self.stacked.addWidget(self.signup_widget)
        self.stacked.addWidget(self.logged_in_widget)
        layout.addWidget(self.stacked)

        # Tab buttons (only show when not logged in)
        self.tab_buttons_widget = QtWidgets.QWidget()
        btn_layout = QtWidgets.QHBoxLayout()
        self.login_tab_btn = QtWidgets.QPushButton("Login")
        self.signup_tab_btn = QtWidgets.QPushButton("Sign Up")

        self.login_tab_btn.clicked.connect(self.show_login)
        self.signup_tab_btn.clicked.connect(self.show_signup)
        
        btn_layout.addWidget(self.login_tab_btn)
        btn_layout.addWidget(self.signup_tab_btn)
        self.tab_buttons_widget.setLayout(btn_layout)
        layout.addWidget(self.tab_buttons_widget)

        self.status_label = QtWidgets.QLabel("")
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        self.show_login()

    def show_login(self):
        self.stacked.setCurrentWidget(self.login_widget)
        self.login_tab_btn.setEnabled(False)
        self.signup_tab_btn.setEnabled(True)
    
    def show_signup(self):
        self.stacked.setCurrentWidget(self.signup_widget)
        self.login_tab_btn.setEnabled(True)
        self.signup_tab_btn.setEnabled(False)

    def create_login_form(self):
        w = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout()
        layout.setSpacing(15)
        
        self.login_user = QtWidgets.QLineEdit()
        self.login_pass = QtWidgets.QLineEdit()
        self.login_pass.setEchoMode(QtWidgets.QLineEdit.Password)
        
        btn = QtWidgets.QPushButton("Login")
        btn.clicked.connect(self.handle_login)
        
        layout.addRow("Username:", self.login_user)
        layout.addRow("Password:", self.login_pass)
        layout.addRow("", btn)
        
        w.setLayout(layout)
        return w
    
    def create_signup_form(self):
        w = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout()
        layout.setSpacing(15)
        
        self.signup_user = QtWidgets.QLineEdit()
        self.signup_pass = QtWidgets.QLineEdit()
        self.signup_pass.setEchoMode(QtWidgets.QLineEdit.Password)
        self.signup_confirm = QtWidgets.QLineEdit()
        self.signup_confirm.setEchoMode(QtWidgets.QLineEdit.Password)
        
        btn = QtWidgets.QPushButton("Sign Up")
        btn.clicked.connect(self.handle_signup)
        
        layout.addRow("Username:", self.signup_user)
        layout.addRow("Password:", self.signup_pass)
        layout.addRow("Confirm Password:", self.signup_confirm)
        layout.addRow("", btn)
        
        w.setLayout(layout)
        return w
    
    def create_logged_in_widget(self):
        w = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(20)
        
        self.welcome_label = QtWidgets.QLabel("")
        self.welcome_label.setAlignment(QtCore.Qt.AlignCenter)
        
        # User stats
        self.stats_label = QtWidgets.QLabel("")
        self.stats_label.setAlignment(QtCore.Qt.AlignCenter)
        
        logout_btn = QtWidgets.QPushButton("Logout")
        logout_btn.clicked.connect(self.handle_logout)
        
        layout.addWidget(self.welcome_label)
        layout.addWidget(self.stats_label)
        layout.addStretch()
        layout.addWidget(logout_btn)
        
        w.setLayout(layout)
        return w
    
    def handle_login(self):
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
            self.login_successful.emit(username)
            
            # Clear login fields
            self.login_user.clear()
            self.login_pass.clear()
        else:
            self.status_label.setText(msg)
    
    def handle_signup(self):
        username = self.signup_user.text().strip()
        password = self.signup_pass.text()
        confirm = self.signup_confirm.text()
        
        if not username or not password:
            self.status_label.setText("Please fill in all fields")
            return
        
        if password != confirm:
            self.status_label.setText("Passwords do not match")
            return
        
        success, msg = self.user_manager.signup(username, password)
        if success:
            self.status_label.setText("Account created! Please login.")
            
            # Clear signup fields and switch to login
            self.signup_user.clear()
            self.signup_pass.clear()
            self.signup_confirm.clear()
            self.show_login()
        else:
            self.status_label.setText(msg)
    
    def handle_logout(self):
        self.logout_requested.emit()
        self.current_user = None
        self.stacked.setCurrentWidget(self.login_widget)
        self.tab_buttons_widget.setVisible(True)
        self.status_label.setText("Logged out successfully")
        self.show_login()
    