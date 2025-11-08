"""
Test module for MainWindow.

Author: Daniel Lindsay-Shad
Note: The Docstrings for methods were generated using Generative AI based on the method functionality.
"""

import pytest
from unittest.mock import Mock
from datetime import datetime
import time
from PyQt5 import QtWidgets
from gui.core.main_window import MainWindow


@pytest.fixture
def main_window(qtbot, mocker):
    # Patch heavy components to keep test lightweight
    mocker.patch('gui.core.main_window.BluetoothMonitor')
    mocker.patch('gui.core.main_window.UserManager')
    mock_thread = mocker.patch('gui.core.main_window.QtCore.QThread')
    mock_thread.return_value.start = Mock()
    mock_thread.return_value.quit = Mock()
    mock_thread.return_value.wait = Mock()

    w = MainWindow()
    qtbot.addWidget(w)

    # Replace components with mocks for controllable behaviour
    w.system_log = Mock()
    w.system_log.add_log_entry = Mock()

    w.connection_status = Mock()
    w.connection_status.update_status = Mock()
    w.connection_status.show_timeout_alarm = Mock()
    w.connection_status.update_mode = Mock()

    w.user_manager = Mock()
    w.user_manager.save_session = Mock()

    live_tab = Mock()
    live_tab.session_bpm = []
    live_tab.session_raw_ppg = []
    live_tab.bpm_low = 60
    live_tab.bpm_high = 100
    live_tab.start_session = Mock()
    live_tab.new_data_received = Mock(return_value=None)
    live_tab.bpm_display = Mock()
    live_tab.bpm_display.setText = Mock()
    w.live_monitor_tab = live_tab

    history_tab = Mock()
    history_tab.start_session = Mock()
    history_tab.update_history_view = Mock()
    w.history_tab = history_tab

    research_tab = Mock()
    research_tab.start_session = Mock()
    w.research_tab = research_tab

    w.bluetooth_monitor = Mock()
    w.bluetooth_monitor.running = True
    w.bluetooth_monitor_thread = mock_thread.return_value

    return w


def test_login_and_logout_flow(main_window):
    main_window.handle_login('alice', 'personal')
    assert main_window.current_user == 'alice'
    assert main_window.tabs.isTabEnabled(2)

    # simulate incoming packet and ensure expected_sequence increments
    pkt = {'sequence': 0, 'ppg_values': tuple(range(50)), 'bpm': 70.0}
    main_window.live_monitor_tab.new_data_received = Mock(return_value=None)
    main_window.handle_new_packet(pkt)
    assert main_window.expected_sequence == 1

    # logout should reset state
    main_window.user_manager.save_session = Mock()
    main_window.handle_logout()
    assert main_window.current_user is None
    assert not main_window.tabs.isTabEnabled(2)


def test_save_current_session_computes_stats(main_window, mocker):
    main_window.current_user = 'bob'
    main_window.session_start_time = datetime.now()
    main_window.live_monitor_tab.session_bpm = [60, 80, 100]
    main_window.live_monitor_tab.session_raw_ppg = []
    main_window.live_monitor_tab.bpm_low = 65
    main_window.live_monitor_tab.bpm_high = 95
    main_window.user_manager.save_session = Mock()

    main_window.save_current_session()
    call_args = main_window.user_manager.save_session.call_args[0]
    assert call_args[0] == 'bob'
    sd = call_args[1]
    assert sd['avg_bpm'] == pytest.approx(80.0)


def test_handle_login_enables_tabs_and_starts_sessions(main_window):
    main_window.handle_login('eve', 'advanced')

    assert main_window.current_user == 'eve'
    assert main_window.tabs.isTabEnabled(2)
    assert main_window.tabs.isTabEnabled(3)
    main_window.live_monitor_tab.start_session.assert_called_once_with('eve')
    main_window.research_tab.start_session.assert_called_once_with('eve', main_window.user_manager)
    main_window.history_tab.start_session.assert_called_once_with('eve', main_window.user_manager)


def test_handle_logout_resets_state(main_window):
    main_window.current_user = 'sam'
    main_window.live_monitor_tab.session_bpm = [60]
    main_window.session_start_time = datetime.now()
    main_window.live_monitor_tab.current_user = 'sam'
    main_window.live_monitor_tab.session_start_time = datetime.now()
    main_window.handle_logout()

    assert main_window.current_user is None
    assert not main_window.tabs.isTabEnabled(2)
    assert not main_window.tabs.isTabEnabled(3)
    assert main_window.live_monitor_tab.session_bpm == []
    assert main_window.live_monitor_tab.current_user is None


def test_handle_new_packet_sequence_and_status(main_window):
    main_window.current_user = 'lee'
    main_window.session_start_time = datetime.now()
    main_window.expected_sequence = 2
    packet = {'sequence': 4, 'bpm': 72.3, 'ppg_values': tuple(range(50)), 'mode': 1}

    main_window.handle_new_packet(packet)

    # Sequence mismatch logged and expected sequence updated
    assert main_window.expected_sequence == 5
    main_window.system_log.add_log_entry.assert_any_call('Packet sequence mismatch: expected 2, got 4')

    assert '72.3' in main_window.status_bar.text()
    main_window.connection_status.update_mode.assert_called_once_with(1)


def test_handle_connection_status_and_timeout(main_window):
    main_window.handle_connection_status(True, 'Connected')
    main_window.connection_status.update_status.assert_called_once_with(True, 'Connected')

    main_window.handle_connection_timeout()
    main_window.connection_status.show_timeout_alarm.assert_called_once()
    main_window.system_log.add_log_entry.assert_called_with('No data received for 5+ seconds - Check sensor power')


def test_close_window_saves_and_stops_thread(main_window, mocker):
    main_window.current_user = 'zoe'
    main_window.live_monitor_tab.session_bpm = [70]
    main_window.save_current_session = Mock()

    mock_quit = mocker.patch('gui.core.main_window.QtWidgets.QApplication.quit')
    main_window.close_window()

    main_window.save_current_session.assert_called_once()
    main_window.system_log.add_log_entry.assert_any_call('Application closing')
    assert main_window.bluetooth_monitor.running is False
    main_window.bluetooth_monitor_thread.quit.assert_called_once()
    main_window.bluetooth_monitor_thread.wait.assert_called_once()
    mock_quit.assert_called_once()


def test_display_latency_requirement(main_window, mocker):
    """Requirement 12: Test that display updates occur within 2 seconds of GUI receiving data."""
    import time

    # Set up user session
    main_window.handle_login('testuser', 'personal')
    main_window.session_start_time = datetime.now()

    # Track when display methods are called
    display_call_times = []

    def track_display_call(*args, **kwargs):
        # high-precision timestamp recorder (microsecond/nanosecond precision)
        display_call_times.append(time.perf_counter())

    # Creates a Timestamp of when display methods are called
    mocker.patch.object(main_window.live_monitor_tab.bpm_display, 'setText', side_effect=track_display_call)
    mocker.patch.object(main_window.live_monitor_tab.bpm_curve, 'setData', side_effect=track_display_call)
    mocker.patch.object(main_window.live_monitor_tab.raw_ppg_curve, 'setData', side_effect=track_display_call)

    # Mock new_data_received to simulate display updates
    def mock_new_data_received(packet):
        bpm = packet.get('bpm', 0)
        if bpm > 0:
            main_window.live_monitor_tab.bpm_display.setText(f"{bpm:.1f} BPM")
            main_window.live_monitor_tab.bpm_curve.setData([1, 2, 3], [60, 70, bpm])
            main_window.live_monitor_tab.raw_ppg_curve.setData([1, 2, 3], packet['ppg_values'][:3])
        return None

    main_window.live_monitor_tab.new_data_received = Mock(side_effect=mock_new_data_received)

    # Test latency 10 times to ensure consistent performance
    for i in range(10):
        display_call_times.clear()

        # Create a packet simulating microcontroller data capture
        packet = {'sequence': i, 'ppg_values': tuple(range(50)), 'bpm': 75.0 + i * 0.1, 'mode': 0}

        # Record the time when GUI receives the data (handle_new_packet called)
        data_received_time = time.perf_counter()

        # Process the packet
        main_window.handle_new_packet(packet)

        # Verify display methods were called
        assert len(display_call_times) > 0, f"Iteration {i+1}: No display updates occurred"

        # time between data received via packet and time when display updates
        latency = display_call_times[0] - data_received_time

        # Check that latency is < 2 seconds for each of the 10 iterations
        assert latency < 2.0, f"Iteration {i+1}: Display latency {latency:.6f}s exceeds 2.0s requirement"