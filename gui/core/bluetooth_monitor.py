"""
Bluetooth monitoring module for PPG Health Monitor.

This module handles serial communication with Bluetooth devices,
specifically for receiving PPG sensor data packets.

Author: Harneet Kaur Dhaliwal, Gladys De Euphrates, Daniel Lindsay-Shad
Note: The Docstrings for methods were generated using Generative AI based on the method functionality.
"""

from PyQt5 import QtCore
import struct
import serial
import serial.tools.list_ports
import time
import datetime
import sys

PACKET_RECEIVE_TIMEOUT = 1.1
FIVE_SEC_TIMEOUT = 5

def get_port():
    """
    Interactively select a serial port for Bluetooth communication.

    Lists available serial ports and prompts user to choose one.
    Exits the program if no ports are available.

    Returns:
        str: The selected serial port device path
    """
    ports = serial.tools.list_ports.comports()
    if not ports:
        print("\nNo serial ports found. Please check your device connection.")
        sys.exit()
    
    print("\nAvailable serial ports:")
    for i, port in enumerate(ports):
        print(f"  {i+1}: {port.device} - {port.description}")

    while True:
        try:
            choice = input("\nEnter the number of the port you want to use: ")
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(ports):
                selected_port = ports[choice_num - 1].device
                print(f"You selected: {selected_port}\n")
                return f"{selected_port}"
            else:
                print("Invalid number. Please pick a number from the list.")
        except ValueError:
            print("Invalid input. Please try again.")

    return f""

class BluetoothMonitor(QtCore.QObject):
    """
    Monitors a single serial port (Bluetooth SPP on ESP32) for incoming data packets.
    """
    packet_received = QtCore.pyqtSignal(dict)
    connection_status_changed = QtCore.pyqtSignal(bool, str)
    connection_timeout = QtCore.pyqtSignal()

    # def __init__(self, port=get_port(), baudRate=115200):
    def __init__(self, port="COMP7", baudRate=115200):
        """
        Initialize the Bluetooth monitor.

        Args:
            port (str): Serial port device path
            baudRate (int): Baud rate for serial communication
        """
        super().__init__()
        self.port = port
        self.baudRate = baudRate
        self.serialPort = serial.Serial()
        self.running = True
        self.STRUCT_FORMAT = "<L50HfB"
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
                self.connection_status_changed.emit(True, f"Connected to {self.port}")
                print("**************************************")
                print(f"** Serial port opened: {self.port}")
                print("**************************************")
                self.last_packet_time = time.time()
                return True
            except serial.SerialException as e:
                print(f"Failed to open port {self.port}: {e}")
                pass

    def reconnect(self):
        """
        Attempt to reconnect to the serial port after a disconnection.
        Closes the current port and tries to establish a new connection.
        """
        print("Reconnecting...")
        start = time.time()
        print(f"Closing port {self.port}...")
        self.serialPort.close()
        # time.sleep(20) 
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

                        now = datetime.datetime.now()

                        data = struct.unpack(self.STRUCT_FORMAT, packet)
                        packet_dict = {
                            "sequence": data[0],
                            "ppg_values": data[1:51],
                            "bpm": data[51],
                            "mode": data[52]
                        }
                        # TESTING DEBUGGING PRINTS
                        print(f"[{now.strftime('%H:%M:%S.%f')}] Received packet: {packet_dict}")
                        # print(f"Received packet sequence: {packet_dict['sequence']}")
                        # print(f"Received packet bpm: {packet_dict['bpm']}")
                        self.packet_received.emit(packet_dict)
                        self.last_packet_time = time.time()
                    else:
                        print("Incomplete packet received. Discarding.")
                        self.serialPort.reset_input_buffer()
                
                # elif time.time() - self.last_packet_time > PACKET_RECEIVE_TIMEOUT:
                #     self.connection_status_changed.emit(False, "Disconnected: Timeout")
                #     self.reconnect()

                # 5 second - packet alert Timeout check
                elif time.time() - self.last_packet_time > FIVE_SEC_TIMEOUT:
                    print(f"No data received for {FIVE_SEC_TIMEOUT}s.")
                    self.connection_status_changed.emit(False, "Disconnected: Timeout")
                    self.connection_timeout.emit()
                    self.reconnect()


            except Exception as e:
                print("Exception")
                self.reconnect()