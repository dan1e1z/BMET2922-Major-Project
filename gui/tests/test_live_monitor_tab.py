
import pytest
from PyQt5 import QtCore
from unittest.mock import Mock
from gui.ui_tabs.live_monitor_tab import LiveMonitorTab

@pytest.fixture
def system_log():
    """Create a mock system log."""
    return Mock()

@pytest.fixture
def widget(qtbot, system_log, mocker):
    """Create an instance of the widget."""
    mocker.patch('gui.ui_tabs.live_monitor_tab.PlotNavigationMixin.setup_plot_navigation')
    mocker.patch('gui.ui_tabs.live_monitor_tab.pg.PlotWidget')
    mocker.patch('gui.ui_tabs.live_monitor_tab.SignalProcessingUtils')
    mocker.patch.object(LiveMonitorTab, 'setup_ui')
    widget = LiveMonitorTab(system_log)
    qtbot.addWidget(widget)
    # Override the plots with Mocks since patching might not work
    widget.bpm_plot = Mock()
    widget.raw_ppg_plot = Mock()
    widget.ibi_plot = Mock()
    widget.rr_plot = Mock()
    # Add curves
    widget.bpm_curve = Mock()
    widget.raw_ppg_curve = Mock()
    widget.ibi_curve = Mock()
    widget.rr_curve = Mock()
    widget.peak_scatter = Mock()
    widget.avg_bpm_line = Mock()
    # IBI and RR plots visibility
    widget._ibi_visible = False
    widget._rr_visible = False
    widget.ibi_plot.isVisible = lambda: widget._ibi_visible
    widget.ibi_plot.setVisible = lambda visible: setattr(widget, '_ibi_visible', visible)
    widget.rr_plot.isVisible = lambda: widget._rr_visible
    widget.rr_plot.setVisible = lambda visible: setattr(widget, '_rr_visible', visible)
    # Sliders and labels
    widget.low_slider = Mock()
    widget.low_slider.setValue = lambda v: setattr(widget, 'bpm_low', v)
    widget.low_slider.value = lambda: getattr(widget, 'bpm_low', 40)
    widget.high_slider = Mock()
    widget.high_slider.setValue = lambda v: setattr(widget, 'bpm_high', v)
    widget.high_slider.value = lambda: getattr(widget, 'bpm_high', 200)
    widget.low_label = Mock()
    widget.low_label.text = lambda: f"Low BPM Warning: {getattr(widget, 'bpm_low', 40)}"
    widget.high_label = Mock()
    widget.high_label.text = lambda: f"High BPM Warning: {getattr(widget, 'bpm_high', 200)}"
    # BPM display
    widget.bpm_display = Mock()
    widget.bpm_display.text = lambda: getattr(widget, 'bpm_display_text', '-- BPM')
    widget.bpm_display.setText = lambda v: setattr(widget, 'bpm_display_text', v)
    # Alarm widget
    widget.alarm_widget = Mock()
    widget.alarm_widget.text = lambda: getattr(widget, 'alarm_text', '')
    widget.alarm_widget.setText = lambda v: setattr(widget, 'alarm_text', v)
    widget.alarm_widget.setVisible = lambda v: None
    # Session data
    widget.session_bpm = []
    widget.session_raw_ppg = []
    # Timer
    widget.alarm_timer = Mock()
    widget.alarm_timer.start = lambda interval: None
    widget.alarm_timer.stop = lambda: None
    # Other required attributes
    widget.avg_bpm_display = Mock()
    widget.avg_bpm_display.setText = lambda v: None
    widget.session_start_time = None
    widget.current_user = None
    widget.bpm_low = 40
    widget.bpm_high = 200
    widget.alarm_active = False
    widget.alarm_visible = True
    # Plot navigation attributes
    widget.is_auto_scrolling = True
    widget.window_seconds = 10
    widget.plot_window_seconds = 10
    widget.plot_start_time = 0
    widget.slider = Mock()
    widget.slider.setRange = lambda min, max: None
    widget.slider.setValue = lambda v: None
    widget.slider.value = lambda: 0
    widget.slider.setMaximum = lambda v: None
    widget.slider.setMinimum = lambda v: None
    widget.plot_slider = widget.slider
    # More attributes for update_plots
    widget.time_bpm_data = []
    widget.visual_bpm_data = []
    widget.time_ppg_data = []
    widget.visual_ppg_data = []
    widget.ibi_times = []
    widget.ibi_data = []
    widget.rr_times = []
    widget.rr_data = []
    return widget

def test_initial_state(widget):
    """Test the initial state of the widget."""
    assert widget.current_user is None
    assert not widget.session_bpm
    assert widget.bpm_display.text() == "-- BPM"

def test_start_session(widget):
    """Test starting a new session."""
    widget.start_session("testuser")
    assert widget.current_user == "testuser"
    assert widget.session_start_time is not None

def test_new_data_received(widget):
    """Test processing a new data packet."""
    widget.start_session("testuser")
    packet = {"bpm": 75.0, "ppg_values": [1, 2, 3]}
    widget.new_data_received(packet)
    assert widget.current_bpm == 75.0
    assert widget.bpm_display.text() == "75.0 BPM"
    assert 75.0 in widget.session_bpm
    assert [1, 2, 3] == widget.session_raw_ppg

def test_check_bpm_alarm_high(widget):
    """Test the high BPM alarm."""
    widget.bpm_high = 100
    widget.current_bpm = 110
    alarm_msg = widget.check_bpm_alarm()
    assert widget.alarm_active
    assert "PULSE HIGH" in widget.alarm_widget.text()
    assert alarm_msg == "Pulse High"

def test_check_bpm_alarm_low(widget):
    """Test the low BPM alarm."""
    widget.bpm_low = 60
    widget.current_bpm = 50
    alarm_msg = widget.check_bpm_alarm()
    assert widget.alarm_active
    assert "PULSE LOW" in widget.alarm_widget.text()
    assert alarm_msg == "Pulse Low"

def test_update_thresholds(widget):
    """Test updating the BPM alarm thresholds."""
    widget.low_slider.setValue(50)
    widget.high_slider.setValue(150)
    widget.update_thresholds()
    assert widget.bpm_low == 50
    assert widget.bpm_high == 150
    assert "Low BPM Warning: 50" in widget.low_label.text()
    assert "High BPM Warning: 150" in widget.high_label.text()

def test_toggle_plots(widget):
    """Test toggling the visibility of the IBI and RR plots."""
    assert not widget.ibi_plot.isVisible()
    assert not widget.rr_plot.isVisible()
    widget.toggle_ibi_plot(QtCore.Qt.Checked)
    widget.toggle_rr_plot(QtCore.Qt.Checked)
    assert widget.ibi_plot.isVisible()
    assert widget.rr_plot.isVisible()
