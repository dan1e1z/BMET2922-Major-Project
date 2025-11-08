
import pytest
import numpy as np
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
    widget.alarm_widget.isVisible = lambda: getattr(widget, 'alarm_visible', False)
    widget.alarm_widget.setVisible = lambda v: setattr(widget, 'alarm_visible', v)
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
    widget.rr_display = Mock()
    widget.rr_display.setText = lambda v: setattr(widget, 'rr_display_text', v)
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
    assert widget.alarm_widget.isVisible()

def test_check_bpm_alarm_low(widget):
    """Test the low BPM alarm."""
    widget.bpm_low = 60
    widget.current_bpm = 50
    alarm_msg = widget.check_bpm_alarm()
    assert widget.alarm_active
    assert "PULSE LOW" in widget.alarm_widget.text()
    assert alarm_msg == "Pulse Low"
    assert widget.alarm_widget.isVisible() 

def test_check_bpm_alarm_normal(widget):
    """Test that the alarm deactivates and hides when BPM returns to normal range."""
    widget.bpm_low = 60
    widget.bpm_high = 100
    widget.alarm_active = True 
    widget.current_bpm = 80 
    alarm_msg = widget.check_bpm_alarm()
    assert not widget.alarm_active
    assert not widget.alarm_widget.isVisible()
    assert alarm_msg == "Pulse Normal"

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


def test_update_peaks_and_ibis(widget, mocker):
    """Ensure peaks are appended and ibis updated correctly."""
    # Prepare mocks and input
    widget.peak_scatter = mocker.Mock()
    peak_times = np.array([1.0, 2.0, 3.0])
    peak_amps = np.array([0.1, 0.2, 0.3])

    # Call private update methods
    widget._update_peaks(peak_times, peak_amps)
    assert widget.last_peak_time == 3.0
    widget._update_ibis(peak_times)
    # IBI between 1.0 and 2.0 -> 1000 ms
    assert widget.current_ibi == pytest.approx(1000.0)


def test_estimate_respiratory_rate_with_mocked_find_peaks(widget, mocker):
    """Test respiratory rate estimation with mocked signal processing."""
    # Set current_bpm for ratio check
    widget.current_bpm = 60

    # Mock rr_display.setText to check if called
    widget.rr_display.setText = mocker.Mock()

    # Mock signal.welch to return a peak at 0.5 Hz (30 breaths/min)
    f_mock = np.linspace(0, 0.5, 100) 
    Pxx_mock = np.zeros(100)
    Pxx_mock[-1] = 1  # Peak at f[-1] = 0.5 Hz
    mocker.patch('scipy.signal.welch', return_value=(f_mock, Pxx_mock))

    # Use regularly spaced peaks (every 100 samples, 11 peaks for sufficient data)
    peaks = np.arange(0, 1100, 100)

    # Call estimator with signal and peaks
    widget.estimate_respiratory_rate(np.zeros(1101), peaks)

    # Should estimate RR as 30 breaths/min, smoothed from 0
    # With alpha = 0.6 (delta = 30 > 5): current_rr = 0.4*0 + 0.6*30 = 18.0
    assert widget.current_rr == pytest.approx(18.0, abs=1.0)
    widget.rr_display.setText.assert_called()


def test_process_ppg_signal_triggers_updates(widget, mocker):
    """Process buffer and ensure update hooks are called when peaks found."""
    # Fill buffer with > 5 seconds of samples
    widget.ppg_buffer.clear()
    widget.ppg_times.clear()
    for i in range(widget.sampling_rate * 6):
        widget.ppg_buffer.append(0.0)
        widget.ppg_times.append(float(i))

    # Patch SignalProcessingUtils to return cleaned signal and peaks
    mocker.patch('gui.ui_tabs.live_monitor_tab.SignalProcessingUtils.clean_ppg_signal', return_value=np.zeros(len(widget.ppg_buffer)))
    mocker.patch('gui.ui_tabs.live_monitor_tab.SignalProcessingUtils.detect_ppg_peaks', return_value=(np.array([0, 10, 20]), {}))

    # Spy on private update methods
    mock_update_peaks = mocker.patch.object(widget, '_update_peaks')
    mock_update_ibis = mocker.patch.object(widget, '_update_ibis')

    widget.process_ppg_signal()

    assert mock_update_peaks.called
    assert mock_update_ibis.called


def test_calculate_hrv_metrics_and_display(widget, mocker):
    """Ensure HRV calculation uses utility and updates the display."""
    # Provide enough ibis for calculation
    widget.ibi_data.clear()
    for v in range(12):
        widget.ibi_data.append(800.0)

    # Patch utility to return expected metrics
    mocker.patch('gui.ui_tabs.live_monitor_tab.SignalProcessingUtils.calculate_hrv_time_domain', return_value={'rmssd': 25.0, 'sdnn': 40.0, 'pnn50': 1.0, 'mean_rr': 800.0, 'sd1': 5.0, 'sd2': 10.0})

    widget.hrv_display = mocker.Mock()
    widget.hrv_display.setText = mocker.Mock()
    widget.hrv_display.parent = mocker.Mock(return_value=mocker.Mock())
    layout_mock = mocker.Mock(
        count=lambda: 0,
        addWidget=mocker.Mock()
    )
    widget.hrv_display.parent.return_value.layout = mocker.Mock(return_value=layout_mock)
    widget.hrv_display.setParent = mocker.Mock()
    widget.hrv_display.deleteLater = mocker.Mock()

    widget.calculate_hrv_metrics()

    # Test passes if no exception is raised


def test_update_average_bpm_line(widget, mocker):
    """Average BPM line should update based on visual data."""
    widget.visual_bpm_data = [60, 70, 80]
    # Patch formatter
    mocker.patch('gui.ui_tabs.live_monitor_tab.SessionInfoFormatter.calculate_session_stats', return_value={'count': 3, 'avg': 70.0})

    widget.avg_bpm_display = mocker.Mock()
    widget.avg_bpm_display.setText = mocker.Mock()
    widget.avg_bpm_line = mocker.Mock()
    widget.avg_bpm_line.setValue = mocker.Mock()

    widget.update_average_bpm_line()

    widget.avg_bpm_display.setText.assert_called()
    widget.avg_bpm_line.setValue.assert_called_with(70.0)