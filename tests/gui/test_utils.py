import pytest
import numpy as np
from unittest.mock import Mock
import pyqtgraph as pg
from gui.utils import(
    DataValidationUtils,
    SignalProcessingUtils,
    SessionInfoFormatter,
    PlotStyleHelper
)


def test_validate_bpm_and_simple_metrics():
    assert DataValidationUtils.validate_bpm(60)
    assert not DataValidationUtils.validate_bpm(0)

    sig = np.array([1.0, 2.0, 3.0])
    m = DataValidationUtils.calculate_signal_quality_metrics(sig)
    assert m['samples'] == 3
    assert m['invalid_count'] == 0


def test_signal_processing_peak_and_rr():
    s = np.sin(np.linspace(0, 4 * np.pi, 200))
    cleaned = SignalProcessingUtils.clean_ppg_signal(s)
    peaks, info = SignalProcessingUtils.detect_ppg_peaks(cleaned, sampling_rate=50)
    # ensure function returns expected types
    assert isinstance(peaks, np.ndarray)
    assert isinstance(info, dict)

    rr = SignalProcessingUtils.calculate_rr_intervals(np.array([10, 60, 110]), sampling_rate=50)
    assert list(rr) == [1000, 1000]


def test_hrv_and_formatter():
    rr = np.array([1000, 1000, 1000])
    m = SignalProcessingUtils.calculate_hrv_time_domain(rr)
    assert 'heart_rate' in m

    assert SessionInfoFormatter.format_duration(1) == '1.0 min'


def test_plot_style_helper_smoke():
    mock_plot = Mock(spec=pg.PlotWidget)
    mock_plot.setTitle = Mock()
    mock_plot.setLabel = Mock()
    mock_plot.showGrid = Mock()
    mock_plot.setMouseEnabled = Mock()
    mock_plot.setMenuEnabled = Mock()
    mock_plot.enableAutoRange = Mock()
    mock_plot.addLegend = Mock(return_value=Mock())

    PlotStyleHelper.configure_plot_widget(mock_plot, title='t', x_label='x')
    PlotStyleHelper.auto_scale_y_axis(mock_plot, [0, 1], [0, 1], (0, 1))
    lg = PlotStyleHelper.create_legend(mock_plot)
    assert lg is not None


def test_signal_quality_empty_and_invalid_values():
    # empty signal returns empty dict
    assert DataValidationUtils.calculate_signal_quality_metrics(np.array([])) == {}

    # signal with NaN and Inf
    sig = np.array([0.0, np.nan, np.inf, 1.0])
    m = DataValidationUtils.calculate_signal_quality_metrics(sig)
    assert m['invalid_count'] >= 2


def test_filter_outliers_empty_and_small():
    empty = np.array([])
    assert DataValidationUtils.filter_outliers(empty).size == 0

    data = np.array([0.0, 0.0, 0.1, 100.0])
    filtered = DataValidationUtils.filter_outliers(data, n_std=1)
    assert len(filtered) < len(data)


def test_signal_processing_handles_neurokit_exceptions(mocker):
    # patch neurokit peaks to raise
    mocker.patch('gui.utils.signal_processing_utils.nk.ppg_peaks', side_effect=Exception('err'))
    peaks, info = SignalProcessingUtils.detect_ppg_peaks(np.zeros(10))
    assert isinstance(peaks, np.ndarray) and peaks.size == 0
    assert info == {}

    # patch neurokit clean to raise
    s = np.array([1.0, 2.0, 3.0])
    mocker.patch('gui.utils.signal_processing_utils.nk.ppg_clean', side_effect=Exception('err2'))
    out = SignalProcessingUtils.clean_ppg_signal(s)
    assert np.array_equal(out, s)


def test_session_info_formatter_branches():
    # format_bpm_status branches
    assert SessionInfoFormatter.format_bpm_status(30)[0].lower().startswith('below')
    assert SessionInfoFormatter.format_bpm_status(250)[0].lower().startswith('above')
    assert SessionInfoFormatter.format_bpm_status(55)[0].lower().startswith('below')
    assert SessionInfoFormatter.format_bpm_status(105)[0].lower().startswith('above')
    assert SessionInfoFormatter.format_bpm_status(80)[0] == 'Normal'

    # calculate_session_stats empty and no valid bpms
    assert SessionInfoFormatter.calculate_session_stats([])['count'] == 0
    assert SessionInfoFormatter.calculate_session_stats([0, -1])['count'] == 0


def test_calculate_hrv_time_domain_edge_cases():
    # very small rr array
    assert SignalProcessingUtils.calculate_hrv_time_domain(np.array([100.0])) == {}

    # rr values filtered out by valid_mask
    assert SignalProcessingUtils.calculate_hrv_time_domain(np.array([100.0, 150.0])) == {}


def test_additional_session_and_signal_utils():
    # SessionInfoFormatter tests
    assert SessionInfoFormatter.format_duration(0.5).endswith(' sec')
    assert 'min' in SessionInfoFormatter.format_duration(2)
    assert 'hrs' in SessionInfoFormatter.format_duration(120)

    ds = SessionInfoFormatter.format_datetime('2023-01-01T12:00:00')
    assert '2023-01-01' in ds
    assert SessionInfoFormatter.format_datetime('not-a-date') == 'not-a-date'

    assert SessionInfoFormatter.format_bpm_status(30)[0].lower().startswith('below')
    assert SessionInfoFormatter.format_bpm_status(150)[0].lower().startswith('above')
    stats = SessionInfoFormatter.calculate_session_stats([60, 70, 0, -1, 80])
    assert stats['count'] == 3

    # SignalProcessingUtils tests
    peaks = np.array([0, 50, 100, 150, 200])
    rr = SignalProcessingUtils.calculate_rr_intervals(peaks, sampling_rate=50)
    assert rr.size == 4
    assert np.allclose(rr, 1000.0)

    dup = np.array([1, 2, 2, 3, 3, 3])
    uniq = SignalProcessingUtils.remove_duplicate_peaks(dup)
    assert np.array_equal(uniq, np.array([1, 2, 3]))

    assert SignalProcessingUtils.calculate_hrv_time_domain(np.array([800])) == {}

    rr_intervals = np.array([800, 820, 810, 790, 805, 815, 800])
    metrics = SignalProcessingUtils.calculate_hrv_time_domain(rr_intervals)
    assert 'mean_rr' in metrics
    assert 'sdnn' in metrics


def test_additional_data_validation_utils():
    assert DataValidationUtils.validate_bpm(20)
    assert DataValidationUtils.validate_bpm(250)
    assert not DataValidationUtils.validate_bpm(10)
    assert not DataValidationUtils.validate_bpm(300)

    sig = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
    metrics = DataValidationUtils.calculate_signal_quality_metrics(sig)
    assert metrics['samples'] == 5
    assert 'snr_db' in metrics
    assert metrics['min'] == 0.0
    assert metrics['max'] == 4.0

    data = np.array([0.0, 0.1, 0.2, 50.0])
    filtered = DataValidationUtils.filter_outliers(data, n_std=1)
    assert isinstance(filtered, np.ndarray)
    assert len(filtered) < len(data)


def test_hrv_tooltip_utils():
    """Test HRVTooltipUtils functionality."""
    from gui.utils.hrv_tooltip_utils import HRVTooltipUtils
    
    # Test get_hrv_metric_tooltips
    tooltips = HRVTooltipUtils.get_hrv_metric_tooltips()
    assert isinstance(tooltips, dict)
    assert "Mean IBI" in tooltips
    assert "SDNN" in tooltips
    assert "RMSSD" in tooltips
    assert "<b>Normal:</b>" in tooltips["Mean IBI"]
    
    # Test get_hrv_metrics_definitions
    definitions = HRVTooltipUtils.get_hrv_metrics_definitions()
    assert isinstance(definitions, list)
    assert len(definitions) > 10
    
    # Check for section headers
    headers = [item for item in definitions if len(item) >= 4 and item[3] is True]
    assert len(headers) >= 3  # TIME DOMAIN, FREQUENCY DOMAIN, NONLINEAR METRICS
    
    # Test format_hrv_metric_with_tooltip
    display_text, tooltip = HRVTooltipUtils.format_hrv_metric_with_tooltip("Mean IBI", 750.5, "ms")
    assert "750.5 ms" in display_text
    assert tooltip == tooltips["Mean IBI"]
    
    # Test without unit
    display_text, tooltip = HRVTooltipUtils.format_hrv_metric_with_tooltip("Heart Rate", 72.3)
    assert "72.3" in display_text
    assert tooltip == tooltips["Heart Rate"]
    
    # Test create_tooltip_label
    label = HRVTooltipUtils.create_tooltip_label("SDNN", 45.2, "ms")
    assert label is not None
    assert "45.2 ms" in label.text()
    assert label.toolTip() == tooltips["SDNN"]


def test_plot_style_helper_comprehensive():
    """Test additional PlotStyleHelper methods for full coverage."""
    mock_plot = Mock(spec=pg.PlotWidget)
    mock_legend = Mock()
    
    # Test toggle_legend_visibility
    PlotStyleHelper.toggle_legend_visibility(mock_legend, True)
    mock_legend.setVisible.assert_called_with(True)
    
    PlotStyleHelper.toggle_legend_visibility(mock_legend, False)
    mock_legend.setVisible.assert_called_with(False)
    
    # Test with None legend
    PlotStyleHelper.toggle_legend_visibility(None, True)
    # Should not raise any exception
    
    # Test auto_scale_y_axis edge cases
    mock_plot.setYRange = Mock()
    
    # Empty data
    PlotStyleHelper.auto_scale_y_axis(mock_plot, [], [], (0, 1))
    assert mock_plot.setYRange.call_count == 0
    
    # Reset mock
    mock_plot.reset_mock()
    
    # Mismatched lengths
    PlotStyleHelper.auto_scale_y_axis(mock_plot, [1], [1, 2], (0, 1))
    assert mock_plot.setYRange.call_count == 0
    
    # Reset mock
    mock_plot.reset_mock()
    
    # No data in range
    PlotStyleHelper.auto_scale_y_axis(mock_plot, [2, 3], [10, 20], (0, 1))
    assert mock_plot.setYRange.call_count == 0
    
    # Reset mock
    mock_plot.reset_mock()
    
    # Fixed mode without limits
    PlotStyleHelper.auto_scale_y_axis(mock_plot, [1], [1], (0, 1), scale_mode="fixed")
    assert mock_plot.setYRange.call_count == 0
    
    # Reset mock
    mock_plot.reset_mock()
    
    # Fixed mode with limits
    PlotStyleHelper.auto_scale_y_axis(mock_plot, [1], [1], (0, 1), scale_mode="fixed", min_limit=0, max_limit=10)
    mock_plot.setYRange.assert_called_with(0, 10, padding=0.1)
    
    # Reset mock
    mock_plot.reset_mock()
    
    # None mode
    PlotStyleHelper.auto_scale_y_axis(mock_plot, [1], [1], (0, 1), scale_mode="none")
    assert mock_plot.setYRange.call_count == 0