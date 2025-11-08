"""
Signal processing utilities.

Provides functions for PPG signal processing and analysis.

Author: Daniel Lindsay-Shad
Note: The Docstrings for methods were generated using Generative AI based on the method functionality.
"""

import numpy as np
import neurokit2 as nk

class SignalProcessingUtils:
    """Shared signal processing utilities for PPG analysis."""
    
    @staticmethod
    def detect_ppg_peaks(signal, sampling_rate=50, method="elgendi"):
        """
        Detect peaks in PPG signal using NeuroKit.
        
        Args:
            signal: PPG signal array
            sampling_rate: Sampling rate in Hz
            method: Peak detection method ('elgendi', 'bishop', 'charlton')
            
        Returns:
            tuple: (peaks array, info dict)
        """
        try:
            _, info = nk.ppg_peaks(signal, sampling_rate=sampling_rate, method=method)
            peaks = info.get("PPG_Peaks", np.array([]))
            return peaks, info
        except Exception as e:
            print(f"Peak detection failed: {e}")
            return np.array([]), {}
    
    @staticmethod
    def clean_ppg_signal(signal, sampling_rate=50, method="elgendi"):
        """
        Clean PPG signal using NeuroKit.
        
        Args:
            signal: Raw PPG signal
            sampling_rate: Sampling rate in Hz
            method: Cleaning method
            
        Returns:
            numpy array: Cleaned signal
        """
        try:
            return nk.ppg_clean(signal, sampling_rate=sampling_rate, method=method)
        except Exception as e:
            print(f"Signal cleaning failed: {e}")
            return signal
    
    @staticmethod
    def calculate_rr_intervals(peak_indices, sampling_rate=50):
        """
        Calculate R-R intervals from peak indices.
        
        Args:
            peak_indices: Array of peak sample indices
            sampling_rate: Sampling rate in Hz
            
        Returns:
            numpy array: R-R intervals in milliseconds
        """
        if len(peak_indices) < 2:
            return np.array([])
        
        rr_intervals = np.diff(peak_indices) / sampling_rate * 1000
        return rr_intervals
    
    @staticmethod
    def calculate_hrv_time_domain(rr_intervals):
        """
        Calculate time-domain HRV metrics.
        
        Args:
            rr_intervals: Array of R-R intervals in milliseconds
            
        Returns:
            dict: Dictionary of HRV metrics
        """
        if len(rr_intervals) < 2:
            return {}
        
        # Filter physiologically plausible intervals
        valid_mask = (rr_intervals > 300) & (rr_intervals < 2000)
        valid_rr = rr_intervals[valid_mask]
        
        if len(valid_rr) < 2:
            return {}
        
        metrics = {
            'mean_rr': np.mean(valid_rr),
            'sdnn': np.std(valid_rr),
            'rmssd': np.sqrt(np.mean(np.diff(valid_rr)**2)),
            'heart_rate': 60000 / np.mean(valid_rr)
        }
        
        # pNN50
        diff_rr = np.abs(np.diff(valid_rr))
        if len(diff_rr) > 0:
            nn50 = np.sum(diff_rr > 50)
            metrics['pnn50'] = (nn50 / len(diff_rr)) * 100
        else:
            metrics['pnn50'] = 0
        
        # Poincaré metrics
        sd1 = np.sqrt(0.5 * metrics['rmssd']**2)
        sd2_squared = 2 * metrics['sdnn']**2 - 0.5 * metrics['rmssd']**2
        sd2 = np.sqrt(max(sd2_squared, 0))
        
        metrics['sd1'] = sd1
        metrics['sd2'] = sd2
        metrics['sd_ratio'] = sd1 / sd2 if sd2 > 0 else 0
        
        return metrics

    @staticmethod
    def remove_duplicate_peaks(peak_indices):
        """
        Remove duplicate peak indices that might cause NeuroKit warnings.
        
        Args:
            peak_indices: Array of peak sample indices
            
        Returns:
            numpy array: Unique peak indices in sorted order
        """
        return np.unique(peak_indices)