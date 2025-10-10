import pytest
from unittest.mock import Mock
from gui.ui_tabs.account_tab import AccountTab

@pytest.fixture
def user_manager():
    """Create a mock user manager."""
    manager = Mock()
    manager.login.return_value = (True, "Login successful")
    manager.signup.return_value = (True, "Account created successfully")
    manager.users = {
        "testuser": {
            "account_type": "personal",
            "total_sessions": 5,
            "total_duration_minutes": 120,
            "first_session": "2023-01-01T12:00:00"
        }
    }
    return manager

@pytest.fixture
def widget(qtbot, user_manager):
    """Create an instance of the widget."""
    widget = AccountTab(user_manager)
    qtbot.addWidget(widget)
    return widget

def test_initial_state(widget):
    """Test the initial state of the widget."""
    assert widget.stacked.currentWidget() == widget.login_widget
    assert not widget.login_tab_btn.isEnabled()
    assert widget.signup_tab_btn.isEnabled()

def test_show_signup(widget):
    """Test switching to the signup form."""
    widget.show_signup()
    assert widget.stacked.currentWidget() == widget.signup_widget
    assert widget.login_tab_btn.isEnabled()
    assert not widget.signup_tab_btn.isEnabled()

def test_handle_login_success(widget, user_manager):
    """Test a successful login."""
    widget.login_user.setText("testuser")
    widget.login_pass.setText("password")
    widget.handle_login()
    user_manager.login.assert_called_once_with("testuser", "password")
    assert widget.stacked.currentWidget() == widget.logged_in_widget
    assert "Welcome back, testuser!" in widget.welcome_label.text()

def test_handle_login_failure(widget, user_manager):
    """Test a failed login."""
    user_manager.login.return_value = (False, "Invalid password")
    widget.login_user.setText("testuser")
    widget.login_pass.setText("wrongpassword")
    widget.handle_login()
    assert widget.stacked.currentWidget() == widget.login_widget
    assert "Invalid password" in widget.status_label.text()

def test_handle_signup_success(widget, user_manager):
    """Test a successful signup."""
    widget.signup_user.setText("newuser")
    widget.signup_pass.setText("newpassword")
    widget.signup_confirm.setText("newpassword")
    widget.handle_signup()
    user_manager.signup.assert_called_once_with("newuser", "newpassword", "personal")
    assert widget.stacked.currentWidget() == widget.login_widget
    assert "Account created!" in widget.status_label.text()

def test_handle_signup_password_mismatch(widget, user_manager):
    """Test a signup with mismatched passwords."""
    widget.signup_user.setText("newuser")
    widget.signup_pass.setText("newpassword")
    widget.signup_confirm.setText("mismatch")
    widget.handle_signup()
    assert user_manager.signup.call_count == 0
    assert "Passwords do not match" in widget.status_label.text()

def test_handle_logout(widget):
    """Test the logout process."""

    # login
    widget.login_user.setText("testuser")
    widget.login_pass.setText("password")
    widget.handle_login()
    
    # logout
    widget.handle_logout()
    assert widget.stacked.currentWidget() == widget.login_widget
    assert "Logged out successfully" in widget.status_label.text()