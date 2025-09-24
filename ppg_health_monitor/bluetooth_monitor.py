from PyQt5 import QtCore
import struct
import serial
import time

PACKET_RECEIVE_TIMEOUT = 1.1
FIVE_SEC_TIMEOUT = 5

class BluetoothMonitor(QtCore.QObject):
    """
    Monitors a single serial port (Bluetooth SPP on ESP32) for incoming data packets.
    """
    packet_received = QtCore.pyqtSignal(dict)
    connection_status_changed = QtCore.pyqtSignal(bool, str)
    connection_timeout = QtCore.pyqtSignal()

    def __init__(self, port="COM8", baudRate=115200):
        super().__init__()
        self.port = port
        self.baudRate = baudRate
        self.serialPort = serial.Serial()
        self.running = True
        self.STRUCT_FORMAT = "<L50HBB"
        self.STRUCT_SIZE = struct.calcsize(self.STRUCT_FORMAT)
        self.last_packet_time = 0

        self.serialPort.port = port
        self.serialPort.baudrate = baudRate
        self.serialPort.bytesize = serial.EIGHTBITS
        self.serialPort.timeout = 0.1

    def connect(self):
        """
        Attempt to open the serial port repeatedly.
        """
        while self.running:
            if self.serialPort.is_open:
                return True
            try:
                print("before port open")
                self.serialPort.open()
                print("**************************************")
                print(f"** Serial port opened: {self.port}")
                print("**************************************")
                self.last_packet_time = time.time()
                return True
            except serial.SerialException:
                pass

    def reconnect(self):
        print("Reconnecting...")
        start = time.time()
        print(f"Closing port {self.port}...")
        self.serialPort.close()
        self.connect()
        print(f"Reconnected in {time.time() - start:.2f} seconds.")


        

    def monitor(self):
        """
        Main loop: reads packets, handles timeouts, and reconnects if needed.
        """
        while self.running:

            if not self.serialPort or not self.serialPort.is_open:
                self.connect()

            try:
                if self.serialPort.in_waiting >= self.STRUCT_SIZE:
                    packet = self.serialPort.read(self.STRUCT_SIZE)
                    if len(packet) == self.STRUCT_SIZE:
                        data = struct.unpack(self.STRUCT_FORMAT, packet)
                        packet_dict = {
                            "sequence": data[0],
                            "ppg_values": data[1:51],
                            "bpm": data[51],
                            "temp": data[52]
                        }
                        # TESTING DEBUGGING PRINTS
                        # print(f"Received packet sequence: {packet_dict['sequence']}")
                        # print(f"Received packet bpm: {packet_dict['bpm']}")
                        self.packet_received.emit(packet_dict)
                        self.last_packet_time = time.time()
                    else:
                        print("Incomplete packet received. Discarding.")
                        self.serialPort.reset_input_buffer()

                elif time.time() - self.last_packet_time > PACKET_RECEIVE_TIMEOUT:
                    self.reconnect()


                # 5 second - packet alert Timeout check
                # if time.time() - self.last_packet_time > FIVE_SEC_TIMEOUT:
                #     print(f"No data received for {FIVE_SEC_TIMEOUT}s.")
                #     self.connection_timeout.emit()
                #     self.reconnect()


            except Exception as e:
                print("Exception")
                self.reconnect()