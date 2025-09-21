from PyQt5 import QtWidgets, QtCore, QtGui

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PPG Health Monitor")
        self.setGeometry(100, 100, 1200, 800)

        # You will add your tabs and other widgets here later
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)

        layout = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel("This is a working MainWindow!")
        label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(label)
        central_widget.setLayout(layout)