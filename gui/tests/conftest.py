import pytest
import sys
import numpy as np
from pathlib import Path
from PyQt5 import QtWidgets, QtCore
from unittest.mock import Mock

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

@pytest.fixture(scope="session")
def qapp():
    """Create QApplication for PyQt5 tests (session-scoped for efficiency)."""
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    yield app
    app.quit()

@pytest.fixture
def qtbot(qapp, request):
    """Provide a simple qtbot for widget testing."""
    class QtBot:
        def __init__(self, app):
            self.app = app
            self.widgets = []
        
        def addWidget(self, widget):
            self.widgets.append(widget)
            widget.show()
            return widget
        
        def wait(self, ms):
            QtCore.QThread.msleep(ms)
    
    bot = QtBot(qapp)
    
    def cleanup():
        for widget in bot.widgets:
            widget.close()
            widget.deleteLater()
    
    request.addfinalizer(cleanup)
    return bot

# Shared fixtures that can be reused across tests
@pytest.fixture
def sample_ppg_signal():
    """Generate a sample PPG signal for testing."""
    t = np.linspace(0, 10, 500)
    signal = np.sin(2 * np.pi * 1.2 * t) + 0.1 * np.random.randn(500)
    return signal

@pytest.fixture
def sample_session_data():
    """Generate sample session data."""
    return {
        "start": "2025-01-15T10:30:00",
        "end": "2025-01-15T10:40:00",
        "duration_minutes": 10.0,
        "avg_bpm": 75.5,
        "min_bpm": 60.0,
        "max_bpm": 90.0,
        "total_samples": 100,
        "abnormal_low": 5,
        "abnormal_high": 8,
        "bpm_low_threshold": 50,
        "bpm_high_threshold": 120,
        "raw_ppg": list(range(100))
    }

@pytest.fixture(scope="session")
def mock_user_manager_factory():
    """Factory for creating mock UserManager instances (session-scoped to avoid recreation)."""
    def _create_manager(users=None):
        manager = Mock()
        manager.users = users or {
            "testuser": {
                "password": "password123",
                "account_type": "personal",
                "history": [],
                "total_sessions": 0,
                "total_duration_minutes": 0,
                "first_session": None
            }
        }
        manager.login = Mock(return_value=(True, "Login successful"))
        manager.signup = Mock(return_value=(True, "Account created successfully"))
        manager.save_session = Mock()
        return manager
    return _create_manager

@pytest.fixture
def mock_user_manager(mock_user_manager_factory):
    """Create a standard mock UserManager for tests."""
    return mock_user_manager_factory()