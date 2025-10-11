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