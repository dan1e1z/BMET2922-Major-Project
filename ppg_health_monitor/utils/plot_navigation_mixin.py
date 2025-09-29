from PyQt5 import QtWidgets, QtCore

class PlotNavigationMixin:
    """
    Mixin class providing common plot navigation controls.
    Use this for tabs that need auto-scroll, time window selection, and manual scrolling.
    """
    
    def setup_plot_navigation(self, parent_layout, default_window_seconds=10):
        """
        Create and add standard plot navigation controls to a layout.
        
        Args:
            parent_layout: QLayout to add controls to
            default_window_seconds: Default time window in seconds
            
        Returns:
            dict: Dictionary containing references to created widgets
        """
        self.plot_window_seconds = default_window_seconds
        self.is_auto_scrolling = True
        
        controls_layout = QtWidgets.QHBoxLayout()
        
        # Auto-scroll checkbox
        self.auto_scroll_checkbox = QtWidgets.QCheckBox("Auto-Scroll")
        self.auto_scroll_checkbox.setChecked(True)
        self.auto_scroll_checkbox.stateChanged.connect(self._toggle_auto_scroll)
        controls_layout.addWidget(self.auto_scroll_checkbox)
        
        # Manual scroll slider
        self.plot_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.plot_slider.setRange(0, 0)
        self.plot_slider.valueChanged.connect(self._on_slider_moved)
        self.plot_slider.sliderPressed.connect(self._disable_auto_scroll)
        controls_layout.addWidget(self.plot_slider)
        
        # Time window selector
        window_label = QtWidgets.QLabel("Time Window:")
        window_label.setStyleSheet("QLabel { font-weight: bold; }")
        self.window_selector = QtWidgets.QComboBox()
        self.window_selector.addItems(["5s", "10s", "30s", "60s"])
        self.window_selector.setCurrentText(f"{default_window_seconds}s")
        self.window_selector.currentTextChanged.connect(self._update_time_window)
        controls_layout.addWidget(window_label)
        controls_layout.addWidget(self.window_selector)
        
        parent_layout.addLayout(controls_layout)
        
        return {
            'checkbox': self.auto_scroll_checkbox,
            'slider': self.plot_slider,
            'selector': self.window_selector
        }
    
    def _toggle_auto_scroll(self, state):
        """Internal handler for auto-scroll toggle."""
        self.is_auto_scrolling = (state == QtCore.Qt.Checked)
        if self.is_auto_scrolling and hasattr(self, 'update_slider'):
            self.update_slider()
            if hasattr(self, 'update_plot_view'):
                self.update_plot_view()
    
    def _disable_auto_scroll(self):
        """Internal handler to disable auto-scroll on manual interaction."""
        self.auto_scroll_checkbox.setChecked(False)
    
    def _on_slider_moved(self, value):
        """Internal handler for slider movement."""
        if not self.is_auto_scrolling and hasattr(self, 'update_plot_view'):
            self.update_plot_view()
    
    def _update_time_window(self, window_text):
        """Internal handler for time window changes."""
        window_map = {"5s": 5, "10s": 10, "30s": 30, "60s": 60}
        self.plot_window_seconds = window_map.get(window_text, 10)
        if hasattr(self, 'update_plot_view'):
            self.update_plot_view()
    
    def update_plot_slider(self, max_time, current_view_start=None):
        """
        Update slider range and position based on data.
        
        Args:
            max_time: Maximum time value in the data
            current_view_start: Optional current view start position
        """
        if self.is_auto_scrolling:
            scrollable_duration = max(0, max_time - self.plot_window_seconds)
            
            if scrollable_duration > 0:
                self.plot_slider.setMaximum(int(scrollable_duration * 100))
                self.plot_slider.blockSignals(True)
                self.plot_slider.setValue(self.plot_slider.maximum())
                self.plot_slider.blockSignals(False)
            else:
                self.plot_slider.setMaximum(0)
    
    def get_plot_view_range(self, max_time):
        """
        Calculate the start and end time for plot view.
        
        Args:
            max_time: Maximum time in data
            
        Returns:
            tuple: (start_time, end_time)
        """
        if self.is_auto_scrolling:
            start_time = max(0, max_time - self.plot_window_seconds)
        else:
            start_time = self.plot_slider.value() / 100.0
        
        end_time = start_time + self.plot_window_seconds
        return start_time, end_time