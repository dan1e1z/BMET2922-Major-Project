
import pytest
from gui.ui_components.bluetooth_connection_status import BluetoothConnectionStatus

@pytest.fixture
def widget(qtbot):
    """Create an instance of the widget."""
    widget = BluetoothConnectionStatus()
    qtbot.addWidget(widget)
    return widget

def test_initial_state(widget):
    """Test the initial state of the widget."""
    assert widget.status_text.text() == "Disconnected"
    assert "color: red" in widget.status_icon.styleSheet()
    assert not widget.timeout_alarm.isVisible()

def test_update_status_connected(widget):
    """Test updating the status to connected."""
    widget.update_status(True, "Connected")
    assert widget.status_text.text() == "Connected"
    assert "color: green" in widget.status_icon.styleSheet()
    assert not widget.timeout_alarm.isVisible()

def test_update_status_disconnected(widget):
    """Test updating the status to disconnected."""
    # connected status
    widget.update_status(True, "Connected")
    # disconnected status
    widget.update_status(False, "Disconnected")
    assert widget.status_text.text() == "Disconnected"
    assert "color: red" in widget.status_icon.styleSheet()

def test_update_mode_adaptive(widget):
    """Test updating the mode to Adaptive."""
    widget.update_mode(0)
    assert widget.mode_indicator.text() == "Adaptive"

def test_update_mode_z_score(widget):
    """Test updating the mode to Z-score."""
    widget.update_mode(1)
    assert widget.mode_indicator.text() == "Z-score"

def test_show_timeout_alarm(widget):
    """Test showing the timeout alarm."""
    widget.show_timeout_alarm()
    assert widget.timeout_alarm.isVisible()
    assert "WARNING" in widget.timeout_alarm.text()

def test_hide_timeout_alarm(widget):
    """Test hiding the timeout alarm."""
    widget.show_timeout_alarm()
    widget.hide_timeout_alarm()
    assert not widget.timeout_alarm.isVisible()
