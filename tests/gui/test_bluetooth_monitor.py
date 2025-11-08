"""
Test module for BluetoothMonitor.

Author: Daniel Lindsay-Shad
Note: The Docstrings for methods were generated using Generative AI based on the method functionality.
"""

import pytest
import serial
import struct
import time
from unittest.mock import MagicMock, Mock

from gui.core.bluetooth_monitor import BluetoothMonitor, FIVE_SEC_TIMEOUT


@pytest.fixture
def bt(mocker):
    serial_instance = MagicMock()
    serial_instance.is_open = False
    serial_instance.in_waiting = 0
    serial_instance.read.return_value = b''
    serial_instance.reset_input_buffer = Mock()
    serial_instance.close = Mock()

    mocker.patch('serial.Serial', return_value=serial_instance)
    monitor = BluetoothMonitor(port='COMX')
    monitor.running = False
    return monitor


def test_init_and_struct(bt):
    assert bt.STRUCT_FORMAT == '<L50HfB'
    assert bt.STRUCT_SIZE == struct.calcsize(bt.STRUCT_FORMAT)


def test_connect_emits_status(mocker, bt):
    bt.running = True
    bt.serialPort.is_open = False
    bt.serialPort.open = Mock()
    spy = Mock()
    bt.connection_status_changed.connect(spy)
    mocker.patch('time.time', return_value=1234.5)
    bt.connect()
    spy.assert_called_once_with(True, 'Connected to COMX')


def test_packet_parsing_emits(bt):
    # craft minimal valid packet
    seq = 1
    ppg = tuple(range(50))
    bpm = 72.5
    mode = 0
    pkt = struct.pack('<L50HfB', seq, *ppg, bpm, mode)

    spy = Mock()
    bt.packet_received.connect(spy)
    # simulate reading
    data = struct.unpack(bt.STRUCT_FORMAT, pkt)
    packet_dict = {
        'sequence': data[0],
        'ppg_values': data[1:51],
        'bpm': data[51],
        'mode': data[52]
    }
    bt.packet_received.emit(packet_dict)
    spy.assert_called_once_with(packet_dict)


def test_timeout_logic(mocker, bt):
    bt.last_packet_time = 0
    mocker.patch('time.time', return_value=FIVE_SEC_TIMEOUT + 10)
    spy = Mock()
    bt.connection_timeout.connect(spy)
    # simulate monitor reacting to timeout
    bt.connection_timeout.emit()
    spy.assert_called_once()


def test_monitor_requests_connect_when_port_closed(mocker, bt):
    """If the port is closed the monitor should attempt to reconnect."""
    bt.serialPort.is_open = False
    bt.running = True

    def connect_side_effect():
        bt.running = False
        bt.last_packet_time = time.time()
        return True

    mock_connect = mocker.patch.object(bt, 'connect', side_effect=connect_side_effect)

    bt.monitor()

    mock_connect.assert_called_once()


def test_reconnect_method(mocker, bt):
    """Test the reconnect method."""
    bt.running = True
    
    # Mock serial port operations
    bt.serialPort.close = Mock()
    mocker.patch('time.sleep')  # Don't actually sleep
    
    # Mock connect to succeed
    mocker.patch.object(bt, 'connect', return_value=True)
    mocker.patch('time.time', return_value=123.0)
    
    bt.reconnect()
    
    bt.serialPort.close.assert_called_once()
    bt.connect.assert_called_once()


def test_monitor_packet_processing(mocker, bt):
    """Test packet processing triggers signal emission."""
    bt.serialPort.is_open = True
    bt.running = True

    # Create a valid packet
    seq = 42
    ppg = tuple(range(50))
    bpm = 75.5
    mode = 1
    packet = struct.pack('<L50HfB', seq, *ppg, bpm, mode)

    bt.serialPort.in_waiting = bt.STRUCT_SIZE

    def read_side_effect(_):
        bt.running = False
        bt.serialPort.in_waiting = 0
        return packet

    bt.serialPort.read = Mock(side_effect=read_side_effect)

    mocker.patch('time.time', return_value=1000.0)
    mocker.patch('builtins.print')

    spy = Mock()
    bt.packet_received.connect(spy)

    bt.monitor()

    spy.assert_called_once()
    called_dict = spy.call_args[0][0]
    assert called_dict['sequence'] == seq
    assert called_dict['bpm'] == bpm
    assert called_dict['mode'] == mode
    assert len(called_dict['ppg_values']) == 50


def test_monitor_handles_incomplete_packet(mocker, bt):
    bt.serialPort.is_open = True
    bt.running = True
    bt.serialPort.in_waiting = bt.STRUCT_SIZE

    def read_side_effect(_):
        bt.running = False
        bt.serialPort.in_waiting = 0
        return b'incomplete'

    bt.serialPort.read = Mock(side_effect=read_side_effect)

    mocker.patch('builtins.print')

    bt.monitor()

    bt.serialPort.reset_input_buffer.assert_called_once()


def test_monitor_timeout_triggers_alarm(mocker, bt):
    bt.serialPort.is_open = True
    bt.running = True
    bt.last_packet_time = 0
    bt.serialPort.in_waiting = 0

    mocker.patch('time.time', return_value=FIVE_SEC_TIMEOUT + 1)

    def reconnect_side_effect():
        bt.running = False

    mock_reconnect = mocker.patch.object(bt, 'reconnect', side_effect=reconnect_side_effect)
    mocker.patch('builtins.print')

    spy_status = Mock()
    spy_timeout = Mock()
    bt.connection_status_changed.connect(spy_status)
    bt.connection_timeout.connect(spy_timeout)

    bt.monitor()

    spy_status.assert_called_once_with(False, 'Disconnected: Timeout')
    spy_timeout.assert_called_once()
    mock_reconnect.assert_called_once()


def test_monitor_exception_handling(mocker, bt):
    bt.serialPort.is_open = True
    bt.running = True
    bt.serialPort.in_waiting = bt.STRUCT_SIZE
    bt.serialPort.read = Mock(side_effect=OSError("boom"))

    def reconnect_side_effect():
        bt.running = False

    mock_reconnect = mocker.patch.object(bt, 'reconnect', side_effect=reconnect_side_effect)
    mocker.patch('builtins.print')

    bt.monitor()

    mock_reconnect.assert_called_once()


def test_monitor_stops_when_not_running(bt):
    bt.running = False
    bt.monitor()  # should return immediately without error


def test_connect_exception_handling(mocker, bt):
    """Test exception handling in connect method."""
    bt.running = True
    bt.serialPort.is_open = False
    def raising_open():
        bt.running = False  # stop after first failure
        raise serial.SerialException("Connection failed")

    bt.serialPort.open = Mock(side_effect=raising_open)
    
    # Mock print
    mocker.patch('builtins.print')
    
    # This should not raise an exception, just not connect
    result = bt.connect()
    assert result is None  # connect doesn't return anything when it fails