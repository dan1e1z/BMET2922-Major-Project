"""
Pytest configuration and fixtures for GUI tests.

Author: Daniel Lindsay-Shad
Note: The Docstrings for methods were generated using Generative AI based on the method functionality.
"""

import pytest
import sys
import numpy as np
from pathlib import Path
from PyQt5 import QtWidgets, QtCore
from unittest.mock import Mock

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
    """Factory for creating mock UserManager instances."""
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

@pytest.fixture
def mock_user_manager_with_history(mock_user_manager_factory):
    """Create a mock UserManager with sample history data."""
    import datetime
    today = datetime.date.today()
    yesterday = (today - datetime.timedelta(days=1)).isoformat()
    two_days_ago = (today - datetime.timedelta(days=2)).isoformat()
    
    manager = mock_user_manager_factory()
    manager.users["testuser"]["history"] = [
        {
            "start": f"{yesterday}T10:00:00",
            "duration_minutes": 10,
            "avg_bpm": 75,
            "min_bpm": 60,
            "max_bpm": 90,
            "abnormal_low": 1,
            "abnormal_high": 2,
            "bpm_low_threshold": 60,
            "bpm_high_threshold": 100
        },
        {
            "start": f"{two_days_ago}T11:00:00",
            "duration_minutes": 15,
            "avg_bpm": 80,
            "min_bpm": 65,
            "max_bpm": 95,
            "abnormal_low": 0,
            "abnormal_high": 0,
            "bpm_low_threshold": 60,
            "bpm_high_threshold": 100
        }
    ]
    return manager


@pytest.fixture
def mock_user_manager_with_raw_ppg(mock_user_manager_factory):
    """Create a mock UserManager with raw PPG data for research tests."""
    import numpy as np
    manager = mock_user_manager_factory()
    manager.users["testuser"]["history"] = [
        {
            "start": "2023-01-01T10:00:00",
            "duration_minutes": 60,
            "raw_ppg": list(np.sin(np.linspace(0, 10 * np.pi, 3000)))
        }
    ]
    return manager