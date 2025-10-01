from PyQt5 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
import numpy as np
from datetime import datetime

from ppg_health_monitor.utils.plot_style_helper import PlotStyleHelper
from ppg_health_monitor.utils.session_info_formatter import SessionInfoFormatter


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
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
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
        self.summary_label.setStyleSheet("padding: 15px; background-color: #f8f9fa; border-radius: 5px;")

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
            "Date", "Duration", "Avg BPM", "Min BPM", "Max BPM",
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
        
        self.plot = pg.PlotWidget()
        PlotStyleHelper.configure_plot_widget(
            self.plot,
            title="",
            x_label="BPM Range",
            x_units="",
            y_label="Frequency",
            y_units="",
            grid=True,
            mouse_enabled=False,
            menu_enabled=False
        )
        layout.addWidget(self.plot)
        
        # Analysis text
        self.analysis_label = QtWidgets.QLabel("")
        self.analysis_label.setStyleSheet(
            "padding: 10px; background-color: #e8f4f8; border-radius: 5px; margin: 5px;"
        )
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
        """Update all history views when user data changes."""
        # Get logged in user history
        user_data = self.user_manager.users[self.current_user]
        history = user_data.get("history", [])

        # User has no history - first session
        if not history:
            self.summary_label.setText(
                "No session data available yet. Start recording to build your health history!"
            )
            self.history_table.setRowCount(0)
            self.plot.clear()
            self.analysis_label.setText("")
            return
        
        # Update all components
        self.update_summary(user_data, history)
        self.update_history_table(history)
        self.update_plot(history)

    def update_summary(self, user_data, history):
        """Update the health summary using SessionInfoFormatter for consistency."""
        total_sessions = len(history)
        total_duration = sum(session.get("duration_minutes", 0) for session in history)
        
        # Collect BPM data and abnormal counts
        all_bpms = []
        all_low_count = 0
        all_high_count = 0
        
        for session in history:
            avg_bpm = session.get("avg_bpm", 0)
            if avg_bpm > 0:
                all_bpms.append(avg_bpm)
            all_low_count += session.get("abnormal_low", 0)
            all_high_count += session.get("abnormal_high", 0)
        
        if all_bpms:
            # Calculate statistics
            stats = SessionInfoFormatter.calculate_session_stats(all_bpms)
            overall_avg = stats['avg']
            overall_min = stats['min']
            overall_max = stats['max']
            
            # Get health status
            health_status, status_color = SessionInfoFormatter.format_bpm_status(
                overall_avg,
                low_threshold=40,
                high_threshold=200
            )
            
            # Format duration
            total_duration_formatted = SessionInfoFormatter.format_duration(total_duration)
            avg_session_duration = SessionInfoFormatter.format_duration(total_duration / total_sessions)
            
            summary_text = f"""
                <div style='line-height: 1.6;'>
                <b style='font-size: 14px; color: {status_color};'>Overall Health Status: {health_status}</b><br><br>
                
                <b>📊 Session Statistics:</b><br>
                • Total Sessions: {total_sessions}<br>
                • Total Recording Time: {total_duration_formatted}<br>
                • Average Session Length: {avg_session_duration}<br><br>
                
                <b>❤️ Heart Rate Metrics:</b><br>
                • Average BPM: {overall_avg:.1f}<br>
                • Range: {overall_min:.1f} - {overall_max:.1f} BPM<br>
                
                <b>⚠️ Abnormal Readings:</b><br>
                • Low Readings (&lt;40 BPM): {all_low_count}<br>
                • High Readings (&gt;200 BPM): {all_high_count}<br>
                • Total Abnormal: {all_low_count + all_high_count}
                </div>
                """
            
            # Add recent trend analysis
            if len(history) >= 2:
                recent_sessions = history[-3:]
                older_sessions = history[:-3] if len(history) > 3 else history[:1]
                
                recent_bpms = [s.get("avg_bpm", 0) for s in recent_sessions if s.get("avg_bpm", 0) > 0]
                older_bpms = [s.get("avg_bpm", 0) for s in older_sessions if s.get("avg_bpm", 0) > 0]
                
                if recent_bpms and older_bpms:
                    recent_avg = np.mean(recent_bpms)
                    older_avg = np.mean(older_bpms)
                    
                    trend = "stable"
                    if recent_avg > older_avg + 5:
                        trend = "increasing"
                    elif recent_avg < older_avg - 5:
                        trend = "decreasing"
                    
                    summary_text += (
                        f"<br><b>Recent Trend:</b> Your heart rate appears to be {trend} "
                        f"compared to earlier sessions."
                    )
        else:
            summary_text = "No valid BPM data recorded yet."
        
        self.summary_label.setText(summary_text)
    
    def update_history_table(self, history):
        """Update the session history table using SessionInfoFormatter for date formatting."""
        self.history_table.setRowCount(len(history))

        for i, session in enumerate(reversed(history)):
            # Format date
            date_str = SessionInfoFormatter.format_datetime(session["start"])
            
            # Get session data
            duration = session.get("duration_minutes", 0)
            avg_bpm = session.get("avg_bpm", 0)
            min_bpm = session.get("min_bpm", 0)
            max_bpm = session.get("max_bpm", 0)

            abnormal_low = session.get("abnormal_low", 0)
            abnormal_high = session.get("abnormal_high", 0)
            abnormal_text = f"Low: {abnormal_low}, High: {abnormal_high}"

            low_thresh = session.get("bpm_low_threshold", 40)
            high_thresh = session.get("bpm_high_threshold", 200)

            # Format duration for display
            duration_str = SessionInfoFormatter.format_duration(duration)

            # Set table items
            self.history_table.setItem(i, 0, QtWidgets.QTableWidgetItem(date_str))
            self.history_table.setItem(i, 1, QtWidgets.QTableWidgetItem(duration_str))
            self.history_table.setItem(i, 2, QtWidgets.QTableWidgetItem(f"{avg_bpm:.1f}"))
            self.history_table.setItem(i, 3, QtWidgets.QTableWidgetItem(f"{min_bpm:.1f}"))
            self.history_table.setItem(i, 4, QtWidgets.QTableWidgetItem(f"{max_bpm:.1f}"))
            self.history_table.setItem(i, 5, QtWidgets.QTableWidgetItem(abnormal_text))
            self.history_table.setItem(i, 6, QtWidgets.QTableWidgetItem(str(low_thresh)))
            self.history_table.setItem(i, 7, QtWidgets.QTableWidgetItem(str(high_thresh)))

            # Highlight rows with abnormal readings
            if abnormal_low > 0 or abnormal_high > 0:
                for col in range(8):
                    item = self.history_table.item(i, col)
                    if item:
                        item.setBackground(QtGui.QColor(255, 235, 235))
    
    def update_plot(self, history):
        """Update the BPM distribution histogram plot."""
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
        x_labels = [f"{bins[i]:.0f}-{bins[i+1]:.0f}" for i in range(len(bins)-1)]
        
        # Create bar colors based on BPM ranges
        bar_colors = self._get_bar_colors(bins)
        
        # Create the bar plot
        bar_plot = pg.BarGraphItem(
            x=x_pos, 
            height=hist, 
            width=0.8, 
            brushes=bar_colors,
            pen={'color': 'black', 'width': 1}
        )
        self.plot.addItem(bar_plot)
        
        # Update plot
        PlotStyleHelper.configure_plot_widget(
            self.plot,
            title='Distribution of Average BPM Across Sessions',
            x_label="BPM Range",
            x_units="", 
            y_label="Number of Sessions",
            y_units="",
            grid=True, 
            mouse_enabled=False,
            menu_enabled=False   
        )
        
        # Set x-axis ticks and labels
        x_ticks = [(i, label) for i, label in enumerate(x_labels)]
        self.plot.getAxis('bottom').setTicks([x_ticks])
        
        # Set axis ranges to prevent weird scaling
        self.plot.setXRange(-0.5, len(hist) - 0.5)
        self.plot.setYRange(0, max(hist) * 1.1 if max(hist) > 0 else 1)
        
        # Generate and display analysis
        self._update_analysis(all_bpms)
    
    def _get_bar_colors(self, bins):
        """
        Generate color array for histogram bars based on BPM health zones.
        
        Args:
            bins: Histogram bin edges
            
        Returns:
            list: List of color tuples (R, G, B, A)
        """
        bar_colors = []
        for i in range(len(bins) - 1):
            bin_center = (bins[i] + bins[i+1]) / 2
            if bin_center < 40:
                bar_colors.append((255, 0, 0, 150))      # Red - Very low
            elif bin_center < 60:
                bar_colors.append((255, 165, 0, 150))    # Orange - Low
            elif bin_center <= 100:
                bar_colors.append((0, 128, 0, 150))      # Green - Normal
            elif bin_center <= 200:
                bar_colors.append((255, 165, 0, 150))    # Orange - High
            else:
                bar_colors.append((255, 0, 0, 150))      # Red - Very high
        return bar_colors
    
    def _update_analysis(self, all_bpms):
        """
        Generate and display BPM distribution analysis using SessionInfoFormatter.
        
        Args:
            all_bpms: List of all BPM values from sessions
        """
        # Calculate statistics
        stats = SessionInfoFormatter.calculate_session_stats(all_bpms)
        
        avg_bpm = stats['avg']
        std_bpm = stats['std']
        min_bpm = stats['min']
        max_bpm = stats['max']
        
        # Count readings in different zones
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
        
        # Add health recommendations based on normal range percentage
        normal_percentage = normal_count / len(all_bpms)
        if normal_percentage > 0.8:
            analysis_text += "• Excellent: Most of your readings are in the normal range!<br>"
        elif normal_percentage > 0.6:
            analysis_text += "• Good: Majority of your readings are normal. Monitor any patterns.<br>"
        else:
            analysis_text += "• Attention: Consider consulting a healthcare provider about your readings.<br>"
        
        # Add specific warnings for abnormal readings
        if low_count > 0:
            analysis_text += (
                f"• You have {low_count} readings below 40 BPM - "
                f"this may indicate bradycardia.<br>"
            )
        
        if high_count > 0:
            analysis_text += (
                f"• You have {high_count} readings above 200 BPM - "
                f"this may indicate tachycardia.<br>"
            )
        
        # Variability assessment
        if std_bpm < 5:
            analysis_text += "• Your heart rate is very consistent across sessions.<br>"
        elif std_bpm < 15:
            analysis_text += "• Your heart rate shows normal variability across sessions.<br>"
        else:
            analysis_text += (
                "• Your heart rate shows high variability - consider tracking factors "
                "like activity, stress, or time of day.<br>"
            )
        
        self.analysis_label.setText(analysis_text)