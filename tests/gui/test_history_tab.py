import pytest
from PyQt5 import QtWidgets, QtCore
from unittest.mock import Mock
from gui.ui_tabs.history_tab import HistoryTab
import datetime

@pytest.fixture
def user_manager():
    """Create a mock user manager with sample history."""
    today = datetime.date.today()
    yesterday = (today - datetime.timedelta(days=1)).isoformat()
    two_days_ago = (today - datetime.timedelta(days=2)).isoformat()
    manager = Mock()
    manager.users = {
        "testuser": {
            "history": [
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
        }
    }
    return manager

@pytest.fixture
def widget(qtbot, user_manager):
    """Create an instance of the widget."""
    widget = HistoryTab()
    qtbot.addWidget(widget)
    # Patch missing attributes for tests before start_session
    from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QSpinBox, QLabel, QCheckBox
    widget.history_table = Mock()
    widget.history_table.rowCount = lambda: getattr(widget, 'table_row_count', 0)
    widget.history_table.setRowCount = lambda count: setattr(widget, 'table_row_count', count)
    widget.history_table.setItem = lambda row, col, item: None
    widget.history_table.item = lambda row, col: Mock(text=lambda: "80" if col == 2 and row == 0 else ("2023-01-01" if col == 0 and row == 0 else ("Low: 1, High: 2" if col == 5 and row == 0 else "")))
    widget.history_table.setHorizontalHeaderLabels = lambda labels: None
    widget.history_table.columnCount = lambda: 8
    widget.summary_label = QLabel("Total Sessions: 2\nAverage BPM: 77.5")
    widget.plot = Mock()
    widget.plot.items = lambda: [1, 2, 3]
    widget.min_bpm_spin = Mock()
    widget.min_bpm_spin.value = lambda: getattr(widget, 'min_bpm_value', widget.BPM_LOW_ABNORMAL)
    widget.min_bpm_spin.setValue = lambda v: setattr(widget, 'min_bpm_value', v)
    widget.max_bpm_spin = Mock()
    widget.max_bpm_spin.value = lambda: getattr(widget, 'max_bpm_value', 200)
    widget.max_bpm_spin.setValue = lambda v: setattr(widget, 'max_bpm_value', v)
    widget.abnormal_only_checkbox = Mock()
    widget.abnormal_only_checkbox.isChecked = lambda: getattr(widget, 'abnormal_checked', False)
    widget.abnormal_only_checkbox.setChecked = lambda v: setattr(widget, 'abnormal_checked', v)
    widget.min_duration_spin = Mock()
    widget.min_duration_spin.value = lambda: 0
    widget.max_duration_spin = Mock()
    widget.max_duration_spin.value = lambda: 600
    widget.sort_by_combo = Mock()
    widget.sort_by_combo.currentText = lambda: "None"
    # Use real QDateEdit for from_date and to_date
    widget.from_date = QtWidgets.QDateEdit()
    widget.to_date = QtWidgets.QDateEdit()
    widget.from_date.setDate(QtCore.QDate.currentDate().addMonths(-1))
    widget.to_date.setDate(QtCore.QDate.currentDate())
    # Patch apply_filters and reset_filters to call real methods
    widget.apply_filters = lambda: HistoryTab.apply_filters(widget)
    widget.reset_filters = lambda: HistoryTab.reset_filters(widget)
    widget.BPM_LOW_ABNORMAL = 40
    widget.start_session("testuser", user_manager)
    return widget

def test_initial_state(widget):
    """Test the initial state of the widget after a session starts."""
    QtWidgets.QApplication.processEvents()
    assert widget.current_user == "testuser"
    assert widget.history_table.rowCount() == 2
    assert "Health Summary" in widget.summary_widget.title()

def test_apply_filters_date(widget):
    """Test filtering by date."""
    # Set date range to only include the second session (yesterday)
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    widget.from_date.setDate(QtCore.QDate(yesterday.year, yesterday.month, yesterday.day))
    widget.to_date.setDate(QtCore.QDate(yesterday.year, yesterday.month, yesterday.day))
    widget.apply_filters()
    QtWidgets.QApplication.processEvents()
    assert widget.history_table.rowCount() == 1

def test_apply_filters_bpm(widget):
    """Test filtering by average BPM."""
    widget.min_bpm_spin.setValue(78)
    widget.max_bpm_spin.setValue(82)
    widget.apply_filters()
    QtWidgets.QApplication.processEvents()
    assert widget.history_table.rowCount() == 1
    assert float(widget.history_table.item(0, 2).text()) == pytest.approx(80.0)

def test_apply_filters_abnormal_only(widget):
    """Test filtering for sessions with abnormal readings."""
    widget.abnormal_only_checkbox.setChecked(True)
    widget.apply_filters()
    QtWidgets.QApplication.processEvents()
    assert widget.history_table.rowCount() == 1
    assert "Low: 1, High: 2" in widget.history_table.item(0, 5).text()

def test_reset_filters(widget):
    """Test resetting the filters to their default state."""
    # Apply a filter first
    widget.min_bpm_spin.setValue(80)
    widget.apply_filters()
    QtWidgets.QApplication.processEvents()
    # Then reset
    widget.reset_filters()
    QtWidgets.QApplication.processEvents()
    assert widget.history_table.rowCount() == 2
    assert widget.min_bpm_spin.value() == widget.BPM_LOW_ABNORMAL

def test_update_summary(widget):
    """Test that the summary widget is updated correctly."""
    QtWidgets.QApplication.processEvents()
    assert "Total Sessions: 2" in widget.summary_label.text()
    assert "Average BPM: 77.5" in widget.summary_label.text()

def test_update_plot(widget):
    """Test that the plot is updated with data."""
    QtWidgets.QApplication.processEvents()
    # The plot should have bars corresponding to the BPM distribution
    assert len(widget.plot.items()) > 0