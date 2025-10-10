import pytest
from unittest.mock import Mock
from datetime import datetime
from PyQt5 import QtWidgets
from gui.core.main_window import MainWindow

@pytest.fixture
def mock_bluetooth_monitor(mocker):
    """Create a mock BluetoothMonitor."""
    mock = mocker.patch('gui.core.main_window.BluetoothMonitor')
    monitor = Mock()
    monitor.packet_received = Mock()
    monitor.connection_status_changed = Mock()
    monitor.connection_timeout = Mock()
    monitor.running = True
    mock.return_value = monitor
    return monitor


@pytest.fixture
def mock_user_manager(mocker):
    """Create a mock UserManager."""
    mock = mocker.patch('gui.core.main_window.UserManager')
    manager = Mock()
    manager.users = {}
    mock.return_value = manager
    return manager


@pytest.fixture
def main_window(qtbot, mocker):
    """Create MainWindow instance for testing."""
    # FIXED: Removed the patch for QtCore.QThread to prevent the test from hanging.
    mocker.patch('gui.core.main_window.BluetoothMonitor')
    mocker.patch('gui.core.main_window.UserManager')
    mock_thread = mocker.patch('gui.core.main_window.QtCore.QThread')
    
    # Mock the thread methods
    mock_thread_instance = Mock()
    mock_thread.return_value = mock_thread_instance
    mock_thread_instance.start = Mock()
    mock_thread_instance.quit = Mock()
    mock_thread_instance.wait = Mock()
    
    window = MainWindow()
    qtbot.addWidget(window)
    
    return window


class TestMainWindowInit:
    """Test MainWindow initialization."""
    
    def test_init_creates_window(self, main_window):
        assert main_window is not None
        assert main_window.windowTitle() == "PPG Health Monitor"
    
    def test_init_creates_user_manager(self, main_window):
        assert hasattr(main_window, 'user_manager')
        assert main_window.user_manager is not None
    
    def test_init_session_variables(self, main_window):
        assert main_window.current_user is None
        assert main_window.session_start_time is None
        assert main_window.packet_sequence == 0
        assert main_window.expected_sequence == 0
    
    def test_init_creates_system_log(self, main_window):
        assert hasattr(main_window, 'system_log')
        assert main_window.system_log is not None
    
    def test_init_creates_connection_status(self, main_window):
        assert hasattr(main_window, 'connection_status')
        assert main_window.connection_status is not None
    
    def test_init_creates_tabs(self, main_window):
        assert hasattr(main_window, 'tabs')
        assert main_window.tabs.count() == 4
    
    def test_init_tab_names(self, main_window):
        assert main_window.tabs.tabText(0) == "Live Monitor"
        assert main_window.tabs.tabText(1) == "Account"
        assert main_window.tabs.tabText(2) == "Health History"
        assert main_window.tabs.tabText(3) == "Research"
    
    def test_init_disabled_tabs(self, main_window):
        # History and Research tabs should be disabled initially
        assert main_window.tabs.isTabEnabled(2) is False
        assert main_window.tabs.isTabEnabled(3) is False
    
    def test_init_bluetooth_thread_started(self, main_window):
        assert hasattr(main_window, 'bluetooth_monitor_thread')


class TestHandleLogin:
    """Test handle_login method."""
    
    def test_login_sets_current_user(self, main_window):
        main_window.handle_login("testuser", "personal")
        
        assert main_window.current_user == "testuser"
    
    def test_login_sets_session_start_time(self, main_window):
        before = datetime.now()
        main_window.handle_login("testuser", "personal")
        after = datetime.now()
        
        assert main_window.session_start_time is not None
        assert before <= main_window.session_start_time <= after
    
    def test_login_resets_expected_sequence(self, main_window):
        main_window.expected_sequence = 100
        main_window.handle_login("testuser", "personal")
        
        assert main_window.expected_sequence == 0
    
    def test_login_enables_history_tab(self, main_window):
        main_window.handle_login("testuser", "personal")
        
        assert main_window.tabs.isTabEnabled(2) is True
    
    def test_login_personal_does_not_enable_research(self, main_window):
        main_window.handle_login("testuser", "personal")
        
        assert main_window.tabs.isTabEnabled(3) is False
    
    def test_login_advanced_enables_research(self, main_window):
        main_window.handle_login("advuser", "advanced")
        
        assert main_window.tabs.isTabEnabled(3) is True
    
    def test_login_updates_status_bar(self, main_window, mocker):
        # Mock the status_bar setText method
        mock_set_text = mocker.patch.object(main_window.status_bar, 'setText')
        main_window.handle_login("testuser", "personal")
        
        mock_set_text.assert_called_once()
        status_text = mock_set_text.call_args[0][0]
        assert "Recording session for testuser" in status_text

    def test_login_switches_to_live_monitor_tab(self, main_window):
        main_window.tabs.setCurrentIndex(1)  # Set to Account tab
        main_window.handle_login("testuser", "personal")
        
        assert main_window.tabs.currentIndex() == 0  # Live Monitor tab


class TestHandleLogout:
    """Test handle_logout method."""
    
    def test_logout_saves_session_if_data_exists(self, main_window):
        main_window.current_user = "testuser"
        main_window.session_start_time = datetime.now()
        main_window.live_monitor_tab.session_bpm = [70, 75, 80]
        main_window.save_current_session = Mock()
        
        main_window.handle_logout()
        
        main_window.save_current_session.assert_called_once()
    
    def test_logout_does_not_save_if_no_user(self, main_window):
        main_window.current_user = None
        main_window.save_current_session = Mock()
        
        main_window.handle_logout()
        
        main_window.save_current_session.assert_not_called()
    
    def test_logout_does_not_save_if_no_session_data(self, main_window):
        main_window.current_user = "testuser"
        main_window.live_monitor_tab.session_bpm = []
        main_window.save_current_session = Mock()
        
        main_window.handle_logout()
        
        main_window.save_current_session.assert_not_called()
    
    def test_logout_resets_current_user(self, main_window):
        main_window.current_user = "testuser"
        main_window.handle_logout()
        
        assert main_window.current_user is None
    
    def test_logout_resets_session_start_time(self, main_window):
        main_window.session_start_time = datetime.now()
        main_window.handle_logout()
        
        assert main_window.session_start_time is None
    
    def test_logout_disables_tabs(self, main_window):
        main_window.tabs.setTabEnabled(2, True)
        main_window.tabs.setTabEnabled(3, True)
        
        main_window.handle_logout()
        
        assert main_window.tabs.isTabEnabled(2) is False
        assert main_window.tabs.isTabEnabled(3) is False
    
    def test_logout_updates_status_bar(self, main_window, mocker):
        # Mock the status_bar setText method
        mock_set_text = mocker.patch.object(main_window.status_bar, 'setText')
        main_window.handle_logout()
        
        mock_set_text.assert_called_once()
        status_text = mock_set_text.call_args[0][0]
        assert "Logged out" in status_text


class TestHandleNewPacket:
    """Test handle_new_packet method."""
    
    def test_handles_packet_sequence(self, main_window):
        packet = {
            'sequence': 42, 'ppg_values': tuple(range(50)), 'bpm': 75.0, 'mode': 0
        }
        main_window.handle_new_packet(packet)
        assert main_window.expected_sequence == 43
    
    def test_logs_sequence_mismatch(self, main_window):
        # REFINED: Simplified test to remove code duplication (DRY principle).
        main_window.system_log.add_log_entry = Mock()

        # Set expected sequence to 10 (as if 10 packets were received)
        main_window.expected_sequence = 10

        # Send an initial packet to set the sequence
        main_window.handle_new_packet({
            'sequence': 10, 'ppg_values': tuple(range(50)), 'bpm': 75.0, 'mode': 0
        })

        # Send a mismatched packet
        main_window.handle_new_packet({
            'sequence': 15, 'ppg_values': tuple(range(50)), 'bpm': 75.0, 'mode': 0
        })

        # Assert that the log method was called with the correct message
        main_window.system_log.add_log_entry.assert_called_once()
        log_message = main_window.system_log.add_log_entry.call_args[0][0]
        
        assert "mismatch" in log_message.lower()
        assert "expected 11" in log_message
        assert "got 15" in log_message

    def test_processes_packet_in_live_monitor(self, main_window):
        packet = {
            'sequence': 1, 'ppg_values': tuple(range(50)), 'bpm': 75.0, 'mode': 0
        }
        main_window.live_monitor_tab.new_data_received = Mock(return_value=None)
        main_window.handle_new_packet(packet)
        
        main_window.live_monitor_tab.new_data_received.assert_called_once_with(packet)
    
    def test_logs_alarm_messages(self, main_window):
        packet = {
            'sequence': 1, 'ppg_values': tuple(range(50)), 'bpm': 75.0, 'mode': 0
        }
        main_window.live_monitor_tab.new_data_received = Mock(return_value="ALARM: High BPM")
        main_window.system_log.add_log_entry = Mock()
        main_window.handle_new_packet(packet)
        
        main_window.system_log.add_log_entry.assert_called_with("ALARM: High BPM")
    
    def test_updates_status_bar_when_logged_in(self, main_window, mocker):
        main_window.current_user = "testuser"
        main_window.session_start_time = datetime.now()
        main_window.live_monitor_tab.session_bpm = [70, 75]
        packet = {
            'sequence': 1, 'ppg_values': tuple(range(50)), 'bpm': 80.0, 'mode': 0
        }
        
        # Mock the status_bar setText method
        mock_set_text = mocker.patch.object(main_window.status_bar, 'setText')
        main_window.handle_new_packet(packet)
        
        mock_set_text.assert_called_once()
        status_text = mock_set_text.call_args[0][0]
        assert "testuser" in status_text
        assert "Current BPM: 80.0" in status_text


class TestHandleConnectionStatus:
    """Test handle_connection_status method."""
    
    def test_updates_connection_status_widget(self, main_window):
        main_window.connection_status.update_status = Mock()
        main_window.handle_connection_status(True, "Connected")
        main_window.connection_status.update_status.assert_called_once_with(True, "Connected")


class TestHandleConnectionTimeout:
    """Test handle_connection_timeout method."""
    
    def test_shows_timeout_alarm(self, main_window):
        main_window.connection_status.show_timeout_alarm = Mock()
        main_window.handle_connection_timeout()
        main_window.connection_status.show_timeout_alarm.assert_called_once()
    
    def test_logs_timeout_message(self, main_window):
        main_window.system_log.add_log_entry = Mock()
        main_window.handle_connection_timeout()
        
        main_window.system_log.add_log_entry.assert_called()
        call_args = main_window.system_log.add_log_entry.call_args[0][0]
        assert "5+ seconds" in call_args


class TestSaveCurrentSession:
    """Test save_current_session method."""
    
    def test_saves_session_data(self, main_window, mocker):
        main_window.current_user = "testuser"
        main_window.session_start_time = datetime(2025, 1, 15, 10, 0, 0)
        main_window.live_monitor_tab.session_bpm = [70, 75, 80, 85, 90]
        main_window.live_monitor_tab.session_raw_ppg = list(range(250))
        main_window.live_monitor_tab.bpm_low = 50
        main_window.live_monitor_tab.bpm_high = 120
        main_window.user_manager.save_session = Mock()
        
        # Correct patch path for datetime
        mock_datetime = mocker.patch('gui.core.main_window.datetime')
        mock_datetime.now.return_value = datetime(2025, 1, 15, 10, 10, 0)
        main_window.save_current_session()
        
        main_window.user_manager.save_session.assert_called_once()
        call_args = main_window.user_manager.save_session.call_args[0]
        
        assert call_args[0] == "testuser"
        session_data = call_args[1]
        assert 'avg_bpm' in session_data
        assert 'min_bpm' in session_data
        assert 'max_bpm' in session_data
        assert session_data['total_samples'] == 5
    
    def test_calculates_statistics_correctly(self, main_window):
        main_window.current_user = "testuser"
        main_window.session_start_time = datetime.now()
        main_window.live_monitor_tab.session_bpm = [60, 70, 80, 90, 100]
        main_window.live_monitor_tab.session_raw_ppg = []
        main_window.live_monitor_tab.bpm_low = 65
        main_window.live_monitor_tab.bpm_high = 95
        main_window.user_manager.save_session = Mock()

        main_window.save_current_session()
        
        session_data = main_window.user_manager.save_session.call_args[0][1]
        
        assert session_data['avg_bpm'] == 80.0
        assert session_data['min_bpm'] == 60.0
        assert session_data['max_bpm'] == 100.0
        assert session_data['abnormal_low'] == 1  # 60 < 65
        assert session_data['abnormal_high'] == 1  # 100 > 95


class TestCloseWindow:
    """Test close_window method."""
    
    def test_saves_session_before_closing(self, main_window, mocker):
        main_window.current_user = "testuser"
        main_window.live_monitor_tab.session_bpm = [70, 75, 80]
        main_window.save_current_session = Mock()
        main_window.bluetooth_monitor.running = True
        
        mocker.patch.object(QtWidgets.QApplication, 'quit')
        main_window.close_window()
        
        main_window.save_current_session.assert_called_once()
    
    def test_stops_bluetooth_monitor(self, main_window, mocker):
        main_window.bluetooth_monitor.running = True
        main_window.bluetooth_monitor_thread.quit = Mock()
        main_window.bluetooth_monitor_thread.wait = Mock()
        
        mocker.patch.object(QtWidgets.QApplication, 'quit')
        main_window.close_window()
        
        assert main_window.bluetooth_monitor.running is False
        main_window.bluetooth_monitor_thread.quit.assert_called_once()
        main_window.bluetooth_monitor_thread.wait.assert_called_once()


class TestIntegration:
    """Integration tests for MainWindow."""
    
    def test_complete_user_session_workflow(self, main_window):
        """Test complete workflow from login to logout."""
        
        # Login
        main_window.handle_login("testuser", "personal")
        assert main_window.current_user == "testuser"
        assert main_window.tabs.isTabEnabled(2) is True
        
        # Receive packets
        for i in range(5):
            packet = {
                'sequence': i, 'ppg_values': tuple(range(50)), 'bpm': 70.0 + i, 'mode': 0
            }
            main_window.handle_new_packet(packet)
        
        assert main_window.expected_sequence == 5
        
        # Logout
        # Mock the save method to prevent actual file I/O during integration test
        main_window.user_manager.save_session = Mock()
        main_window.handle_logout()
        
        # Assert session was saved on logout
        main_window.user_manager.save_session.assert_called_once()
        assert main_window.current_user is None
        assert main_window.tabs.isTabEnabled(2) is False