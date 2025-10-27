from PyQt5 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
import numpy as np
from datetime import datetime

from gui.utils import (
    PlotStyleHelper,
    SessionInfoFormatter
)


class HistoryTab(QtWidgets.QWidget):
    """
    Modernised history tab with tabbed navigation, filtering, and enhanced UX.
    """
    BPM_LOW_ABNORMAL = 40
    BPM_LOW_NORMAL = 60
    BPM_HIGH_NORMAL = 100
    BPM_HIGH_ABNORMAL = 200

    SORT_OPTIONS = {
        "Date (Newest)": (lambda s: s["start"], True),
        "Date (Oldest)": (lambda s: s["start"], False),
        "Avg BPM (High-Low)": (lambda s: s.get("avg_bpm", 0), True),
        "Avg BPM (Low-High)": (lambda s: s.get("avg_bpm", 0), False),
        "Duration (Long-Short)": (lambda s: s.get("duration_minutes", 0), True),
        "Duration (Short-Long)": (lambda s: s.get("duration_minutes", 0), False),
    }

    def __init__(self):
        super().__init__()
        self.current_user = None
        self.user_manager = None
        self.all_sessions = []  # Store a clean copy of the user's history
        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout()

        title = QtWidgets.QLabel("Health Monitor")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin: 12px;")
        layout.addWidget(title)

        self.tabs = QtWidgets.QTabWidget()

        # Overview tab
        self.overview_tab = QtWidgets.QWidget()
        scroll = QtWidgets.QScrollArea()
        scroll_widget = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout()

        self.summary_widget = self.create_summary_widget()
        scroll_layout.addWidget(self.summary_widget)

        self.plot_widget = self.create_plot_widget()
        scroll_layout.addWidget(self.plot_widget)

        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)

        overview_layout = QtWidgets.QVBoxLayout()
        overview_layout.addWidget(scroll)
        self.overview_tab.setLayout(overview_layout)
        self.tabs.addTab(self.overview_tab, "Overview")

        # History tab
        self.history_tab = QtWidgets.QWidget()
        history_layout = QtWidgets.QHBoxLayout()
        self.filter_widget = self.create_filter_widget()
        self.history_widget = self.create_history_widget()
        history_layout.addWidget(self.filter_widget, stretch=0)
        history_layout.addWidget(self.history_widget, stretch=1)
        self.history_tab.setLayout(history_layout)
        self.tabs.addTab(self.history_tab, "History")

        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def create_summary_widget(self):
        widget = QtWidgets.QGroupBox("Health Summary")
        layout = QtWidgets.QVBoxLayout()
        self.summary_label = QtWidgets.QLabel("Please log in to view your health summary")
        self.summary_label.setStyleSheet("padding: 15px; background-color: #f8f9fa; border-radius: 5px;")
        layout.addWidget(self.summary_label)
        widget.setLayout(layout)
        return widget

    def create_filter_widget(self):
        widget = QtWidgets.QGroupBox("Filter Sessions")
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(12)

        def add_spinbox_row(label_text, min_val, max_val, default, callback):
            row = QtWidgets.QHBoxLayout()
            row.addWidget(QtWidgets.QLabel(label_text))
            spin = QtWidgets.QSpinBox()
            spin.setRange(min_val, max_val)
            spin.setValue(default)
            spin.valueChanged.connect(callback)
            row.addWidget(spin)
            return row, spin

        # Date Range
        layout.addWidget(QtWidgets.QLabel("<b>Date Range</b>", textFormat=QtCore.Qt.RichText))
        date_row = QtWidgets.QHBoxLayout()
        self.from_date = QtWidgets.QDateEdit(calendarPopup=True)
        self.from_date.setDate(QtCore.QDate.currentDate().addMonths(-1))
        self.from_date.setDisplayFormat("yyyy-MM-dd")
        self.from_date.dateChanged.connect(self.apply_filters)
        self.to_date = QtWidgets.QDateEdit(calendarPopup=True)
        self.to_date.setDate(QtCore.QDate.currentDate())
        self.to_date.setDisplayFormat("yyyy-MM-dd")
        self.to_date.dateChanged.connect(self.apply_filters)
        for lbl, widget_item in [("From:", self.from_date), ("To:", self.to_date)]:
            date_row.addWidget(QtWidgets.QLabel(lbl))
            date_row.addWidget(widget_item)
            date_row.addSpacing(8)
        layout.addLayout(date_row)

        # BPM Range
        layout.addWidget(QtWidgets.QLabel("<b>BPM Range</b>", textFormat=QtCore.Qt.RichText))
        bpm_row = QtWidgets.QHBoxLayout()
        _, self.min_bpm_spin = add_spinbox_row("Min:", 30, 250, self.BPM_LOW_ABNORMAL, self.apply_filters)
        bpm_row.addLayout(_)
        bpm_row.addSpacing(8)
        _, self.max_bpm_spin = add_spinbox_row("Max:", 30, 250, self.BPM_HIGH_ABNORMAL, self.apply_filters)
        bpm_row.addLayout(_)
        layout.addLayout(bpm_row)

        # Duration
        layout.addWidget(QtWidgets.QLabel("<b>Session Duration (min)</b>", textFormat=QtCore.Qt.RichText))
        dur_row = QtWidgets.QHBoxLayout()
        _, self.min_duration_spin = add_spinbox_row("Min:", 0, 600, 0, self.apply_filters)
        dur_row.addLayout(_)
        dur_row.addSpacing(8)
        _, self.max_duration_spin = add_spinbox_row("Max:", 1, 600, 600, self.apply_filters)
        dur_row.addLayout(_)
        layout.addLayout(dur_row)

        # Other Filters
        layout.addWidget(QtWidgets.QLabel("<b>Other Filters</b>", textFormat=QtCore.Qt.RichText))
        self.abnormal_only_checkbox = QtWidgets.QCheckBox("Show only sessions with abnormal readings")
        self.abnormal_only_checkbox.stateChanged.connect(self.apply_filters)
        layout.addWidget(self.abnormal_only_checkbox)

        sort_row = QtWidgets.QHBoxLayout()
        sort_row.addWidget(QtWidgets.QLabel("Sort By:"))
        self.sort_by_combo = QtWidgets.QComboBox()
        self.sort_by_combo.addItems(self.SORT_OPTIONS.keys())
        self.sort_by_combo.currentIndexChanged.connect(self.apply_filters)
        sort_row.addWidget(self.sort_by_combo)
        layout.addLayout(sort_row)

        layout.addStretch()
        self.reset_button = QtWidgets.QPushButton("Reset Filters")
        self.reset_button.clicked.connect(self.reset_filters)
        layout.addWidget(self.reset_button, alignment=QtCore.Qt.AlignLeft)

        widget.setLayout(layout)
        return widget

    def create_history_widget(self):
        widget = QtWidgets.QGroupBox("Session History")
        layout = QtWidgets.QVBoxLayout()
        self.history_table = QtWidgets.QTableWidget()
        headers = ["Date", "Duration", "Avg BPM", "Min BPM", "Max BPM", "Abnormal Readings", "Low Threshold", "High Threshold"]
        self.history_table.setColumnCount(len(headers))
        self.history_table.setHorizontalHeaderLabels(headers)
        header = self.history_table.horizontalHeader()
        header.setStretchLastSection(True)
        for i in range(len(headers)):
            header.setSectionResizeMode(i, QtWidgets.QHeaderView.Stretch)
        layout.addWidget(self.history_table)
        widget.setLayout(layout)
        return widget

    def create_plot_widget(self):
        widget = QtWidgets.QGroupBox("BPM Distribution Analysis")
        layout = QtWidgets.QVBoxLayout()
        self.plot = pg.PlotWidget()
        PlotStyleHelper.configure_plot_widget(
            self.plot, title='', x_label="BPM Range", y_label="Frequency",
            grid=True, mouse_enabled=False, menu_enabled=False
        )
        layout.addWidget(self.plot)
        self.analysis_label = QtWidgets.QLabel("")
        self.analysis_label.setStyleSheet("padding: 10px; background-color: #e8f4f8; border-radius: 5px; margin: 5px;")
        self.analysis_label.setWordWrap(True)
        layout.addWidget(self.analysis_label)
        widget.setLayout(layout)
        return widget
    
    @staticmethod
    def _parse_session_date(start_date):
        """Helper to consistently parse date from session data."""
        return datetime.fromisoformat(str(start_date).replace('Z', '+00:00')).date()

    def apply_filters(self):
        if not self.all_sessions:
            self.update_history_table([])
            return

        from_dt = self.from_date.date().toPyDate()
        to_dt = self.to_date.date().toPyDate()
        min_bpm, max_bpm = self.min_bpm_spin.value(), self.max_bpm_spin.value()
        min_duration, max_duration = self.min_duration_spin.value(), self.max_duration_spin.value()
        abnormal_only = self.abnormal_only_checkbox.isChecked()
        sort_by = self.sort_by_combo.currentText()

        filtered = []
        for session in self.all_sessions:
            session_date = self._parse_session_date(session.get("start"))
            if not session_date or not (from_dt <= session_date <= to_dt):
                continue
            
            avg_bpm = session.get("avg_bpm", 0)
            if not (min_bpm <= avg_bpm <= max_bpm):
                continue
            
            duration = session.get("duration_minutes", 0)
            if not (min_duration <= duration <= max_duration):
                continue
            
            if abnormal_only and session.get("abnormal_low", 0) == 0 and session.get("abnormal_high", 0) == 0:
                continue
            
            filtered.append(session)

        if sort_by in self.SORT_OPTIONS:
            key, reverse = self.SORT_OPTIONS[sort_by]
            filtered.sort(key=key, reverse=reverse)

        self.update_history_table(filtered)

    def reset_filters(self):
        self.from_date.setDate(QtCore.QDate.currentDate().addMonths(-1))
        self.to_date.setDate(QtCore.QDate.currentDate())
        self.min_bpm_spin.setValue(self.BPM_LOW_ABNORMAL)
        self.max_bpm_spin.setValue(self.BPM_HIGH_ABNORMAL)
        self.min_duration_spin.setValue(0)
        self.max_duration_spin.setValue(600)
        self.abnormal_only_checkbox.setChecked(False)
        self.sort_by_combo.setCurrentIndex(0)
        
        self.apply_filters()

    def start_session(self, username, user_manager):
        self.current_user = username
        self.user_manager = user_manager
        
        user_data = self.user_manager.users.get(self.current_user, {})
        # Store a clean, pre-processed copy of the history
        self.all_sessions = user_data.get("history", [])
        
        self.update_history_view()
        self.reset_filters()

    def update_history_view(self):
        if not self.all_sessions:
            self.summary_label.setText("No session data available yet. Start recording to build your health history!")
            self.history_table.setRowCount(0)
            self.plot.clear()
            self.analysis_label.setText("")
            return
        
        user_data = self.user_manager.users[self.current_user]
        self.update_summary(user_data, self.all_sessions)
        self.update_plot(self.all_sessions)
        self.apply_filters()

    def update_summary(self, user_data, history):
        total_sessions = len(history)
        total_duration = sum(session.get("duration_minutes", 0) for session in history)
        all_bpms = [s.get("avg_bpm", 0) for s in history if s.get("avg_bpm", 0) > 0]
        all_low_count = sum(s.get("abnormal_low", 0) for s in history)
        all_high_count = sum(s.get("abnormal_high", 0) for s in history)

        if not all_bpms:
            self.summary_label.setText("No valid BPM data recorded yet.")
            return

        stats = SessionInfoFormatter.calculate_session_stats(all_bpms)
        overall_avg, overall_min, overall_max = stats['avg'], stats['min'], stats['max']
        health_status, status_color = SessionInfoFormatter.format_bpm_status(overall_avg, self.BPM_LOW_ABNORMAL, self.BPM_HIGH_ABNORMAL)
        total_duration_formatted = SessionInfoFormatter.format_duration(total_duration)
        avg_session_duration = SessionInfoFormatter.format_duration(total_duration / total_sessions) if total_sessions > 0 else "N/A"

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
            • Low Readings (&lt;{self.BPM_LOW_ABNORMAL} BPM): {all_low_count}<br>
            • High Readings (>{self.BPM_HIGH_ABNORMAL} BPM): {all_high_count}<br>
            • Total Abnormal: {all_low_count + all_high_count}
            </div>
            """
        self.summary_label.setText(summary_text)

    def update_history_table(self, history):
        self.history_table.setRowCount(len(history))
        for i, session in enumerate(history):
            values = [
                SessionInfoFormatter.format_datetime(session["start"]),
                SessionInfoFormatter.format_duration(session.get("duration_minutes", 0)),
                f"{session.get('avg_bpm', 0):.1f}",
                f"{session.get('min_bpm', 0):.1f}",
                f"{session.get('max_bpm', 0):.1f}",
                f"Low: {session.get('abnormal_low', 0)}, High: {session.get('abnormal_high', 0)}",
                str(session.get("bpm_low_threshold", self.BPM_LOW_ABNORMAL)),
                str(session.get("bpm_high_threshold", self.BPM_HIGH_ABNORMAL))
            ]
            for col, val in enumerate(values):
                self.history_table.setItem(i, col, QtWidgets.QTableWidgetItem(val))
            
            if session.get("abnormal_low", 0) > 0 or session.get("abnormal_high", 0) > 0:
                for col in range(self.history_table.columnCount()):
                    item = self.history_table.item(i, col)
                    if item:
                        item.setBackground(QtGui.QColor(255, 235, 235))

    def update_plot(self, history):
        self.plot.clear()
        all_bpms = [s.get("avg_bpm", 0) for s in history if s.get("avg_bpm", 0) > 0]
        if not all_bpms:
            self.analysis_label.setText("No BPM data available for analysis.")
            return

        hist, bins = np.histogram(all_bpms, bins=20)
        x_pos = np.arange(len(hist))
        x_labels = [f"{bins[i]:.0f}-{bins[i+1]:.0f}" for i in range(len(bins)-1)]
        
        brushes = self._get_bar_colors(bins)
        bar_graph = pg.BarGraphItem(
            x=x_pos, height=hist, width=0.8,
            brushes=brushes, pen={'color': 'black', 'width': 1}
        )
        self.plot.addItem(bar_graph)

        PlotStyleHelper.configure_plot_widget(
            self.plot,
            title='Distribution of Average BPM Across Sessions',
            x_label="BPM Range", y_label="Number of Sessions",
            grid=True, mouse_enabled=False, menu_enabled=False
        )
        
        bottom_axis = self.plot.getAxis('bottom')
        bottom_axis.setTicks([[(i, label) for i, label in enumerate(x_labels)]])

        # Set y-axis ticks in increments of 1
        if hist.size > 0:
            max_sessions = int(max(hist))
            y_ticks = [(i, str(i)) for i in range(max_sessions + 2)]
            self.plot.getAxis('left').setTicks([y_ticks])

        self.plot.setXRange(-0.5, len(hist) - 0.5)
        self.plot.setYRange(0, max(hist) * 1.1 if max(hist) > 0 else 1)
        self._update_analysis(all_bpms)

    def _get_bar_colors(self, bins):
        colors = []
        for i in range(len(bins) - 1):
            center = (bins[i] + bins[i+1]) / 2
            if center < self.BPM_LOW_ABNORMAL:
                colors.append((255, 0, 0, 150))          # Red
            elif center < self.BPM_LOW_NORMAL:
                colors.append((255, 165, 0, 150))     # Orange
            elif center <= self.BPM_HIGH_NORMAL:
                colors.append((0, 128, 0, 150))        # Green
            elif center <= self.BPM_HIGH_ABNORMAL:
                colors.append((255, 165, 0, 150))     # Orange
            else:
                colors.append((255, 0, 0, 150))          # Red
        return colors

    def _update_analysis(self, all_bpms):
        stats = SessionInfoFormatter.calculate_session_stats(all_bpms)
        avg_bpm, std_bpm, min_bpm, max_bpm = stats['avg'], stats['std'], stats['min'], stats['max']
        
        low_count = sum(1 for bpm in all_bpms if bpm < self.BPM_LOW_ABNORMAL)
        high_count = sum(1 for bpm in all_bpms if bpm > self.BPM_HIGH_ABNORMAL)
        normal_count = sum(1 for bpm in all_bpms if self.BPM_LOW_NORMAL <= bpm <= self.BPM_HIGH_NORMAL)

        total_analyzed = len(all_bpms)
        analysis_text = f"""
            <b>BPM Distribution Analysis:</b><br>
            • Total Sessions Analyzed: {total_analyzed}<br>
            • Average BPM: {avg_bpm:.1f} ± {std_bpm:.1f}<br>
            • Range: {min_bpm:.1f} - {max_bpm:.1f} BPM<br><br>
            <b>Health Insights:</b><br>
            """

        if total_analyzed > 0:
            normal_percentage = normal_count / total_analyzed
            if normal_percentage > 0.8:
                analysis_text += "• Excellent: Most readings are in the normal range!<br>"
            elif normal_percentage > 0.6:
                analysis_text += "• Good: Majority are normal. Monitor patterns.<br>"
            else:
                analysis_text += "• Attention: Consider consulting a healthcare provider.<br>"

        if low_count > 0:
            analysis_text += f"• {low_count} readings below {self.BPM_LOW_ABNORMAL} BPM - may indicate bradycardia.<br>"
        if high_count > 0:
            analysis_text += f"• {high_count} readings above {self.BPM_HIGH_ABNORMAL} BPM - may indicate tachycardia.<br>"

        if std_bpm < 5:
            analysis_text += "• Heart rate is very consistent.<br>"
        elif std_bpm < 15:
            analysis_text += "• Heart rate shows normal variability.<br>"
        else:
            analysis_text += "• High variability - track activity, stress, or time of day.<br>"

        self.analysis_label.setText(analysis_text)