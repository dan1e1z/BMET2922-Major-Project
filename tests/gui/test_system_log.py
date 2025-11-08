import pytest
import re
from datetime import datetime
from gui.ui_components.system_log import SystemLog

@pytest.fixture
def widget(qtbot):
    """Create an instance of the widget."""
    widget = SystemLog()
    qtbot.addWidget(widget)
    return widget

def test_initial_state(widget):
    """Test the initial state of the widget."""
    assert widget.log_text.toPlainText() == ""

def test_add_log_entry(widget):
    """Test adding a log entry."""
    widget.add_log_entry("Test message")
    assert "Test message" in widget.log_text.toPlainText()

def test_clear_log(widget):
    """Test clearing the log."""
    widget.add_log_entry("Test message")
    widget.clear_log()
    assert widget.log_text.toPlainText() == ""

def test_add_multiple_log_entries(widget):
    """Test adding multiple log entries."""
    widget.add_log_entry("Message 1")
    widget.add_log_entry("Message 2")
    log_content = widget.log_text.toPlainText()
    assert "Message 1" in log_content
    assert "Message 2" in log_content

def test_log_entry_format(widget):
    """Requirement 13: Test that log entries follow the format:
    'Day Mon DD HH:MM:SS YYYY: message'."""
    widget.add_log_entry("Test message")
    log_content = widget.log_text.toPlainText()
    
    parts = log_content.split(': ', 1)
    assert len(parts) == 2, f"Log entry must contain ': ' separator: {log_content}"
    
    timestamp_str, message = parts
    assert message == "Test message", f"Message mismatch: {message}"
    
    try:
        datetime.strptime(timestamp_str, "%a %b %d %H:%M:%S %Y")
    except ValueError as e:
        pytest.fail(
            f"Timestamp '{timestamp_str}' does not match format "
            f"'Day Mon DD HH:MM:SS YYYY': {e}"
        )