from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg
class HistoryTab(QtWidgets.QWidget):
    """
    Tab widget for displaying user's health history, session stats, and BPM distribution analysis.
    """
    def __init__(self):
        """
        Initialize the HistoryTab and set up the UI.
        """
        super().__init__()
        self.current_user = None
        self.user_manager = None
        self.setup_ui()

    def setup_ui(self):
        """
        Set up the main layout, including title, summary, session history, and plot widgets inside a scroll area.
        """

        layout = QtWidgets.QVBoxLayout()

        # Title
        title = QtWidgets.QLabel("Health History")
        title.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title)

        # Create scroll area for content
        scroll = QtWidgets.QScrollArea()
        scroll_widget = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout()

        # Summary stats
        self.summary_widget = self.create_summary_widget()
        scroll_layout.addWidget(self.summary_widget)

        # Session history
        self.history_widget = self.create_history_widget()
        scroll_layout.addWidget(self.history_widget)
        
        # Histogram plot
        self.plot_widget = self.create_plot_widget()
        scroll_layout.addWidget(self.plot_widget)
        
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        self.setLayout(layout)
    
    def create_summary_widget(self):
        """
        Create and return a widget displaying the user's health summary.
        """
        widget = QtWidgets.QGroupBox("Health Summary")
        layout = QtWidgets.QVBoxLayout()
        
        self.summary_label = QtWidgets.QLabel("Please log in to view your health summary")
        layout.addWidget(self.summary_label)
        
        widget.setLayout(layout)
        return widget
    

    def create_history_widget(self):
        """
        Create and return a widget displaying the user's session history in a table.
        Columns are set to equal width for clarity.
        """
        widget = QtWidgets.QGroupBox("Session History")
        layout = QtWidgets.QVBoxLayout()

        self.history_table = QtWidgets.QTableWidget()
        self.history_table.setColumnCount(8)
        self.history_table.setHorizontalHeaderLabels([
            "Date", "Duration (min)", "Avg BPM", "Min BPM", "Max BPM",
            "Abnormal Readings", "Low Thresh", "High Thresh"
        ])

        header = self.history_table.horizontalHeader()
        header.setStretchLastSection(True)
        for i in range(self.history_table.columnCount()):
            header.setSectionResizeMode(i, QtWidgets.QHeaderView.Stretch)

        layout.addWidget(self.history_table)
        widget.setLayout(layout)
        return widget
    

    def create_plot_widget(self):
        """
        Create and return a widget displaying a histogram plot of BPM distribution and analysis text.
        """
        widget = QtWidgets.QGroupBox("BPM Distribution Analysis")
        layout = QtWidgets.QVBoxLayout()
        
        # Create plot widget
        self.plot = pg.PlotWidget()
        self.plot.setLabel('left', 'Frequency')
        self.plot.setLabel('bottom', 'BPM')
        self.plot.showGrid(True, True)
        self.plot.setMouseEnabled(x=False, y=False)  # Disable mouse interaction
        self.plot.setMenuEnabled(False)  # Disable context menu
        self.plot.enableAutoRange(False)  # Prevent auto-scaling
        layout.addWidget(self.plot)
        
        # Analysis text
        self.analysis_label = QtWidgets.QLabel("")
        self.analysis_label.setWordWrap(True)
        layout.addWidget(self.analysis_label)
        
        widget.setLayout(layout)
        return widget


