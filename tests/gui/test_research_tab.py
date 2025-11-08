"""
Test module for ResearchTab.

Author: Daniel Lindsay-Shad
Note: The Docstrings for methods were generated using Generative AI based on the method functionality.
"""


import pytest
from unittest.mock import Mock
import numpy as np
import pandas as pd
from gui.ui_tabs.research_tab import ResearchTab

@pytest.fixture
def widget(qtbot, mock_user_manager_with_raw_ppg):
    """Create an instance of the widget."""
    widget = ResearchTab()
    qtbot.addWidget(widget)
    widget.start_session("testuser", mock_user_manager_with_raw_ppg)
    return widget

def test_initial_state(widget):
    """Test the initial state of the widget after a session starts."""
    assert widget.current_user == "testuser"
    assert widget.session_selector.count() > 1

def test_load_selected_session(widget):
    """Test loading a session from the selector."""
    widget.session_selector.setCurrentIndex(1)
    assert len(widget.raw_ppg_signal) == 3000
    assert widget.time_axis.size > 0
    assert "Loaded session" in widget.status_text.toPlainText()

def test_apply_filter(widget):
    """Test applying a filter to the raw signal."""
    widget.session_selector.setCurrentIndex(1)
    widget.apply_filter()
    assert len(widget.filtered_ppg_signal) == 3000
    assert widget.filter_applied
    assert widget.control_tabs.isTabEnabled(2) # Analysis tab

def test_detect_peaks(widget):
    """Test detecting peaks in the filtered signal."""
    widget.session_selector.setCurrentIndex(1)
    widget.apply_filter()
    widget.detect_peaks()
    assert widget.peaks.size > 0
    assert "Detected" in widget.status_text.toPlainText()

def test_analyze_hrv(widget, mocker):
    """Test HRV analysis functionality."""
    # Set up widget state
    widget.session_selector.setCurrentIndex(1)
    widget.apply_filter()
    
    # Mock peak detection to return some peaks
    mock_peaks = np.array([100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200])
    mock_detect = mocker.patch('gui.ui_tabs.research_tab.SignalProcessingUtils.detect_ppg_peaks')
    mock_detect.return_value = (mock_peaks, {})
    widget.detect_peaks()
    
    # Mock the utility functions
    mock_hrv_result = {
        'HRV_VLF': [0.1],
        'HRV_LF': [0.2], 
        'HRV_HF': [0.3]
    }
    mock_rr = mocker.patch('gui.ui_tabs.research_tab.SignalProcessingUtils.calculate_rr_intervals')
    mock_time_domain = mocker.patch('gui.ui_tabs.research_tab.SignalProcessingUtils.calculate_hrv_time_domain')
    mock_hrv_frequency = mocker.patch('gui.ui_tabs.research_tab.nk.hrv_frequency')
    mock_rr.return_value = np.array([800, 820, 790, 810, 805, 815])  # 6 intervals
    mock_time_domain.return_value = {
        'mean_rr': 800, 'sdnn': 50, 'rmssd': 30, 'pnn50': 5, 'sd1': 20, 'sd2': 40, 'sd_ratio': 0.5
    }
    mock_hrv_frequency.return_value = pd.DataFrame(mock_hrv_result)
    widget.analyze_hrv()
    assert widget.hrv_metrics
    assert "HRV analysis completed" in widget.status_text.toPlainText()

def test_export_data(widget, mocker):
    """Test the data export functionality."""
    widget.session_selector.setCurrentIndex(1)
    widget.apply_filter()
    widget.detect_peaks()
    mock_dialog = mocker.patch('PyQt5.QtWidgets.QFileDialog.getSaveFileName')
    mock_msgbox = mocker.patch('PyQt5.QtWidgets.QMessageBox.information')
    mock_dialog.return_value = ("test_export.csv", "CSV Files (*.csv)")
    mock_to_csv = mocker.patch('pandas.DataFrame.to_csv')
    widget.export_data()
    mock_to_csv.assert_called()
    mock_msgbox.assert_called_once()


def test_design_butter_filter_and_response(widget, mocker):
    """Test filter design utilities and response plotting."""
    # Small signal to pass through update_filter_response
    b, a = widget.design_butter_filter(0.5, 2.0, 2, 'band')
    # patch filter_response_curve and filter_response_plot
    widget.filter_response_curve = mocker.Mock()
    widget.filter_response_plot = mocker.Mock()
    widget.update_filter_response(b, a)
    widget.filter_response_curve.setData.assert_called()


def test_calculate_data_quality_and_assess(widget, mocker):
    """Exercise calculate_data_quality and assess_signal_quality paths."""
    widget.session_selector.setCurrentIndex(1)
    # Ensure filtered signal exists
    widget.apply_filter()

    # Patch neurokit ppg_quality to return deterministic scores
    mocker.patch('gui.ui_tabs.research_tab.nk.ppg_quality', return_value=np.ones(100))
    widget.assess_signal_quality()
    assert 'overall_rating' in widget.signal_quality_metrics


def test_apply_butterworth_edge_highcut(widget, mocker):
    """Test apply_butterworth_filter reduces highcut if above Nyquist."""
    # set sliders that would produce a high cutoff above Nyquist
    widget.sampling_rate = 50
    widget.order_slider = mocker.Mock()
    widget.order_slider.value = lambda: 2
    widget.low_cutoff_slider = mocker.Mock()
    widget.low_cutoff_slider.value = lambda: 10
    widget.high_cutoff_slider = mocker.Mock()
    # Set an extremely high percentage to force reduction
    widget.high_cutoff_slider.value = lambda: 10000
    # patch the filter response plot update only to avoid GUI side-effects
    mocker.patch.object(widget, 'update_filter_response')

    # call with a short sample signal; let design_butter_filter compute real coeffs
    sig = np.linspace(0, 1, 500)
    out = widget.apply_butterworth_filter(sig)
    # filtfilt returns an array with same length
    assert out.shape[0] == sig.shape[0]


def test_log_status_appends_timestamp(widget):
    widget.status_text.clear()
    widget.log_status("Test message")
    assert "Test message" in widget.status_text.toPlainText()


def test_apply_filter_without_signal_logs_error(widget):
    widget.raw_ppg_signal = np.array([])
    widget.apply_filter()
    assert "No signal loaded" in widget.status_text.toPlainText()


def test_apply_filter_savgol_adjusts_window(widget):
    widget.raw_ppg_signal = np.linspace(0, 1, 50)
    idx = widget.filter_method_combo.findText("Savitzky–Golay FIR (Smoothing)")
    widget.filter_method_combo.setCurrentIndex(idx)
    widget.window_length_spin.setValue(3)
    widget.poly_order_spin.setValue(4)
    widget.apply_filter()
    assert widget.window_length_spin.value() > widget.poly_order_spin.value()


def test_apply_filter_none_returns_copy(widget):
    widget.raw_ppg_signal = np.array([1.0, 2.0, 3.0])
    idx = widget.filter_method_combo.findText("None (Raw Signal)")
    widget.filter_method_combo.setCurrentIndex(idx)
    widget.apply_filter()
    assert widget.filtered_ppg_signal.size == widget.raw_ppg_signal.size
    assert np.isclose(widget.filtered_ppg_signal.min(), 0.0)
    assert np.isclose(widget.filtered_ppg_signal.max(), 1.0)


def test_detect_peaks_requires_filtered_signal(widget, mocker):
    widget.filtered_ppg_signal = np.array([])
    mock_warning = mocker.patch('PyQt5.QtWidgets.QMessageBox.warning')
    widget.detect_peaks()
    mock_warning.assert_called_once()


def test_analyze_hrv_requires_min_peaks(widget, mocker):
    widget.peaks = np.array([1, 2, 3])
    mock_warning = mocker.patch('PyQt5.QtWidgets.QMessageBox.warning')
    widget.analyze_hrv()
    mock_warning.assert_called_once()


def test_analyze_hrv_insufficient_intervals(widget, mocker):
    widget.peaks = np.arange(10)
    widget.hrv_results = Mock()
    mocker.patch('gui.ui_tabs.research_tab.SignalProcessingUtils.calculate_rr_intervals', return_value=np.array([100, 110, 120, 130]))
    widget.analyze_hrv()
    widget.hrv_results.setText.assert_called_with('Error: Insufficient IBI intervals for analysis')


def test_analyze_hrv_invalid_time_domain(widget, mocker):
    widget.peaks = np.arange(12)
    widget.hrv_results = Mock()
    mocker.patch('gui.ui_tabs.research_tab.SignalProcessingUtils.calculate_rr_intervals', return_value=np.linspace(100, 200, 6))
    mocker.patch('gui.ui_tabs.research_tab.SignalProcessingUtils.calculate_hrv_time_domain', return_value={})
    widget.analyze_hrv()
    widget.hrv_results.setText.assert_called_with('Error: Insufficient valid IBI intervals for analysis')


def test_update_control_visibility_toggles_sections(widget, mocker):
    widget.butterworth_controls.setVisible = mocker.Mock()
    widget.savgol_controls.setVisible = mocker.Mock()
    widget.low_cutoff_widget.setVisible = mocker.Mock()
    widget.high_cutoff_widget.setVisible = mocker.Mock()

    idx = widget.filter_method_combo.findText("Butterworth Filter (Custom)")
    widget.filter_method_combo.setCurrentIndex(idx)
    widget.filter_type_combo.setCurrentText('Bandpass')
    widget.update_control_visibility()
    widget.butterworth_controls.setVisible.assert_called_with(True)
    widget.low_cutoff_widget.setVisible.assert_called_with(True)
    widget.high_cutoff_widget.setVisible.assert_called_with(True)

    idx = widget.filter_method_combo.findText("Savitzky–Golay FIR (Smoothing)")
    widget.filter_method_combo.setCurrentIndex(idx)
    widget.update_control_visibility()
    widget.savgol_controls.setVisible.assert_called_with(True)


def test_start_session_without_history(qtbot):
    manager = Mock()
    manager.users = {"empty": {"history": []}}
    widget = ResearchTab()
    qtbot.addWidget(widget)
    widget.start_session("empty", manager)
    assert widget.session_selector.count() == 1


def test_load_selected_session_index_zero_clears_data(widget):
    widget.load_selected_session(0)
    assert widget.raw_ppg_signal.size == 0
    assert not widget.filter_applied
    assert not widget.control_tabs.isTabEnabled(2)


def test_clear_all_data_resets_labels(widget):
    widget.clear_all_data()
    assert widget.samples_label.text() == "-"
    assert widget.metadata_label.text() == ""
    assert widget.hrv_metrics == {}


def test_update_plot_view_without_data(widget, mocker):
    widget.time_axis = np.array([])
    widget.original_plot.setXRange = mocker.Mock()
    widget.filtered_plot.setXRange = mocker.Mock()
    widget.hrv_plot.setXRange = mocker.Mock()
    widget.update_plot_view()
    widget.original_plot.setXRange.assert_not_called()


def test_update_plot_view_with_data(widget, mocker):
    widget.time_axis = np.linspace(0, 9, 10)
    widget.original_plot.setXRange = mocker.Mock()
    widget.filtered_plot.setXRange = mocker.Mock()
    widget.hrv_plot.setXRange = mocker.Mock()
    widget.get_plot_view_range = mocker.Mock(return_value=(0, 5))
    widget.update_plot_view()
    widget.original_plot.setXRange.assert_called_with(0, 5, padding=0)


def test_update_slider_handles_ranges(widget, mocker):
    widget.plot_slider.setMaximum = mocker.Mock()
    widget.time_axis = np.array([])
    widget.update_slider()
    widget.plot_slider.setMaximum.assert_called_with(0)

    widget.plot_slider.setMaximum.reset_mock()
    widget.time_axis = np.linspace(0, 9, 10)
    widget.update_plot_slider = mocker.Mock()
    widget.update_slider()
    widget.update_plot_slider.assert_called()


def test_export_data_cancelled(widget, mocker):
    widget.session_selector.setCurrentIndex(1)
    widget.apply_filter()
    widget.detect_peaks()
    mocker.patch('PyQt5.QtWidgets.QFileDialog.getSaveFileName', return_value=("", ""))
    mock_to_csv = mocker.patch('pandas.DataFrame.to_csv')
    widget.export_data()
    mock_to_csv.assert_not_called()