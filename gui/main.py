"""
Main entry point for the PPG Health Monitor GUI application.

Author: Daniel Lindsay-Shad
Note: The Docstrings for methods were generated using Generative AI based on the method functionality.
"""

import sys
from PyQt5 import QtWidgets

from gui.core import MainWindow


def main():
    """
    Main application entry point.
    """
    QtWidgets.QApplication.setStyle('Fusion')
    # Create the QApplication instance.
    app = QtWidgets.QApplication(sys.argv)
    
    # Create an instance of your main window.
    viewer = MainWindow()
    
    # Display the window.
    viewer.show()
    
    # Start the application's event loop.
    return sys.exit(app.exec_())


if __name__ == "__main__":
    main()