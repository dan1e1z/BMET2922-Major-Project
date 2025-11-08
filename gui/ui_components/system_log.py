"""
System log UI component.

Provides a widget for displaying and managing system log messages.

Author: Daniel Lindsay-Shad
Note: The Docstrings for methods were generated using Generative AI based on the method functionality.
"""

from PyQt5 import QtWidgets
from datetime import datetime

class SystemLog(QtWidgets.QWidget):
    """
    A widget for displaying and managing system log messages in the application.
    Provides a text area for log entries and a button to clear the log.
    """
    def __init__(self):
        """
        Initialize the SystemLog widget and set up the UI components.
        """
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        """
        Set up the layout and widgets for the system log UI.
        Includes a title, a read-only text area, and a clear button.
        """
        layout = QtWidgets.QVBoxLayout()
        title = QtWidgets.QLabel("System Log")
        title.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 5px;")
        layout.addWidget(title)

        # Create the log text area
        self.log_text = QtWidgets.QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setStyleSheet("""
            background-color: #2b2b2b; 
            color: #ffffff; 
            font-family: 'Consolas', 'Monaco', monospace; 
            font-size: 11px;
            border: 1px solid #555;
        """)
        layout.addWidget(self.log_text)

        # Create the clear button
        clear_btn = QtWidgets.QPushButton("Clear Log")
        clear_btn.setMaximumWidth(100)
        clear_btn.clicked.connect(self.clear_log)
        layout.addWidget(clear_btn)
        
        # Set the layout for this widget
        self.setLayout(layout)

    def add_log_entry(self, message):
        """
        Add a log entry to the log text area with a timestamp.
        Automatically scrolls to the bottom after adding.

        Args:
            message (str): The log message to add.
        """
        timestamp = datetime.now().strftime("%a %b %d %H:%M:%S %Y")
        log_entry = f"{timestamp}: {message}"
        self.log_text.append(log_entry)

        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_log(self):
        """
        Clear all log entries from the log text area.
        """
        self.log_text.clear()