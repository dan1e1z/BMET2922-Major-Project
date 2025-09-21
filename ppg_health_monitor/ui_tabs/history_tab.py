from PyQt5 import QtWidgets, QtCore
class HistoryTab(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.current_user = None
        self.user_manager = None
        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout()
        title = QtWidgets.QLabel("Health History")
        title.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title)

        self.history_text = QtWidgets.QTextEdit()
        self.history_text.setReadOnly(True)
        layout.addWidget(self.history_text)

        self.setLayout(layout)
