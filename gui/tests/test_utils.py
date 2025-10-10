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


class TestDataValidationUtils:
    """Test DataValidationUtils class."""

    class TestValidateBpm:
        """Test validate_bpm method."""

        def test_valid_bpm_normal_range(self):
            assert DataValidationUtils.validate_bpm(60) is True
            assert DataValidationUtils.validate_bpm(100) is True
            assert DataValidationUtils.validate_bpm(75.5) is True

        def test_valid_bpm_edge_cases(self):
            assert DataValidationUtils.validate_bpm(20) is True
            assert DataValidationUtils.validate_bpm(250) is True

        def test_invalid_bpm_too_low(self):
            assert DataValidationUtils.validate_bpm(19) is False
            assert DataValidationUtils.validate_bpm(0) is False
            assert DataValidationUtils.validate_bpm(-10) is False

        def test_invalid_bpm_too_high(self):
            assert DataValidationUtils.validate_bpm(251) is False
            assert DataValidationUtils.validate_bpm(300) is False

        def test_custom_thresholds(self):
            assert DataValidationUtils.validate_bpm(15, min_valid=10, max_valid=200) is True
            assert DataValidationUtils.validate_bpm(15, min_valid=20, max_valid=200) is False
            assert DataValidationUtils.validate_bpm(210, min_valid=20, max_valid=200) is False

    class TestCalculateSignalQualityMetrics:
        """Test calculate_signal_quality_metrics method."""

        def test_empty_signal(self):
            result = DataValidationUtils.calculate_signal_quality_metrics(np.array([]))
            assert result == {}

        def test_basic_signal_metrics(self):
            signal = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
            result = DataValidationUtils.calculate_signal_quality_metrics(signal)

            assert result['samples'] == 5
            assert result['invalid_count'] == 0
            assert result['invalid_percent'] == 0
            assert result['mean'] == 3.0
            assert result['std'] == np.std(signal)
            assert result['min'] == 1.0
            assert result['max'] == 5.0

        def test_signal_with_nan(self):
            signal = np.array([1.0, 2.0, np.nan, 4.0, 5.0])
            result = DataValidationUtils.calculate_signal_quality_metrics(signal)

            assert result['samples'] == 5
            assert result['invalid_count'] == 1
            assert result['invalid_percent'] == 20.0

        def test_signal_with_inf(self):
            signal = np.array([1.0, 2.0, np.inf, 4.0, 5.0])
            result = DataValidationUtils.calculate_signal_quality_metrics(signal)

            assert result['invalid_count'] == 1

        def test_signal_with_multiple_invalid(self):
            signal = np.array([1.0, np.nan, np.inf, 4.0, np.nan])
            result = DataValidationUtils.calculate_signal_quality_metrics(signal)

            assert result['invalid_count'] == 3
            assert result['invalid_percent'] == 60.0

        def test_snr_calculation(self):
            # Use a sine wave instead of a constant signal to avoid -inf results.
            signal = np.sin(np.linspace(0, 10 * np.pi, 200))
            result = DataValidationUtils.calculate_signal_quality_metrics(signal)
            assert 'snr_db' in result

            noisy_signal = signal + np.random.randn(200) * 0.1
            result_noisy = DataValidationUtils.calculate_signal_quality_metrics(noisy_signal)
            # SNR for cleaner signal should be higher than for noisy signal
            assert result['snr_db'] > result_noisy['snr_db']

        def test_all_invalid_signal(self):
            signal = np.array([np.nan, np.inf, np.nan])
            result = DataValidationUtils.calculate_signal_quality_metrics(signal)

            assert result['samples'] == 3
            assert result['invalid_count'] == 3
            assert result['invalid_percent'] == 100.0

    class TestFilterOutliers:
        """Test filter_outliers method."""

        def test_no_outliers(self):
            data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
            result = DataValidationUtils.filter_outliers(data)
            assert len(result) == 5

        def test_with_outliers(self):
            data = np.array([1.0, 2.0, 3.0, 100.0, 4.0, 5.0])
            result = DataValidationUtils.filter_outliers(data, n_std=2)
            assert len(result) < len(data)
            assert 100.0 not in result

        def test_empty_data(self):
            data = np.array([])
            result = DataValidationUtils.filter_outliers(data)
            assert len(result) == 0

        def test_custom_std_threshold(self):
            data = np.array([1.0, 2.0, 3.0, 4.0, 10.0])
            result_loose = DataValidationUtils.filter_outliers(data, n_std=3)
            result_strict = DataValidationUtils.filter_outliers(data, n_std=1)
            assert len(result_loose) >= len(result_strict)

        def test_single_value(self):
            data = np.array([5.0])
            result = DataValidationUtils.filter_outliers(data)
            assert len(result) == 1


class TestSignalProcessingUtils:
    """Test SignalProcessingUtils class."""

    class TestDetectPpgPeaks:
        """Test detect_ppg_peaks method."""

        def test_detect_peaks_basic(self):
            signal = np.sin(np.linspace(0, 10*np.pi, 500))
            peaks, info = SignalProcessingUtils.detect_ppg_peaks(signal, sampling_rate=50)

            assert isinstance(peaks, np.ndarray)
            assert isinstance(info, dict)
            assert len(peaks) > 0

        def test_detect_peaks_different_methods(self):
            signal = np.sin(np.linspace(0, 10*np.pi, 500))
            peaks_elgendi, _ = SignalProcessingUtils.detect_ppg_peaks(signal, method="elgendi")
            peaks_bishop, _ = SignalProcessingUtils.detect_ppg_peaks(signal, method="bishop")

            assert len(peaks_elgendi) > 0
            assert len(peaks_bishop) > 0

        def test_detect_peaks_empty_signal(self):
            signal = np.array([])
            peaks, info = SignalProcessingUtils.detect_ppg_peaks(signal)

            assert len(peaks) == 0
            assert isinstance(info, dict)

        def test_detect_peaks_flat_signal(self):
            signal = np.ones(100)
            peaks, info = SignalProcessingUtils.detect_ppg_peaks(signal)

            assert isinstance(peaks, np.ndarray)

        def test_detect_peaks_handles_exception(self, mocker):
            mock_ppg_peaks = mocker.patch('neurokit2.ppg_peaks')
            mock_ppg_peaks.side_effect = Exception("Processing error")
            signal = np.array([1, 2, 3, 4, 5])
            peaks, info = SignalProcessingUtils.detect_ppg_peaks(signal)

            assert len(peaks) == 0
            assert info == {}

    class TestCleanPpgSignal:
        """Test clean_ppg_signal method."""

        def test_clean_signal_basic(self):
            signal = np.random.randn(500) + np.sin(np.linspace(0, 10*np.pi, 500))
            cleaned = SignalProcessingUtils.clean_ppg_signal(signal)

            assert isinstance(cleaned, np.ndarray)
            assert len(cleaned) == len(signal)

        def test_clean_signal_preserves_length(self):
            signal = np.random.randn(200)
            cleaned = SignalProcessingUtils.clean_ppg_signal(signal)

            assert len(cleaned) == 200

        def test_clean_signal_handles_exception(self, mocker):
            mock_ppg_clean = mocker.patch('neurokit2.ppg_clean')
            mock_ppg_clean.side_effect = Exception("Cleaning error")
            signal = np.array([1, 2, 3, 4, 5])
            cleaned = SignalProcessingUtils.clean_ppg_signal(signal)

            np.testing.assert_array_equal(cleaned, signal)

    class TestCalculateRrIntervals:
        """Test calculate_rr_intervals method."""

        def test_calculate_rr_basic(self):
            peak_indices = np.array([10, 60, 110, 160])
            rr_intervals = SignalProcessingUtils.calculate_rr_intervals(peak_indices, sampling_rate=50)

            assert len(rr_intervals) == 3
            np.testing.assert_array_almost_equal(rr_intervals, [1000, 1000, 1000])

        def test_calculate_rr_variable_intervals(self):
            peak_indices = np.array([10, 50, 120])
            rr_intervals = SignalProcessingUtils.calculate_rr_intervals(peak_indices, sampling_rate=50)

            assert len(rr_intervals) == 2
            assert rr_intervals[0] == 800
            assert rr_intervals[1] == 1400

        def test_calculate_rr_single_peak(self):
            peak_indices = np.array([10])
            rr_intervals = SignalProcessingUtils.calculate_rr_intervals(peak_indices)
            assert len(rr_intervals) == 0

        def test_calculate_rr_no_peaks(self):
            peak_indices = np.array([])
            rr_intervals = SignalProcessingUtils.calculate_rr_intervals(peak_indices)
            assert len(rr_intervals) == 0

        def test_calculate_rr_different_sampling_rate(self):
            peak_indices = np.array([10, 110])
            rr_intervals = SignalProcessingUtils.calculate_rr_intervals(peak_indices, sampling_rate=100)
            assert rr_intervals[0] == 1000

    class TestCalculateHrvTimeDomain:
        """Test calculate_hrv_time_domain method."""

        def test_hrv_basic_metrics(self):
            rr_intervals = np.array([800, 820, 790, 810, 800, 795, 805])
            metrics = SignalProcessingUtils.calculate_hrv_time_domain(rr_intervals)

            assert all(k in metrics for k in ['mean_rr', 'sdnn', 'rmssd', 'heart_rate', 'pnn50', 'sd1', 'sd2', 'sd_ratio'])

        def test_hrv_filters_invalid_intervals(self):
            rr_intervals = np.array([100, 800, 2500, 820, 790, 3000])
            metrics = SignalProcessingUtils.calculate_hrv_time_domain(rr_intervals)

            assert 'mean_rr' in metrics
            assert 300 < metrics['mean_rr'] < 2000

        def test_hrv_insufficient_data(self):
            rr_intervals = np.array([800])
            metrics = SignalProcessingUtils.calculate_hrv_time_domain(rr_intervals)
            assert metrics == {}

        def test_hrv_all_invalid_intervals(self):
            rr_intervals = np.array([100, 2500, 3000])
            metrics = SignalProcessingUtils.calculate_hrv_time_domain(rr_intervals)
            assert metrics == {}

        def test_hrv_heart_rate_calculation(self):
            rr_intervals = np.array([1000, 1000, 1000])
            metrics = SignalProcessingUtils.calculate_hrv_time_domain(rr_intervals)
            assert abs(metrics['heart_rate'] - 60.0) < 0.1

        def test_hrv_pnn50_calculation(self):
            rr_intervals = np.array([800, 860, 810, 870, 800, 850])
            metrics = SignalProcessingUtils.calculate_hrv_time_domain(rr_intervals)

            assert 'pnn50' in metrics
            assert 0 <= metrics['pnn50'] <= 100

        def test_hrv_poincare_metrics(self):
            # Provide more data points to ensure SD1/SD2 can be calculated.
            rr_intervals = np.array([800, 820, 790, 810, 800, 815, 785, 805, 825])
            metrics = SignalProcessingUtils.calculate_hrv_time_domain(rr_intervals)

            assert metrics['sd1'] > 0
            assert metrics['sd2'] > 0
            assert metrics['sd_ratio'] > 0

    class TestRemoveDuplicatePeaks:
        """Test remove_duplicate_peaks method."""

        def test_remove_duplicates_basic(self):
            peaks = np.array([10, 20, 20, 30, 40, 40, 40, 50])
            unique_peaks = SignalProcessingUtils.remove_duplicate_peaks(peaks)
            expected = np.array([10, 20, 30, 40, 50])
            np.testing.assert_array_equal(unique_peaks, expected)

        def test_remove_duplicates_no_duplicates(self):
            peaks = np.array([10, 20, 30, 40, 50])
            unique_peaks = SignalProcessingUtils.remove_duplicate_peaks(peaks)
            np.testing.assert_array_equal(unique_peaks, peaks)

        def test_remove_duplicates_empty(self):
            peaks = np.array([])
            unique_peaks = SignalProcessingUtils.remove_duplicate_peaks(peaks)
            assert len(unique_peaks) == 0

        def test_remove_duplicates_maintains_order(self):
            peaks = np.array([50, 20, 30, 20, 10, 40])
            unique_peaks = SignalProcessingUtils.remove_duplicate_peaks(peaks)
            expected = np.array([10, 20, 30, 40, 50])
            np.testing.assert_array_equal(unique_peaks, expected)


class TestSessionInfoFormatter:
    """Test SessionInfoFormatter class."""

    class TestFormatDuration:
        """Test format_duration method."""
        def test_format_seconds(self):
            assert SessionInfoFormatter.format_duration(0.5) == "30 sec"
            assert SessionInfoFormatter.format_duration(0.25) == "15 sec"

        def test_format_minutes(self):
            assert SessionInfoFormatter.format_duration(5) == "5.0 min"
            assert SessionInfoFormatter.format_duration(45.5) == "45.5 min"

        def test_format_hours(self):
            assert SessionInfoFormatter.format_duration(60) == "1.0 hrs"
            assert SessionInfoFormatter.format_duration(90) == "1.5 hrs"
            assert SessionInfoFormatter.format_duration(120) == "2.0 hrs"

        def test_format_edge_cases(self):
            assert SessionInfoFormatter.format_duration(0) == "0 sec"
            assert SessionInfoFormatter.format_duration(1) == "1.0 min"
            assert SessionInfoFormatter.format_duration(59.9) == "59.9 min"

    class TestFormatDatetime:
        """Test format_datetime method."""

        def test_format_valid_iso_string(self):
            result = SessionInfoFormatter.format_datetime("2025-01-15T10:30:45")
            assert result == "2025-01-15 10:30:45"

        def test_format_with_microseconds(self):
            result = SessionInfoFormatter.format_datetime("2025-01-15T10:30:45.123456")
            assert "2025-01-15 10:30:45" in result

        def test_format_invalid_string(self):
            result = SessionInfoFormatter.format_datetime("not a date")
            assert result == "not a date"

        def test_format_none(self):
            result = SessionInfoFormatter.format_datetime(None)
            assert result is None

        def test_format_already_formatted(self):
            result = SessionInfoFormatter.format_datetime("2025-01-15 10:30:45")
            assert result == "2025-01-15 10:30:45"

    class TestFormatBpmStatus:
        """Test format_bpm_status method."""

        def test_normal_range(self):
            status, color = SessionInfoFormatter.format_bpm_status(75)
            assert status == "Normal"
            assert color == "#4CAF50"

        def test_below_threshold(self):
            status, color = SessionInfoFormatter.format_bpm_status(35, low_threshold=40)
            assert status == "Below Normal (Bradycardia)"
            assert color == "#FF9800"

        def test_above_threshold(self):
            status, color = SessionInfoFormatter.format_bpm_status(210, high_threshold=200)
            assert status == "Above Normal (Tachycardia)"
            assert color == "#FF5722"

        def test_below_normal_not_bradycardia(self):
            status, color = SessionInfoFormatter.format_bpm_status(55)
            assert status == "Below Normal"
            assert color == "#FF9800"

        def test_above_normal_not_tachycardia(self):
            status, color = SessionInfoFormatter.format_bpm_status(110)
            assert status == "Above Normal"
            assert color == "#FF9800"

        def test_edge_cases(self):
            status, _ = SessionInfoFormatter.format_bpm_status(60)
            assert status == "Normal"
            status, _ = SessionInfoFormatter.format_bpm_status(100)
            assert status == "Normal"

    class TestCalculateSessionStats:
        """Test calculate_session_stats method."""

        def test_basic_stats(self):
            bpm_list = [70, 75, 80, 85, 90]
            stats = SessionInfoFormatter.calculate_session_stats(bpm_list)

            assert stats['avg'] == 80
            assert stats['min'] == 70
            assert stats['max'] == 90
            assert stats['count'] == 5
            assert 'std' in stats

        def test_empty_list(self):
            stats = SessionInfoFormatter.calculate_session_stats([])
            assert stats['avg'] == 0
            assert stats['min'] == 0
            assert stats['max'] == 0
            assert stats['count'] == 0

        def test_filters_zero_values(self):
            bpm_list = [70, 0, 80, 0, 90]
            stats = SessionInfoFormatter.calculate_session_stats(bpm_list)
            assert stats['count'] == 3
            assert stats['avg'] == 80
            assert stats['min'] == 70

        def test_all_zero_values(self):
            bpm_list = [0, 0, 0]
            stats = SessionInfoFormatter.calculate_session_stats(bpm_list)
            assert stats['avg'] == 0
            assert stats['count'] == 0

        def test_single_value(self):
            stats = SessionInfoFormatter.calculate_session_stats([75])
            assert stats['avg'] == 75
            assert stats['min'] == 75
            assert stats['max'] == 75
            assert stats['count'] == 1
            assert stats['std'] == 0

        def test_negative_values(self):
            bpm_list = [70, -5, 80, 90]
            stats = SessionInfoFormatter.calculate_session_stats(bpm_list)
            assert stats['count'] == 3
            assert -5 not in [stats['min'], stats['max']]


class TestPlotStyleHelper:
    """Test PlotStyleHelper class."""

    class TestConfigurePlotWidget:
        """Test configure_plot_widget method."""

        @pytest.fixture
        def mock_plot_widget(self):
            mock = Mock(spec=pg.PlotWidget)
            mock.setTitle = Mock()
            mock.setLabel = Mock()
            mock.showGrid = Mock()
            mock.setMouseEnabled = Mock()
            mock.setMenuEnabled = Mock()
            mock.enableAutoRange = Mock()
            mock.addLegend = Mock(return_value=Mock())
            return mock

        def test_configure_basic(self, mock_plot_widget):
            PlotStyleHelper.configure_plot_widget(
                mock_plot_widget, title="Test Plot", x_label="Time"
            )
            mock_plot_widget.setTitle.assert_called_once_with("Test Plot")
            mock_plot_widget.setLabel.assert_any_call('bottom', "Time", units="s")
            mock_plot_widget.setLabel.assert_any_call('bottom', "Time", units="s")

        def test_configure_with_units(self, mock_plot_widget):
            PlotStyleHelper.configure_plot_widget(
                mock_plot_widget, x_label="Time", x_units="s", y_label="Amplitude", y_units="mV"
            )
            mock_plot_widget.setLabel.assert_any_call('left', "Amplitude", units="mV")
            mock_plot_widget.setLabel.assert_any_call('bottom', "Time", units="s")

        def test_configure_grid_enabled(self, mock_plot_widget):
            PlotStyleHelper.configure_plot_widget(mock_plot_widget, grid=True)
            # Match actual call signature: positional args, not keyword
            mock_plot_widget.showGrid.assert_called_once_with(True, True)

        def test_configure_grid_disabled(self, mock_plot_widget):
            PlotStyleHelper.configure_plot_widget(mock_plot_widget, grid=False)
            mock_plot_widget.showGrid.assert_not_called()

        def test_configure_mouse_enabled(self, mock_plot_widget):
            PlotStyleHelper.configure_plot_widget(mock_plot_widget, mouse_enabled=True)
            mock_plot_widget.setMouseEnabled.assert_called_once_with(x=True, y=True)

        def test_configure_mouse_disabled(self, mock_plot_widget):
            PlotStyleHelper.configure_plot_widget(mock_plot_widget, mouse_enabled=False)
            mock_plot_widget.setMouseEnabled.assert_called_once_with(x=False, y=False)

        def test_configure_menu_enabled(self, mock_plot_widget):
            PlotStyleHelper.configure_plot_widget(mock_plot_widget, menu_enabled=True)
            mock_plot_widget.setMenuEnabled.assert_called_once_with(True)

        def test_configure_no_title(self, mock_plot_widget):
            PlotStyleHelper.configure_plot_widget(mock_plot_widget)
            mock_plot_widget.setTitle.assert_not_called()

    class TestAutoScaleYAxis:
        """Test auto_scale_y_axis method."""

        @pytest.fixture
        def mock_plot_widget(self):
            mock = Mock(spec=pg.PlotWidget)
            mock.enableAutoRange = Mock()
            return mock

        def test_auto_scale_enables_autorange(self, mock_plot_widget):
            x_data = [0, 1, 2, 3, 4]
            y_data = [10, 20, 15, 25, 30]
            x_range = (0, 4)
            PlotStyleHelper.auto_scale_y_axis(mock_plot_widget, x_data, y_data, x_range)
            mock_plot_widget.enableAutoRange.assert_called_once_with(axis='y', enable=True)

    class TestCreateLegend:
        """Test create_legend method."""

        def test_create_legend_basic(self):
            mock_plot = Mock(spec=pg.PlotWidget)
            mock_legend = Mock()
            mock_plot.addLegend = Mock(return_value=mock_legend)
            result = PlotStyleHelper.create_legend(mock_plot)
            mock_plot.addLegend.assert_called_once_with(offset=(-1, -1))
            assert result == mock_legend

        def test_create_legend_custom_offset(self):
            mock_plot = Mock(spec=pg.PlotWidget)
            mock_plot.addLegend = Mock()
            PlotStyleHelper.create_legend(mock_plot, offset=(10, 20))
            mock_plot.addLegend.assert_called_once_with(offset=(10, 20))

    class TestToggleLegendVisibility:
        """Test toggle_legend_visibility method."""

        def test_toggle_visible(self):
            mock_legend = Mock()
            PlotStyleHelper.toggle_legend_visibility(mock_legend, True)
            mock_legend.setVisible.assert_called_once_with(True)

        def test_toggle_invisible(self):
            mock_legend = Mock()
            PlotStyleHelper.toggle_legend_visibility(mock_legend, False)
            mock_legend.setVisible.assert_called_once_with(False)

        def test_toggle_none_legend(self):
            # Should not raise an error
            PlotStyleHelper.toggle_legend_visibility(None, True)


class TestIntegration:
    """Integration tests across utility classes."""

    def test_signal_processing_pipeline(self):
        t = np.linspace(0, 10, 500)
        signal = np.sin(2 * np.pi * 1.2 * t) + 0.1 * np.random.randn(500)
        cleaned = SignalProcessingUtils.clean_ppg_signal(signal, sampling_rate=50)
        peaks, _ = SignalProcessingUtils.detect_ppg_peaks(cleaned, sampling_rate=50)

        if len(peaks) > 1:
            rr_intervals = SignalProcessingUtils.calculate_rr_intervals(peaks, sampling_rate=50)
            if len(rr_intervals) > 2:
                hrv_metrics = SignalProcessingUtils.calculate_hrv_time_domain(rr_intervals)
                if hrv_metrics:
                    assert 'mean_rr' in hrv_metrics
                    assert 'sdnn' in hrv_metrics
                    assert 'heart_rate' in hrv_metrics

    def test_data_validation_and_formatting(self):
        bpm_values = [70, 75, 80, 85, 90, 95, 100]
        stats = SessionInfoFormatter.calculate_session_stats(bpm_values)
        for bpm in bpm_values:
            assert DataValidationUtils.validate_bpm(bpm) is True

        duration_str = SessionInfoFormatter.format_duration(10)
        assert "min" in duration_str
        status, _ = SessionInfoFormatter.format_bpm_status(stats['avg'])
        assert status in ["Normal", "Below Normal", "Above Normal"]

    def test_signal_quality_assessment(self):
        good_signal = np.sin(np.linspace(0, 10*np.pi, 500))
        noisy_signal = good_signal + np.random.randn(500) * 0.5
        good_metrics = DataValidationUtils.calculate_signal_quality_metrics(good_signal)
        noisy_metrics = DataValidationUtils.calculate_signal_quality_metrics(noisy_signal)

        assert good_metrics['snr_db'] > noisy_metrics['snr_db']
        assert good_metrics['invalid_count'] == 0
        assert noisy_metrics['invalid_count'] == 0