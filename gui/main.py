import sys
from PyQt5 import QtWidgets

from gui.main_window import MainWindow

if __name__ == "__main__":
    # Create the QApplication instance.
    app = QtWidgets.QApplication(sys.argv)
    
    # Create an instance of your main window.
    viewer = MainWindow()
    
    # Display the window.
    viewer.show()
    
    # Start the application's event loop.
    sys.exit(app.exec_())