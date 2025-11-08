"""
Data validation utilities.

Provides functions for validating PPG data and signal quality metrics.

Author: Daniel Lindsay-Shad
Note: The Docstrings for methods were generated using Generative AI based on the method functionality.
"""

import numpy as np

class DataValidationUtils:
    """Utilities for data validation and quality checks."""
    
    @staticmethod
    def validate_bpm(bpm, min_valid=20, max_valid=250):
        """
        Check if BPM value is physiologically valid.
        
        Args:
            bpm: BPM value to validate
            min_valid: Minimum valid BPM
            max_valid: Maximum valid BPM
            
        Returns:
            bool: True if valid
        """
        return min_valid <= bpm <= max_valid
    
    @staticmethod
    def calculate_signal_quality_metrics(signal):
        """
        Calculate basic signal quality metrics.
        
        Args:
            signal: Signal array
            
        Returns:
            dict: Quality metrics
        """
        if len(signal) == 0:
            return {}
        
        # Missing/invalid data
        invalid_count = np.sum(np.isnan(signal)) + np.sum(np.isinf(signal))
        
        # SNR estimate
        signal_power = np.var(signal)
        diff_signal = np.diff(signal)
        noise_power = np.var(diff_signal) / 2
        snr_db = 10 * np.log10(signal_power / max(noise_power, 1e-10))
        
        return {
            'samples': len(signal),
            'invalid_count': invalid_count,
            'invalid_percent': (invalid_count / len(signal)) * 100,
            'snr_db': snr_db,
            'mean': np.mean(signal),
            'std': np.std(signal),
            'min': np.min(signal),
            'max': np.max(signal)
        }
    
    @staticmethod
    def filter_outliers(data, n_std=3):
        """
        Filter outliers using standard deviation method.
        
        Args:
            data: Data array
            n_std: Number of standard deviations for outlier threshold
            
        Returns:
            numpy array: Filtered data
        """
        if len(data) == 0:
            return data
        
        mean = np.mean(data)
        std = np.std(data)
        mask = np.abs(data - mean) <= n_std * std
        return data[mask]