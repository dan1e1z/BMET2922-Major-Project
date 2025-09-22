from PyQt5 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
import numpy as np
from datetime import datetime
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
    
    def start_session(self, username, user_manager):
        """
        Start a new session for the given user.
        Loads user data and updates the UI components accordingly.

        Args:
            username (str): The username of the logged-in user.
            user_manager (UserManager): The user manager instance for data access.
        """
        self.current_user = username
        self.user_manager = user_manager
        self.update_history_view()

    def update_history_view(self):
        # Should only be called when a user is logged in

        # Get logged in User History
        user_data = self.user_manager.users[self.current_user]
        history = user_data.get("history", [])

        # User has not History - first session
        if not history:
            self.summary_label.setText("No session data available yet. Start recording to build your health history!")
            self.history_table.setRowCount(0)
            self.plot.clear()
            self.analysis_label.setText("")
            return
        
        # Update summary
        self.update_summary(user_data, history)
        
        # Update history table
        self.update_history_table(history)
        
        # Update plot
        self.update_plot(history)

    def update_summary(self, user_data, history):
        total_sessions = len(history)
        total_duration = sum(session.get("duration_minutes", 0) for session in history)
        
        all_bpms = []
        all_low_count = 0
        all_high_count = 0
        
        for session in history:
            avg_bpm = session.get("avg_bpm", 0)
            all_bpms.append(avg_bpm)

        
        if all_bpms:
            overall_avg = np.mean(all_bpms)
            overall_min = np.min(all_bpms)
            overall_max = np.max(all_bpms)
            
            # Health insights
            
            summary_text = f"""
            <b>Overall Health Metrics:</b><br>
            • Total Sessions: {total_sessions}<br>
            • Total Recording Time: {total_duration:.1f} minutes<br>
            • Average BPM: {overall_avg:.1f} <br>
            • BPM Range: {overall_min:.1f} - {overall_max:.1f}<br>
            • Abnormal Low Readings (&lt;40): {all_low_count}<br>
            • Abnormal High Readings (&gt;200): {all_high_count}<br>
            """
            
            # Add recent trend
            if len(history) >= 2:
                recent_avg = np.mean([s.get("avg_bpm", 0) for s in history[-3:]])
                older_avg = np.mean([s.get("avg_bpm", 0) for s in history[:-3]]) if len(history) > 3 else recent_avg
                
                trend = "stable"
                if recent_avg > older_avg + 5:
                    trend = "increasing"
                elif recent_avg < older_avg - 5:
                    trend = "decreasing"
                
                summary_text += f"<br><b>Recent Trend:</b> Your heart rate appears to be {trend} compared to earlier sessions."
            
        else:
            summary_text = "No valid BPM data recorded yet."
        
        self.summary_label.setText(summary_text)
    
    def update_history_table(self, history):
        self.history_table.setRowCount(len(history))

        for i, session in enumerate(reversed(history)):
            date_str = datetime.fromisoformat(session["start"]).strftime("%Y-%m-%d %H:%M")
            duration = session.get("duration_minutes", 0)
            avg_bpm = session.get("avg_bpm", 0)
            min_bpm = session.get("min_bpm", 0)
            max_bpm = session.get("max_bpm", 0)

            self.history_table.setItem(i, 0, QtWidgets.QTableWidgetItem(date_str))
            self.history_table.setItem(i, 1, QtWidgets.QTableWidgetItem(f"{duration:.1f}"))
            self.history_table.setItem(i, 2, QtWidgets.QTableWidgetItem(f"{avg_bpm:.1f}"))
            self.history_table.setItem(i, 3, QtWidgets.QTableWidgetItem(f"{min_bpm:.1f}"))
            self.history_table.setItem(i, 4, QtWidgets.QTableWidgetItem(f"{max_bpm:.1f}"))
  
    
    def update_plot(self, history):
        self.plot.clear()
        
        # Collect all BPM data
        all_bpms = []
        for session in history:
            avg_bpm = session.get("avg_bpm", 0)
            if avg_bpm > 0:
                all_bpms.append(avg_bpm)
        
        if not all_bpms:
            self.analysis_label.setText("No BPM data available for analysis.")
            return
        
        # Create histogram data
        hist, bins = np.histogram(all_bpms, bins=20)
        
        # Create x positions for bars (center of each bin)
        x_pos = np.arange(len(hist))
        
        # Create labels for x-axis (BPM ranges)
        x_labels = []
        for i in range(len(bins)-1):
            x_labels.append(f"{bins[i]:.0f}-{bins[i+1]:.0f}")
        
        # Create bar colors based on BPM ranges
        bar_colors = []
        for i in range(len(hist)):
            bin_center = (bins[i] + bins[i+1]) / 2
            if bin_center < 40:
                bar_colors.append((255, 0, 0, 150))  # Red with transparency
            elif bin_center < 60:
                bar_colors.append((255, 165, 0, 150))  # Orange
            elif bin_center <= 100:
                bar_colors.append((0, 128, 0, 150))  # Green
            elif bin_center <= 200:
                bar_colors.append((255, 165, 0, 150))  # Orange
            else:
                bar_colors.append((255, 0, 0, 150))  # Red
        
        # Create the bar plot
        bar_plot = pg.BarGraphItem(
            x=x_pos, 
            height=hist, 
            width=0.8, 
            brushes=bar_colors,
            pen={'color': 'black', 'width': 1}
        )
        self.plot.addItem(bar_plot)
        
        # Set up the plot
        self.plot.setLabel('left', 'Number of Sessions')
        self.plot.setLabel('bottom', 'BPM Range')
        self.plot.setTitle('Distribution of Average BPM Across Sessions')
        
        # Set x-axis ticks and labels
        x_ticks = [(i, label) for i, label in enumerate(x_labels)]
        self.plot.getAxis('bottom').setTicks([x_ticks])
        
        # Set axis ranges to prevent weird scaling
        self.plot.setXRange(-0.5, len(hist) - 0.5)
        self.plot.setYRange(0, max(hist) * 1.1 if max(hist) > 0 else 1)
        
        # Find which bins correspond to normal range
        normal_bins = []
        for i, (bin_start, bin_end) in enumerate(zip(bins[:-1], bins[1:])):
            bin_center = (bin_start + bin_end) / 2
            if 60 <= bin_center <= 100:
                normal_bins.append(i)
        
        if normal_bins:
            # Add text annotation for normal range
            normal_text = pg.TextItem("Normal Range (60-100 BPM)", color=(0, 128, 0))
            normal_text.setPos(normal_bins[0], max(hist) * 0.9)
            self.plot.addItem(normal_text)
        
        # Analysis
        avg_bpm = np.mean(all_bpms)
        std_bpm = np.std(all_bpms)
        min_bpm = np.min(all_bpms)
        max_bpm = np.max(all_bpms)
        
        low_count = sum(1 for bpm in all_bpms if bpm < 40)
        high_count = sum(1 for bpm in all_bpms if bpm > 200)
        normal_count = sum(1 for bpm in all_bpms if 60 <= bpm <= 100)
        
        analysis_text = f"""
        <b>BPM Distribution Analysis:</b><br>
        • Total Sessions Analyzed: {len(all_bpms)}<br>
        • Average BPM: {avg_bpm:.1f} ± {std_bpm:.1f}<br>
        • Range: {min_bpm:.1f} - {max_bpm:.1f} BPM<br>
        <br>
        <b>Health Insights:</b><br>
        """
        
        # Add health recommendations
        if normal_count/len(all_bpms) > 0.8:
            analysis_text += "• Excellent: Most of your readings are in the normal range!<br>"
        elif normal_count/len(all_bpms) > 0.6:
            analysis_text += "• Good: Majority of your readings are normal. Monitor any patterns.<br>"
        else:
            analysis_text += "• Attention: Consider consulting a healthcare provider about your readings.<br>"
        
        if low_count > 0:
            analysis_text += f"• You have {low_count} readings below 40 BPM - this may indicate bradycardia.<br>"
        
        if high_count > 0:
            analysis_text += f"• You have {high_count} readings above 200 BPM - this may indicate tachycardia.<br>"
        
        # Variability assessment
        if std_bpm < 5:
            analysis_text += "• Your heart rate is very consistent across sessions.<br>"
        elif std_bpm < 15:
            analysis_text += "• Your heart rate shows normal variability across sessions.<br>"
        else:
            analysis_text += "• Your heart rate shows high variability - consider tracking factors like activity, stress, or time of day.<br>"
        
        self.analysis_label.setText(analysis_text)


