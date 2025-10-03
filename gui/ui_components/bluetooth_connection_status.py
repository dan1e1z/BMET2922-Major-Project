from PyQt5 import QtWidgets
class BluetoothConnectionStatus(QtWidgets.QWidget):
    """Displays the current Bluetooth connection status."""
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QtWidgets.QHBoxLayout()
        
        self.status_icon = QtWidgets.QLabel("●")
        self.status_icon.setStyleSheet("font-size: 16px; color: red;")
        self.status_text = QtWidgets.QLabel("Disconnected")
        
        self.timeout_alarm = QtWidgets.QLabel("")
        self.timeout_alarm.setVisible(False)
       
        
        layout.addWidget(QtWidgets.QLabel("Bluetooth:"))
        layout.addWidget(self.status_icon)
        layout.addWidget(self.status_text)
        layout.addStretch()
        layout.addWidget(self.timeout_alarm)
        
        self.setLayout(layout)
    
    def update_status(self, connected, message=""):
        if connected:
            self.status_icon.setStyleSheet("font-size: 16px; color: green;")
            self.status_text.setText("Connected")
            self.status_text.setStyleSheet("color: green; font-weight: bold;")
            self.timeout_alarm.setVisible(False)
        else:
            self.status_icon.setStyleSheet("font-size: 16px; color: red;")
            self.status_text.setText("Disconnected")
            self.status_text.setStyleSheet("color: red; font-weight: bold;")
    
    def show_timeout_alarm(self):
        self.timeout_alarm.setText("WARNING: NO DATA - Check Sensor Power")
        self.timeout_alarm.setStyleSheet("color: red; font-weight: bold; background-color: #ffcccc; padding: 5px; border: 1px solid red; border-radius: 3px;")
        self.timeout_alarm.setVisible(True)
    
    def hide_timeout_alarm(self):
        self.timeout_alarm.setVisible(False)