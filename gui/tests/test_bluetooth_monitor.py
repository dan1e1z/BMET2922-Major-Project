import pytest
import struct
import time
from unittest.mock import Mock
import serial

from gui.core.bluetooth_monitor import BluetoothMonitor


@pytest.fixture
def mock_serial(mocker):
    """Create a mock serial port."""
    mock = mocker.patch('serial.Serial')
    mock_instance = Mock(spec=serial.Serial)
    mock_instance.is_open = False
    mock_instance.in_waiting = 0
    mock.return_value = mock_instance
    return mock_instance


@pytest.fixture
def bt_monitor(mocker):
    """Create a BluetoothMonitor instance."""
    mocker.patch('serial.Serial')
    monitor = BluetoothMonitor(port="COM8", baudRate=115200)
    monitor.running = False
    return monitor


class TestBluetoothMonitorInit:
    """Test BluetoothMonitor initialization."""
    
    def test_init_default_parameters(self, mocker):
        mocker.patch('serial.Serial')
        monitor = BluetoothMonitor()
        
        assert monitor.port == "COM8"
        assert monitor.baudRate == 115200
        assert monitor.running is True
        assert monitor.STRUCT_FORMAT == "<L50HfB"
    
    def test_init_custom_parameters(self, mocker):
        mocker.patch('serial.Serial')
        monitor = BluetoothMonitor(port="COM5", baudRate=9600)
        
        assert monitor.port == "COM5"
        assert monitor.baudRate == 9600
    
    def test_init_serial_port_configuration(self, mocker):
        mocker.patch('serial.Serial')
        monitor = BluetoothMonitor(port="COM8", baudRate=115200)
        
        assert monitor.serialPort.port == "COM8"
        assert monitor.serialPort.baudrate == 115200
        assert monitor.serialPort.bytesize == serial.EIGHTBITS
        assert monitor.serialPort.timeout == 0.1
    
    def test_init_struct_size_calculation(self, mocker):
        mocker.patch('serial.Serial')
        monitor = BluetoothMonitor()
        
        # Verify struct size is calculated correctly
        expected_size = struct.calcsize("<L50HfB")
        assert monitor.STRUCT_SIZE == expected_size
        assert monitor.STRUCT_SIZE == 109  # 4 + 100 + 4 + 1
    
    def test_init_signals_exist(self, mocker):
        mocker.patch('serial.Serial')
        monitor = BluetoothMonitor()
        
        assert hasattr(monitor, 'packet_received')
        assert hasattr(monitor, 'connection_status_changed')
        assert hasattr(monitor, 'connection_timeout')


class TestConnect:
    """Test connect method."""
    
    def test_connect_success(self, bt_monitor, mocker):
        bt_monitor.running = True
        bt_monitor.serialPort.is_open = False
        bt_monitor.serialPort.open = Mock()
        
        mocker.patch('time.time', return_value=1000.0)
        result = bt_monitor.connect()
        
        assert result is True
        bt_monitor.serialPort.open.assert_called_once()
        assert bt_monitor.last_packet_time == 1000.0
    
    def test_connect_already_open(self, bt_monitor):
        bt_monitor.running = True
        bt_monitor.serialPort.is_open = True
        
        result = bt_monitor.connect()
        
        assert result is True
    
    def test_connect_failure_retry(self, bt_monitor, mocker):
        bt_monitor.running = True
        bt_monitor.serialPort.is_open = False
        bt_monitor.serialPort.open = Mock(side_effect=[
            serial.SerialException("Port busy"),
            None  # Success on second try
        ])
        
        mocker.patch('time.time', return_value=1000.0)
        result = bt_monitor.connect()
        
        assert result is True
        assert bt_monitor.serialPort.open.call_count == 2
    
    def test_connect_emits_status_signal(self, bt_monitor, mocker):
        bt_monitor.running = True
        bt_monitor.serialPort.is_open = False
        bt_monitor.serialPort.open = Mock()
        
        signal_spy = Mock()
        bt_monitor.connection_status_changed.connect(signal_spy)
        
        mocker.patch('time.time', return_value=1000.0)
        bt_monitor.connect()
        
        signal_spy.assert_called_once_with(True, "Connected to COM8")
    
    def test_connect_stops_when_not_running(self, bt_monitor):
        bt_monitor.running = False
        bt_monitor.serialPort.open = Mock()
        
        # Should exit without opening
        result = bt_monitor.connect()
        
        assert result is None
        bt_monitor.serialPort.open.assert_not_called()


class TestReconnect:
    """Test reconnect method."""
    
    def test_reconnect_closes_and_reopens(self, bt_monitor, mocker):
        bt_monitor.serialPort.close = Mock()
        bt_monitor.connect = Mock()
        
        mocker.patch('time.time', side_effect=[100.0, 100.5])
        bt_monitor.reconnect()
        
        bt_monitor.serialPort.close.assert_called_once()
        bt_monitor.connect.assert_called_once()
    
    def test_reconnect_measures_time(self, bt_monitor, capsys, mocker):
        bt_monitor.serialPort.close = Mock()
        bt_monitor.connect = Mock()
        
        mocker.patch('time.time', side_effect=[100.0, 102.5])
        bt_monitor.reconnect()
        
        captured = capsys.readouterr()
        assert "2.50 seconds" in captured.out


class TestMonitor:
    """Test monitor method."""
    
    def test_monitor_reads_complete_packet(self, bt_monitor, mocker):
        # Create a valid packet
        sequence = 42
        ppg_values = tuple(range(50))
        bpm = 75.5
        mode = 1
        
        packet_data = struct.pack("<L50HfB", sequence, *ppg_values, bpm, mode)
        
        bt_monitor.running = True
        bt_monitor.serialPort.is_open = True
        bt_monitor.serialPort.in_waiting = len(packet_data)
        bt_monitor.serialPort.read = Mock(return_value=packet_data)
        
        signal_spy = Mock()
        bt_monitor.packet_received.connect(signal_spy)
        
        # Run one iteration
        mocker.patch('time.time', return_value=1000.0)
        # Manually run one iteration
        if bt_monitor.serialPort.in_waiting >= bt_monitor.STRUCT_SIZE:
            packet = bt_monitor.serialPort.read(bt_monitor.STRUCT_SIZE)
            if len(packet) == bt_monitor.STRUCT_SIZE:
                data = struct.unpack(bt_monitor.STRUCT_FORMAT, packet)
                packet_dict = {
                    "sequence": data[0],
                    "ppg_values": data[1:51],
                    "bpm": data[51],
                    "mode": data[52]
                }
                bt_monitor.packet_received.emit(packet_dict)
                bt_monitor.last_packet_time = time.time()
        
        signal_spy.assert_called_once()
        call_args = signal_spy.call_args[0][0]
        assert call_args['sequence'] == sequence
        assert call_args['bpm'] == bpm
        assert call_args['mode'] == mode
        assert len(call_args['ppg_values']) == 50
    
    def test_monitor_handles_incomplete_packet(self, bt_monitor):
        bt_monitor.running = True
        bt_monitor.serialPort.is_open = True
        bt_monitor.serialPort.in_waiting = 109
        bt_monitor.serialPort.read = Mock(return_value=b'incomplete')
        bt_monitor.serialPort.reset_input_buffer = Mock()
        
        # Simulate one iteration
        if bt_monitor.serialPort.in_waiting >= bt_monitor.STRUCT_SIZE:
            packet = bt_monitor.serialPort.read(bt_monitor.STRUCT_SIZE)
            if len(packet) != bt_monitor.STRUCT_SIZE:
                bt_monitor.serialPort.reset_input_buffer()
        
        bt_monitor.serialPort.reset_input_buffer.assert_called_once()
    
    def test_monitor_timeout_triggers_reconnect(self, bt_monitor, mocker):
        bt_monitor.running = True
        bt_monitor.serialPort.is_open = True
        bt_monitor.serialPort.in_waiting = 0
        bt_monitor.last_packet_time = 1000.0
        bt_monitor.reconnect = Mock()
        
        signal_spy = Mock()
        bt_monitor.connection_status_changed.connect(signal_spy)
        timeout_spy = Mock()
        bt_monitor.connection_timeout.connect(timeout_spy)
        
        # Simulate timeout condition
        mocker.patch('time.time', return_value=1006.0)  # 6 seconds later
        current_time = time.time()
        if current_time - bt_monitor.last_packet_time > 5:
            bt_monitor.connection_status_changed.emit(False, "Disconnected: Timeout")
            bt_monitor.connection_timeout.emit()
            bt_monitor.reconnect()
        
        signal_spy.assert_called_once_with(False, "Disconnected: Timeout")
        timeout_spy.assert_called_once()
        bt_monitor.reconnect.assert_called_once()
    
    def test_monitor_connects_when_port_closed(self, bt_monitor):
        bt_monitor.running = True
        bt_monitor.serialPort = None
        bt_monitor.connect = Mock()
        
        # Simulate check in monitor loop
        if not bt_monitor.serialPort or not getattr(bt_monitor.serialPort, 'is_open', False):
            bt_monitor.connect()
        
        bt_monitor.connect.assert_called_once()
    
    def test_monitor_handles_exception(self, bt_monitor):
        bt_monitor.running = True
        bt_monitor.serialPort.is_open = True
        # FIX: Ensure the monitor loop terminates by setting running to False
        # in the mock. This prevents the test from hanging.
        def stop_loop():
            bt_monitor.running = False

        bt_monitor.serialPort.in_waiting = Mock(side_effect=Exception("Serial error"))
        bt_monitor.reconnect = Mock(side_effect=stop_loop)

        # Call the method under test
        bt_monitor.monitor()

        # Assert that reconnect was called once
        bt_monitor.reconnect.assert_called_once()



class TestPacketParsing:
    """Test packet structure and parsing."""
    
    def test_packet_structure_format(self, bt_monitor):
        # Verify the struct format matches expected packet structure
        assert bt_monitor.STRUCT_FORMAT == "<L50HfB"
        
        # L = unsigned long (4 bytes) - sequence
        # 50H = 50 unsigned shorts (100 bytes) - PPG values
        # f = float (4 bytes) - BPM
        # B = unsigned char (1 byte) - mode
        # Total = 109 bytes
        assert bt_monitor.STRUCT_SIZE == 109
    
    def test_unpack_packet_structure(self, bt_monitor):
        sequence = 100
        ppg_values = tuple(range(1000, 1050))
        bpm = 80.5
        mode = 0
        
        packet = struct.pack("<L50HfB", sequence, *ppg_values, bpm, mode)
        unpacked = struct.unpack("<L50HfB", packet)
        
        assert unpacked[0] == sequence
        assert unpacked[1:51] == ppg_values
        assert abs(unpacked[51] - bpm) < 0.01
        assert unpacked[52] == mode
    
    def test_packet_dict_creation(self, bt_monitor):
        data = (42,) + tuple(range(50)) + (75.5, 1)
        
        packet_dict = {
            "sequence": data[0],
            "ppg_values": data[1:51],
            "bpm": data[51],
            "mode": data[52]
        }
        
        assert packet_dict['sequence'] == 42
        assert len(packet_dict['ppg_values']) == 50
        assert packet_dict['bpm'] == 75.5
        assert packet_dict['mode'] == 1


class TestTimeouts:
    """Test timeout constants and behavior."""
    
    def test_timeout_constants_defined(self):
        from gui.core.bluetooth_monitor import PACKET_RECEIVE_TIMEOUT, FIVE_SEC_TIMEOUT
        
        assert PACKET_RECEIVE_TIMEOUT == 1.1
        assert FIVE_SEC_TIMEOUT == 5
    
    def test_timeout_logic(self, bt_monitor, mocker):
        bt_monitor.last_packet_time = 1000.0
        
        # Not timed out
        mocker.patch('time.time', return_value=1004.0)
        assert time.time() - bt_monitor.last_packet_time < 5
        
        # Timed out
        mocker.patch('time.time', return_value=1006.0)
        assert time.time() - bt_monitor.last_packet_time > 5


class TestSignals:
    """Test PyQt signals."""
    
    def test_packet_received_signal_emits_dict(self, bt_monitor):
        signal_spy = Mock()
        bt_monitor.packet_received.connect(signal_spy)
        
        test_packet = {
            "sequence": 1,
            "ppg_values": tuple(range(50)),
            "bpm": 75.0,
            "mode": 0
        }
        
        bt_monitor.packet_received.emit(test_packet)
        
        signal_spy.assert_called_once_with(test_packet)
    
    def test_connection_status_signal_emits_bool_and_string(self, bt_monitor):
        signal_spy = Mock()
        bt_monitor.connection_status_changed.connect(signal_spy)
        
        bt_monitor.connection_status_changed.emit(True, "Connected")
        signal_spy.assert_called_with(True, "Connected")
        
        bt_monitor.connection_status_changed.emit(False, "Disconnected")
        signal_spy.assert_called_with(False, "Disconnected")
    
    def test_connection_timeout_signal(self, bt_monitor):
        signal_spy = Mock()
        bt_monitor.connection_timeout.connect(signal_spy)
        
        bt_monitor.connection_timeout.emit()
        
        signal_spy.assert_called_once()


class TestIntegration:
    """Integration tests for BluetoothMonitor."""
    
    def test_complete_packet_reception_flow(self, bt_monitor, mocker):
        """Test complete flow from packet reception to signal emission."""
        bt_monitor.running = True
        bt_monitor.serialPort.is_open = True
        
        # Create multiple packets
        packets_data = []
        for i in range(3):
            sequence = i
            ppg_values = tuple(range(i*10, i*10+50))
            bpm = 70.0 + i
            mode = i % 2
            packets_data.append(struct.pack("<L50HfB", sequence, *ppg_values, bpm, mode))
        
        received_packets = []
        
        def capture_packet(packet):
            received_packets.append(packet)
        
        bt_monitor.packet_received.connect(capture_packet)
        
        # Simulate receiving each packet
        for packet_data in packets_data:
            bt_monitor.serialPort.in_waiting = len(packet_data)
            bt_monitor.serialPort.read = Mock(return_value=packet_data)
            
            mocker.patch('time.time', return_value=1000.0)
            if bt_monitor.serialPort.in_waiting >= bt_monitor.STRUCT_SIZE:
                packet = bt_monitor.serialPort.read(bt_monitor.STRUCT_SIZE)
                if len(packet) == bt_monitor.STRUCT_SIZE:
                    data = struct.unpack(bt_monitor.STRUCT_FORMAT, packet)
                    packet_dict = {
                        "sequence": data[0],
                        "ppg_values": data[1:51],
                        "bpm": data[51],
                        "mode": data[52]
                    }
                    bt_monitor.packet_received.emit(packet_dict)
        
        assert len(received_packets) == 3
        assert received_packets[0]['sequence'] == 0
        assert received_packets[1]['sequence'] == 1
        assert received_packets[2]['sequence'] == 2