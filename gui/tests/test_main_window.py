import pytest
from unittest.mock import Mock
from datetime import datetime
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