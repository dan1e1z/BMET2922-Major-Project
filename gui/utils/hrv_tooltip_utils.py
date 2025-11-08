"""
HRV Tooltip Utilities

This module provides standardized tooltip definitions for HRV (Heart Rate Variability)
metrics used across different UI components in the application.

Author: Daniel Lindsay-Shad
Note: The Docstrings for methods were generated using Generative AI based on the method functionality.
"""

class HRVTooltipUtils:
    """Utility class for HRV metric tooltips and formatting."""

    @staticmethod
    def get_hrv_metric_tooltips():
        """
        Get comprehensive HRV metric definitions with tooltips.

        Returns:
            dict: Dictionary mapping metric names to their tooltip HTML content
        """
        return {
            "Mean IBI": (
                "Average time between heartbeats.<br>"
                "<b>Normal:</b> 600–1000 ms (60–100 bpm)<br>"
                "<b>Interpretation:</b> Lower values may indicate faster heart rate or stress; higher values suggest relaxation."
            ),
            "SDNN": (
                "Overall heart rate variability (standard deviation of NN intervals).<br>"
                "<b>Normal:</b> 20–200 ms<br>"
                "<b>Interpretation:</b> Higher values indicate stronger autonomic regulation; lower values may indicate stress, fatigue, or reduced HRV."
            ),
            "RMSSD": (
                "Short-term HRV reflecting parasympathetic (vagal) activity.<br>"
                "<b>Normal:</b> 20–50 ms<br>"
                "<b>Interpretation:</b> Higher values suggest good vagal tone; lower values may indicate stress or insufficient recovery."
            ),
            "pNN50": (
                "Percentage of successive heartbeats differing by more than 50 ms.<br>"
                "<b>Normal:</b> 5–30%<br>"
                "<b>Interpretation:</b> Higher values indicate healthy short-term HRV; lower values suggest sympathetic dominance or stress."
            ),
            "Heart Rate": (
                "Average heart rate calculated from mean IBI interval.<br>"
                "<b>Normal resting:</b> 60–100 bpm<br>"
                "<b>Interpretation:</b> Lower during rest; higher during stress, activity, or exercise."
            ),
            "VLF Power": (
                "Very low frequency (&lt;0.04 Hz) variability.<br>"
                "<b>Normal:</b> No strict range<br>"
                "<b>Interpretation:</b> May reflect thermoregulation or hormonal influences. Interpret cautiously."
            ),
            "LF Power": (
                "Low frequency (0.04–0.15 Hz) variability.<br>"
                "<b>Normal:</b> 200–1500 ms²<br>"
                "<b>Interpretation:</b> Reflects sympathetic activity and baroreflex. Higher values may indicate stress or sympathetic dominance."
            ),
            "HF Power": (
                "High frequency (0.15–0.4 Hz) variability.<br>"
                "<b>Normal:</b> 200–2000 ms²<br>"
                "<b>Interpretation:</b> Reflects parasympathetic (vagal) activity. Higher values indicate relaxation and strong vagal tone; lower values suggest stress."
            ),
            "LF/HF Ratio": (
                "Ratio of low- to high-frequency variability.<br>"
                "<b>Normal:</b> 0.5–2.0<br>"
                "<b>Interpretation:</b> &gt;2 indicates sympathetic dominance (stress/anxiety); &lt;0.5 indicates parasympathetic dominance."
            ),
            "SD1": (
                "Short-term HRV (Poincaré plot width). Similar to RMSSD.<br>"
                "<b>Normal:</b> 5–20 ms<br>"
                "<b>Interpretation:</b> Higher values indicate better short-term autonomic function."
            ),
            "SD2": (
                "Long-term HRV (Poincaré plot length). Reflects overall HRV.<br>"
                "<b>Normal:</b> 20–200 ms<br>"
                "<b>Interpretation:</b> Higher values indicate stronger overall autonomic regulation."
            ),
            "SD1/SD2 Ratio": (
                "Ratio of short-term to long-term HRV.<br>"
                "<b>Normal:</b> 0.3–1.0<br>"
                "<b>Interpretation:</b> &lt;0.5 suggests short-term variability is reduced; closer to 1 indicates balanced variability."
            )
        }

    @staticmethod
    def get_hrv_metrics_definitions():
        """
        Get HRV metrics definitions for display purposes.

        Returns:
            list: List of tuples (name, value, tooltip, is_header) for HRV metrics
        """
        tooltips = HRVTooltipUtils.get_hrv_metric_tooltips()

        return [
            ("TIME DOMAIN METRICS", "", "", True),  # Section header
            ("Mean IBI", "{mean_ibi:.1f} ms", tooltips["Mean IBI"]),
            ("SDNN", "{sdnn:.1f} ms", tooltips["SDNN"]),
            ("RMSSD", "{rmssd:.1f} ms", tooltips["RMSSD"]),
            ("pNN50", "{pnn50:.1f}%", tooltips["pNN50"]),
            ("Heart Rate", "{heart_rate:.1f} bpm", tooltips["Heart Rate"]),
            ("", "", ""),  # Spacer
            ("FREQUENCY DOMAIN", "", "", True),  # Section header
            ("VLF Power", "{vlf_power:.3f} ms²", tooltips["VLF Power"]),
            ("LF Power", "{lf_power:.3f} ms²", tooltips["LF Power"]),
            ("HF Power", "{hf_power:.3f} ms²", tooltips["HF Power"]),
            ("LF/HF Ratio", "{lf_hf_ratio:.2f}", tooltips["LF/HF Ratio"]),
            ("", "", ""),  # Spacer
            ("NONLINEAR METRICS", "", "", True),  # Section header
            ("SD1", "{sd1:.2f} ms", tooltips["SD1"]),
            ("SD2", "{sd2:.2f} ms", tooltips["SD2"]),
            ("SD1/SD2 Ratio", "{sd_ratio:.3f}", tooltips["SD1/SD2 Ratio"]),
        ]

    @staticmethod
    def format_hrv_metric_with_tooltip(metric_name, value, unit=""):
        """
        Format an HRV metric with its tooltip for QLabel display.

        Args:
            metric_name (str): Name of the HRV metric
            value (float): Numeric value of the metric
            unit (str): Unit string (e.g., "ms", "bpm", "%")

        Returns:
            tuple: (display_text, tooltip_text) for QLabel creation
        """
        tooltips = HRVTooltipUtils.get_hrv_metric_tooltips()
        tooltip = tooltips.get(metric_name, "")

        if unit:
            display_text = f"{value:.1f} {unit}"
        else:
            display_text = f"{value:.1f}"

        return display_text, tooltip

    @staticmethod
    def create_tooltip_label(metric_name, value, unit="", parent=None):
        """
        Create a QLabel with HRV metric value and tooltip.

        Args:
            metric_name (str): Name of the HRV metric
            value (float): Numeric value of the metric
            unit (str): Unit string (e.g., "ms", "bpm", "%")
            parent: Parent widget

        Returns:
            QtWidgets.QLabel: Configured label with tooltip
        """
        from PyQt5 import QtWidgets

        display_text, tooltip = HRVTooltipUtils.format_hrv_metric_with_tooltip(metric_name, value, unit)

        label = QtWidgets.QLabel(display_text, parent)
        label.setToolTip(tooltip)
        label.setStyleSheet("background-color: transparent;")

        return label