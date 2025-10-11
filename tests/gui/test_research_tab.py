
import pytest
from unittest.mock import Mock
import numpy as np
import pandas as pd
from gui.ui_tabs.research_tab import ResearchTab

@pytest.fixture
def user_manager():
    """Create a mock user manager with sample session data."""
    manager = Mock()
    manager.users = {
        "testuser": {
            "history": [
                {
                    "start": "2023-01-01T10:00:00",
                    "duration": 60,
                    "raw_ppg": list(np.sin(np.linspace(0, 10 * np.pi, 3000)))
                }
            ]
        }
    }
    return manager

@pytest.fixture
def widget(qtbot, user_manager):
    """Create an instance of the widget."""
    widget = ResearchTab()
    qtbot.addWidget(widget)
    widget.start_session("testuser", user_manager)
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