import pytest
import struct
from unittest.mock import Mock

from gui.core.bluetooth_monitor import BluetoothMonitor, FIVE_SEC_TIMEOUT


@pytest.fixture
def bt(mocker):
    mocker.patch('serial.Serial')
    m = BluetoothMonitor(port='COMX')
    m.running = False
    return m


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