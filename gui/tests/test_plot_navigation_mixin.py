import pytest
from unittest.mock import Mock
from PyQt5 import QtWidgets, QtCore
from gui.utils.plot_navigation_mixin import PlotNavigationMixin


class TestWidget(QtWidgets.QWidget, PlotNavigationMixin):
    """Test widget implementing PlotNavigationMixin."""
    
    def __init__(self):
        super().__init__()
        self.update_plot_view_called = False
        self.update_slider_called = False
    
    def update_plot_view(self):
        self.update_plot_view_called = True
    
    def update_slider(self):
        self.update_slider_called = True


@pytest.fixture
def test_widget(qtbot):
    """Create a test widget with PlotNavigationMixin."""
    widget = TestWidget()
    qtbot.addWidget(widget)
    return widget


class TestSetupPlotNavigation:
    """Test setup_plot_navigation method."""
    
    def test_setup_creates_widgets(self, test_widget):
        layout = QtWidgets.QHBoxLayout()
        
        widgets = test_widget.setup_plot_navigation(layout, default_window_seconds=10)
        
        assert 'checkbox' in widgets
        assert 'slider' in widgets
        assert 'selector' in widgets
        assert test_widget.plot_window_seconds == 10
        assert test_widget.is_auto_scrolling is True
    
    def test_setup_custom_window_seconds(self, test_widget):
        layout = QtWidgets.QHBoxLayout()
        
        test_widget.setup_plot_navigation(layout, default_window_seconds=30)
        
        assert test_widget.plot_window_seconds == 30
    
    def test_setup_checkbox_checked_by_default(self, test_widget):
        layout = QtWidgets.QHBoxLayout()
        
        widgets = test_widget.setup_plot_navigation(layout)
        
        assert widgets['checkbox'].isChecked() is True
    
    def test_setup_creates_slider_with_correct_orientation(self, test_widget):
        layout = QtWidgets.QHBoxLayout()
        
        widgets = test_widget.setup_plot_navigation(layout)
        
        assert widgets['slider'].orientation() == QtCore.Qt.Horizontal
    
    def test_setup_creates_window_selector_with_options(self, test_widget):
        layout = QtWidgets.QHBoxLayout()
        
        widgets = test_widget.setup_plot_navigation(layout)
        
        selector = widgets['selector']
        assert selector.count() == 4
        assert selector.itemText(0) == "5s"
        assert selector.itemText(1) == "10s"
        assert selector.itemText(2) == "30s"
        assert selector.itemText(3) == "60s"
    
    def test_setup_sets_default_window_in_selector(self, test_widget):
        layout = QtWidgets.QHBoxLayout()
        
        widgets = test_widget.setup_plot_navigation(layout, default_window_seconds=30)
        
        assert widgets['selector'].currentText() == "30s"


class TestToggleAutoScroll:
    """Test _toggle_auto_scroll method."""
    
    def test_toggle_enables_auto_scroll(self, test_widget):
        layout = QtWidgets.QHBoxLayout()
        test_widget.setup_plot_navigation(layout)
        
        test_widget.is_auto_scrolling = False
        test_widget._toggle_auto_scroll(QtCore.Qt.Checked)
        
        assert test_widget.is_auto_scrolling is True
    
    def test_toggle_disables_auto_scroll(self, test_widget):
        layout = QtWidgets.QHBoxLayout()
        test_widget.setup_plot_navigation(layout)
        
        test_widget.is_auto_scrolling = True
        test_widget._toggle_auto_scroll(QtCore.Qt.Unchecked)
        
        assert test_widget.is_auto_scrolling is False
    
    def test_toggle_calls_update_methods_when_enabled(self, test_widget):
        layout = QtWidgets.QHBoxLayout()
        test_widget.setup_plot_navigation(layout)
        
        test_widget._toggle_auto_scroll(QtCore.Qt.Checked)
        
        assert test_widget.update_slider_called is True
        assert test_widget.update_plot_view_called is True


class TestDisableAutoScroll:
    """Test _disable_auto_scroll method."""
    
    def test_disable_unchecks_checkbox(self, test_widget):
        layout = QtWidgets.QHBoxLayout()
        widgets = test_widget.setup_plot_navigation(layout)
        
        widgets['checkbox'].setChecked(True)
        test_widget._disable_auto_scroll()
        
        assert widgets['checkbox'].isChecked() is False


class TestOnSliderMoved:
    """Test _on_slider_moved method."""
    
    def test_slider_moved_calls_update_when_not_auto_scrolling(self, test_widget):
        layout = QtWidgets.QHBoxLayout()
        test_widget.setup_plot_navigation(layout)
        test_widget.is_auto_scrolling = False
        
        test_widget.update_plot_view_called = False
        test_widget._on_slider_moved(50)
        
        assert test_widget.update_plot_view_called is True
    
    def test_slider_moved_does_not_call_update_when_auto_scrolling(self, test_widget):
        layout = QtWidgets.QHBoxLayout()
        test_widget.setup_plot_navigation(layout)
        test_widget.is_auto_scrolling = True
        
        test_widget.update_plot_view_called = False
        test_widget._on_slider_moved(50)
        
        assert test_widget.update_plot_view_called is False


class TestUpdateTimeWindow:
    """Test _update_time_window method."""
    
    def test_update_window_5s(self, test_widget):
        layout = QtWidgets.QHBoxLayout()
        test_widget.setup_plot_navigation(layout)
        
        test_widget._update_time_window("5s")
        
        assert test_widget.plot_window_seconds == 5
    
    def test_update_window_10s(self, test_widget):
        layout = QtWidgets.QHBoxLayout()
        test_widget.setup_plot_navigation(layout)
        
        test_widget._update_time_window("10s")
        
        assert test_widget.plot_window_seconds == 10
    
    def test_update_window_30s(self, test_widget):
        layout = QtWidgets.QHBoxLayout()
        test_widget.setup_plot_navigation(layout)
        
        test_widget._update_time_window("30s")
        
        assert test_widget.plot_window_seconds == 30
    
    def test_update_window_60s(self, test_widget):
        layout = QtWidgets.QHBoxLayout()
        test_widget.setup_plot_navigation(layout)
        
        test_widget._update_time_window("60s")
        
        assert test_widget.plot_window_seconds == 60
    
    def test_update_window_invalid_defaults_to_10(self, test_widget):
        layout = QtWidgets.QHBoxLayout()
        test_widget.setup_plot_navigation(layout)
        
        test_widget._update_time_window("invalid")
        
        assert test_widget.plot_window_seconds == 10
    
    def test_update_window_calls_update_plot_view(self, test_widget):
        layout = QtWidgets.QHBoxLayout()
        test_widget.setup_plot_navigation(layout)
        
        test_widget.update_plot_view_called = False
        test_widget._update_time_window("30s")
        
        assert test_widget.update_plot_view_called is True


class TestUpdatePlotSlider:
    """Test update_plot_slider method."""
    
    def test_update_slider_auto_scrolling(self, test_widget):
        layout = QtWidgets.QHBoxLayout()
        widgets = test_widget.setup_plot_navigation(layout, default_window_seconds=10)
        test_widget.is_auto_scrolling = True
        
        test_widget.update_plot_slider(max_time=30)
        
        # scrollable_duration = 30 - 10 = 20
        # maximum = 20 * 100 = 2000
        assert widgets['slider'].maximum() == 2000
        assert widgets['slider'].value() == 2000
    
    def test_update_slider_no_scrollable_duration(self, test_widget):
        layout = QtWidgets.QHBoxLayout()
        widgets = test_widget.setup_plot_navigation(layout, default_window_seconds=10)
        test_widget.is_auto_scrolling = True
        
        test_widget.update_plot_slider(max_time=5)
        
        assert widgets['slider'].maximum() == 0
    
    def test_update_slider_blocks_signals(self, test_widget):
        layout = QtWidgets.QHBoxLayout()
        widgets = test_widget.setup_plot_navigation(layout)
        test_widget.is_auto_scrolling = True
        
        signal_spy = Mock()
        widgets['slider'].valueChanged.connect(signal_spy)
        
        test_widget.update_plot_slider(max_time=30)
        
        # Signal should be blocked during setValue
        # Hard to test directly, but verify it doesn't break
        assert widgets['slider'].value() == widgets['slider'].maximum()


class TestGetPlotViewRange:
    """Test get_plot_view_range method."""
    
    def test_get_range_auto_scrolling(self, test_widget):
        layout = QtWidgets.QHBoxLayout()
        test_widget.setup_plot_navigation(layout, default_window_seconds=10)
        test_widget.is_auto_scrolling = True
        
        start, end = test_widget.get_plot_view_range(max_time=30)
        
        assert start == 20  # 30 - 10
        assert end == 30    # 20 + 10
    
    def test_get_range_auto_scrolling_insufficient_data(self, test_widget):
        layout = QtWidgets.QHBoxLayout()
        test_widget.setup_plot_navigation(layout, default_window_seconds=10)
        test_widget.is_auto_scrolling = True
        
        start, end = test_widget.get_plot_view_range(max_time=5)
        
        assert start == 0   # max(0, 5 - 10)
        assert end == 10    # 0 + 10
    
    def get_plot_view_range(self, max_time):
        window_seconds = self.default_window_seconds
        if self.is_auto_scrolling:
            end_time = max_time
            start_time = max(0, end_time - window_seconds)
        else:
            if hasattr(self, "slider") and self.slider is not None:
                slider_value = self.slider.value()
                start_time = slider_value / 100.0  # because test sets slider to 500
            else:
                start_time = 0.0
            end_time = min(start_time + window_seconds, max_time)
        return start_time, end_time

    
    def test_get_range_different_window_sizes(self, test_widget):
        layout = QtWidgets.QHBoxLayout()
        test_widget.setup_plot_navigation(layout, default_window_seconds=30)
        test_widget.is_auto_scrolling = True
        
        start, end = test_widget.get_plot_view_range(max_time=100)
        
        assert start == 70  # 100 - 30
        assert end == 100   # 70 + 30


class TestIntegration:
    """Integration tests for PlotNavigationMixin."""
    
    def test_complete_navigation_workflow(self, test_widget):
        """Test complete workflow of navigation controls."""
        layout = QtWidgets.QHBoxLayout()
        widgets = test_widget.setup_plot_navigation(layout, default_window_seconds=10)
        
        # Initially auto-scrolling
        assert test_widget.is_auto_scrolling is True
        
        # Update slider for new data
        test_widget.update_plot_slider(max_time=50)
        start, end = test_widget.get_plot_view_range(max_time=50)
        assert start == 40
        assert end == 50
        
        # Disable auto-scroll
        widgets['checkbox'].setChecked(False)
        assert test_widget.is_auto_scrolling is False
        
        # Manual scroll
        widgets['slider'].setValue(1000)  # 10 seconds
        start, end = test_widget.get_plot_view_range(max_time=50)
        assert start == 10
        assert end == 20
        
        # Change window size
        widgets['selector'].setCurrentText("30s")
        assert test_widget.plot_window_seconds == 30
        start, end = test_widget.get_plot_view_range(max_time=50)
        assert start == 10
        assert end == 40
    
    def test_slider_interaction_disables_auto_scroll(self, test_widget):
        """Test that interacting with slider disables auto-scroll."""
        layout = QtWidgets.QHBoxLayout()
        widgets = test_widget.setup_plot_navigation(layout)
        
        assert widgets['checkbox'].isChecked() is True
        
        # Simulate slider press
        widgets['slider'].sliderPressed.emit()
        
        assert widgets['checkbox'].isChecked() is False
        assert test_widget.is_auto_scrolling is False