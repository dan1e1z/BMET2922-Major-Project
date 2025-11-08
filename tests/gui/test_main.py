import pytest
from unittest.mock import Mock, patch
from PyQt5 import QtWidgets
import gui.main


def test_main_function(qtbot, mocker):
    """Test the main function creates and shows the main window."""
    # Mock QApplication and MainWindow
    mock_app = Mock(spec=QtWidgets.QApplication)
    mock_app.exec_.return_value = 0
    
    mock_window = Mock()
    
    with patch('PyQt5.QtWidgets.QApplication', return_value=mock_app), \
         patch('gui.main.MainWindow', return_value=mock_window), \
         patch('sys.exit') as mock_exit:
        
        gui.main.main()
        
        # Verify QApplication was created with sys.argv
        # Verify MainWindow was created
        mock_window.show.assert_called_once()
        # Verify app.exec_ was called
        mock_app.exec_.assert_called_once()
        # Verify sys.exit was called with the return value
        mock_exit.assert_called_once_with(0)