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

@pytest.mark.parametrize("connected,status_text,expected_color", [
    (True, "Connected", "green"),
    (False, "Disconnected", "red"),
])
def test_update_status(widget, connected, status_text, expected_color):
    """Test updating connection status."""
    widget.update_status(connected, status_text)
    assert widget.status_text.text() == status_text
    assert f"color: {expected_color}" in widget.status_icon.styleSheet()

@pytest.mark.parametrize("mode_index,expected_text", [
    (0, "Adaptive"),
    (1, "Z-score"),
])
def test_update_mode(widget, mode_index, expected_text):
    """Test updating the mode indicator."""
    widget.update_mode(mode_index)
    assert widget.mode_indicator.text() == expected_text

def test_timeout_alarm_visibility(widget):
    """Test showing and hiding the timeout alarm."""
    widget.show_timeout_alarm()
    assert widget.timeout_alarm.isVisible()
    assert "WARNING" in widget.timeout_alarm.text()
    
    widget.hide_timeout_alarm()
    assert not widget.timeout_alarm.isVisible()