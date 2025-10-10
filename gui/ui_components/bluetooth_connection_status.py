from PyQt5 import QtWidgets
class BluetoothConnectionStatus(QtWidgets.QWidget):
    """Displays the current Bluetooth connection status and detection mode."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Bluetooth status
        bluetooth_label = QtWidgets.QLabel("Bluetooth:")
        self.status_icon = QtWidgets.QLabel("●")
        self.status_icon.setStyleSheet("font-size: 16px; color: red;")
        self.status_text = QtWidgets.QLabel("Disconnected")
        
        layout.addWidget(bluetooth_label)
        layout.addWidget(self.status_icon)
        layout.addWidget(self.status_text)
        
        # Separator
        separator = QtWidgets.QLabel("|")
        separator.setStyleSheet("color: #ccc; margin: 0 5px;")
        layout.addWidget(separator)
        
        # Detection mode indicator
        mode_label = QtWidgets.QLabel("Mode:")
        self.mode_indicator = QtWidgets.QLabel("--")
        self.mode_indicator.setStyleSheet("color: #1565C0; font-weight: normal;")
        
        layout.addWidget(mode_label)
        layout.addWidget(self.mode_indicator)
        
        # Stretch to push timeout alarm to the right
        layout.addStretch()
        
        # Timeout alarm (on the right side)
        self.timeout_alarm = QtWidgets.QLabel("")
        self.timeout_alarm.setVisible(False)
        layout.addWidget(self.timeout_alarm)
        
        self.setLayout(layout)
    
    def update_status(self, connected, message=""):
        """Update Bluetooth connection status."""
        if connected:
            self.status_icon.setStyleSheet("font-size: 16px; color: green;")
            self.status_text.setText("Connected")
            self.status_text.setStyleSheet("color: green; font-weight: bold;")
            self.timeout_alarm.setVisible(False)
        else:
            self.status_icon.setStyleSheet("font-size: 16px; color: red;")
            self.status_text.setText("Disconnected")
            self.status_text.setStyleSheet("color: red; font-weight: bold;")
    
    def update_mode(self, mode):
        """Update detection mode display.
        
        Args:
            mode (int): 0 for Adaptive Threshold, 1 for Z-score Detection
        """
        mode_text = 'Adaptive' if mode == 0 else 'Z-score'
        self.mode_indicator.setText(mode_text)
    
    def show_timeout_alarm(self):
        """Display timeout warning alarm."""
        self.timeout_alarm.setText("⚠ WARNING: NO DATA (5s) - Check Sensor Power")
        # self.timeout_alarm.setStyleSheet(
        #     "color: #d32f2f; font-weight: bold; background-color: #ffebee; "
        #     "padding: 4px 8px; border: 1px solid #ef5350; border-radius: 3px;"
        # )
        self.timeout_alarm.setStyleSheet(
            "color: white; font-weight: bold; background-color: #ff0000; "
            "padding: 4px 8px; border-radius: 3px;"
        )
        self.timeout_alarm.setVisible(True)
    
    def hide_timeout_alarm(self):
        """Hide timeout warning alarm."""
        self.timeout_alarm.setVisible(False)