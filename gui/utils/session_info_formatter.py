"""
Session info formatter utilities.

Provides functions for formatting session information for display.

Author: Daniel Lindsay-Shad
Note: The Docstrings for methods were generated using Generative AI based on the method functionality.
"""

import numpy as np
from datetime import datetime

class SessionInfoFormatter:
    """Utilities for formatting session information consistently."""
    
    @staticmethod
    def format_duration(duration_minutes):
        """
        Format duration for display.
        
        Args:
            duration_minutes: Duration in minutes
            
        Returns:
            str: Formatted duration string
        """
        if duration_minutes < 1:
            return f"{duration_minutes*60:.0f} sec"
        elif duration_minutes < 60:
            return f"{duration_minutes:.1f} min"
        else:
            hours = duration_minutes / 60
            return f"{hours:.1f} hrs"
    
    @staticmethod
    def format_datetime(datetime_str):
        """
        Format datetime string for display.
        
        Args:
            datetime_str: ISO format datetime string
            
        Returns:
            str: Formatted datetime
        """
        try:
            dt = datetime.fromisoformat(datetime_str)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            return datetime_str
    
    @staticmethod
    def format_bpm_status(bpm, low_threshold=40, high_threshold=200):
        """
        Get BPM status and color.
        
        Args:
            bpm: Heart rate in BPM
            low_threshold: Low threshold
            high_threshold: High threshold
            
        Returns:
            tuple: (status_text, color_hex)
        """
        if bpm < low_threshold:
            return "Below Normal (Bradycardia)", "#FF9800"
        elif bpm > high_threshold:
            return "Above Normal (Tachycardia)", "#FF5722"
        elif bpm < 60:
            return "Below Normal", "#FF9800"
        elif bpm > 100:
            return "Above Normal", "#FF9800"
        else:
            return "Normal", "#4CAF50"
    
    @staticmethod
    def calculate_session_stats(session_bpm_list):
        """
        Calculate basic statistics from session BPM data.
        
        Args:
            session_bpm_list: List of BPM values
            
        Returns:
            dict: Statistics dictionary
        """
        if not session_bpm_list:
            return {
                'avg': 0, 'min': 0, 'max': 0,
                'std': 0, 'count': 0
            }
        
        valid_bpm = [b for b in session_bpm_list if b > 0]
        if not valid_bpm:
            return {
                'avg': 0, 'min': 0, 'max': 0,
                'std': 0, 'count': 0
            }
        
        return {
            'avg': np.mean(valid_bpm),
            'min': np.min(valid_bpm),
            'max': np.max(valid_bpm),
            'std': np.std(valid_bpm),
            'count': len(valid_bpm)
        }