from PyQt5 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
import numpy as np
from scipy.signal import butter, filtfilt
import os

class ResearchTab(QtWidgets.QWidget):
    """
    Tab for advanced users to load, filter, and analyze raw PPG signals from past sessions.
    """
    def __init__(self):
        super().__init__()
        self.user_manager = None
        self.current_user = None
        self.raw_ppg_signal = np.array([])
        self.filtered_ppg_signal = np.array([])
        self.sampling_rate = 50 # Default, should be updated based on data
        self.setup_ui()

    def setup_ui(self):
        """
        Set up the UI for the research tab, including plots and controls.
        """
        layout = QtWidgets.QVBoxLayout()

        # Title
        title = QtWidgets.QLabel("Raw Signal Analysis")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)

        # Main horizontal layout for plots and controls
        main_hbox = QtWidgets.QHBoxLayout()

        # --- Plots ---
        plots_vbox = QtWidgets.QVBoxLayout()
        self.original_plot = pg.PlotWidget(title="Original Raw PPG Signal")
        self.original_plot.setLabel('left', 'Amplitude')
        self.original_plot.setLabel('bottom', 'Time (s)')
        self.original_curve = self.original_plot.plot(pen='b')
        plots_vbox.addWidget(self.original_plot)

        self.filtered_plot = pg.PlotWidget(title="Filtered PPG Signal")
        self.filtered_plot.setLabel('left', 'Amplitude')
        self.filtered_plot.setLabel('bottom', 'Time (s)')
        self.filtered_curve = self.filtered_plot.plot(pen='g')
        plots_vbox.addWidget(self.filtered_plot)

        main_hbox.addLayout(plots_vbox, 3) # 75% width for plots

        # --- Controls ---
        controls_vbox = QtWidgets.QVBoxLayout()
        controls_group = QtWidgets.QGroupBox("Controls")
        controls_layout = QtWidgets.QFormLayout()

        # Session Loader
        self.session_selector = QtWidgets.QComboBox()
        self.session_selector.addItem("Select a session to load...")
        self.session_selector.currentIndexChanged.connect(self.load_selected_session)
        controls_layout.addRow("Load Session:", self.session_selector)

        # Filter Type
        self.filter_type_combo = QtWidgets.QComboBox()
        self.filter_type_combo.addItems(["Bandpass", "Low-pass", "High-pass"])
        self.filter_type_combo.currentIndexChanged.connect(self.update_control_visibility)
        controls_layout.addRow("Filter Type:", self.filter_type_combo)

        # Low Cutoff
        self.low_cutoff_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.low_cutoff_slider.setRange(1, 100) # 0.1 to 10.0 Hz
        self.low_cutoff_slider.setValue(5) # Default 0.5 Hz
        self.low_cutoff_label = QtWidgets.QLabel(f"{self.low_cutoff_slider.value()/10:.1f} Hz")
        self.low_cutoff_slider.valueChanged.connect(lambda v: self.low_cutoff_label.setText(f"{v/10:.1f} Hz"))
        self.low_cutoff_widget = self.create_slider_widget("Low Cutoff:", self.low_cutoff_slider, self.low_cutoff_label)
        controls_layout.addRow(self.low_cutoff_widget)

        # High Cutoff
        self.high_cutoff_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.high_cutoff_slider.setRange(10, 400) # 1.0 to 40.0 Hz
        self.high_cutoff_slider.setValue(400) # Default 40.0 Hz
        self.high_cutoff_label = QtWidgets.QLabel(f"{self.high_cutoff_slider.value()/10:.1f} Hz")
        self.high_cutoff_slider.valueChanged.connect(lambda v: self.high_cutoff_label.setText(f"{v/10:.1f} Hz"))
        self.high_cutoff_widget = self.create_slider_widget("High Cutoff:", self.high_cutoff_slider, self.high_cutoff_label)
        controls_layout.addRow(self.high_cutoff_widget)

        # Filter Order
        self.order_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.order_slider.setRange(1, 10)
        self.order_slider.setValue(5)
        self.order_label = QtWidgets.QLabel(str(self.order_slider.value()))
        self.order_slider.valueChanged.connect(lambda v: self.order_label.setText(str(v)))
        order_widget = self.create_slider_widget("Filter Order:", self.order_slider, self.order_label)
        controls_layout.addRow(order_widget)

        # Apply Button
        apply_btn = QtWidgets.QPushButton("Apply Filter")
        apply_btn.clicked.connect(self.apply_filter)
        controls_layout.addRow(apply_btn)

        # Save Filtered Data Button
        self.save_btn = QtWidgets.QPushButton("Save Filtered Data")
        self.save_btn.clicked.connect(self.save_filtered_data)
        self.save_btn.setEnabled(False) # Disabled until data is filtered
        controls_layout.addRow(self.save_btn)

        controls_group.setLayout(controls_layout)
        controls_vbox.addWidget(controls_group)
        controls_vbox.addStretch()

        main_hbox.addLayout(controls_vbox, 1) # 25% width for controls

        layout.addLayout(main_hbox)

        self.setLayout(layout)
        self.update_control_visibility()

    def create_slider_widget(self, label_text, slider, value_label):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(QtWidgets.QLabel(label_text))
        layout.addWidget(slider)
        layout.addWidget(value_label)
        widget.setLayout(layout)
        return widget

    def start_session(self, username, user_manager):
        """Called when user logs in."""
        self.current_user = username
        self.user_manager = user_manager
        self.populate_session_selector()

    def populate_session_selector(self):
        """Fills the session selector combobox with the user's sessions."""
        self.session_selector.clear()
        self.session_selector.addItem("Select a session to load...")
        if not self.user_manager or not self.current_user:
            return

        user_data = self.user_manager.users.get(self.current_user, {})
        history = user_data.get("history", [])

        for i, session in enumerate(reversed(history)):
            if "raw_ppg" in session and session["raw_ppg"]:
                date_str = session.get("start", f"Session {len(history)-i}")
                self.session_selector.addItem(f"{date_str}", userData=session)

    def load_selected_session(self, index):
        """Loads the raw PPG data from the selected session and plots it."""
        if index <= 0:
            self.raw_ppg_signal = np.array([])
            self.original_curve.setData([])
            self.filtered_curve.setData([])
            self.save_btn.setEnabled(False)
            return

        session_data = self.session_selector.itemData(index)
        self.raw_ppg_signal = np.array(session_data.get("raw_ppg", []))

        if self.raw_ppg_signal.size > 0:
            # Assuming 50Hz sampling rate from ESP32 packet structure (50 samples per packet)
            self.sampling_rate = 50
            time_axis = np.arange(len(self.raw_ppg_signal)) / self.sampling_rate
            self.original_curve.setData(time_axis, self.raw_ppg_signal)
            self.original_plot.autoRange()
            self.filtered_curve.clear() # Clear filtered plot on new load

    def update_control_visibility(self):
        """Shows/hides cutoff sliders based on selected filter type."""
        filter_type = self.filter_type_combo.currentText()
        if filter_type == "Bandpass":
            self.low_cutoff_widget.setVisible(True)
            self.high_cutoff_widget.setVisible(True)
        elif filter_type == "Low-pass":
            self.low_cutoff_widget.setVisible(False)
            self.high_cutoff_widget.setVisible(True)
        elif filter_type == "High-pass":
            self.low_cutoff_widget.setVisible(True)
            self.high_cutoff_widget.setVisible(False)

    def apply_filter(self):
        """Applies the selected filter to the raw signal and plots the result."""
        if self.raw_ppg_signal.size == 0:
            print("No signal loaded to filter.")
            self.save_btn.setEnabled(False)
            return

        filter_type = self.filter_type_combo.currentText()
        order = self.order_slider.value()

        fs = self.sampling_rate
        nyquist = 0.5 * fs

        # Normalise between [0, 1]
        lowcut = self.low_cutoff_slider.value() / nyquist
        highcut = self.high_cutoff_slider.value() / nyquist

        try:
            b, a = self.butter_filter(lowcut, highcut, self.sampling_rate, order, btype=filter_type.lower())
            self.filtered_ppg_signal = filtfilt(b, a, self.raw_ppg_signal)

            time_axis = np.arange(len(self.filtered_ppg_signal)) / self.sampling_rate
            self.filtered_curve.setData(time_axis, self.filtered_ppg_signal)
            self.filtered_plot.autoRange()
            self.save_btn.setEnabled(True)
        except ValueError as e:
            print(f"Error applying filter: {e}")
            self.save_btn.setEnabled(False)
            
            # show error to user
            msg_box = QtWidgets.QMessageBox()
            msg_box.setIcon(QtWidgets.QMessageBox.Warning)
            msg_box.setText("Filter Error")
            msg_box.setInformativeText(f"Could not apply filter. Check parameters.\nError: {e}")
            msg_box.setWindowTitle("Warning")
            msg_box.exec_()

            msg_box.setWindowTitle("Warning")
            msg_box.exec_()

    def save_filtered_data(self):
        """Saves the filtered PPG signal to a CSV file."""
        if self.filtered_ppg_signal.size == 0:
            QtWidgets.QMessageBox.warning(self, "No Data", "There is no filtered data to save.")
            return

        # Suggest a filename
        selected_session_text = self.session_selector.currentText().split("T")[0]
        filename = f"filtered_ppg_{self.current_user}_{selected_session_text}.csv"

        # Open file dialog
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save Filtered Data",
            filename,
            "CSV Files (*.csv);;All Files (*)",
            options=options
        )

        if file_path:
            try:
                time_axis = np.arange(len(self.filtered_ppg_signal)) / self.sampling_rate
                data_to_save = np.vstack((time_axis, self.filtered_ppg_signal)).T
                np.savetxt(file_path, data_to_save, delimiter=',', header='Time (s),Filtered PPG', comments='')
                QtWidgets.QMessageBox.information(self, "Success", f"Data saved successfully to:\n{os.path.basename(file_path)}")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", f"Failed to save data.\nError: {e}")






    def butter_filter(self, lowcut, highcut, fs, order=5, btype='band'):
        """
        Designs a Butterworth filter.

        Args:
            lowcut (float): Lower cutoff frequency (Hz).
            highcut (float): Higher cutoff frequency (Hz).
            fs (int): Sampling rate (Hz).
            order (int): Filter order.
            btype (str): Type of filter {'lowpass', 'highpass', 'bandpass'}.

        Returns:
            tuple: Numerator (b) and denominator (a) polynomials of the IIR filter.
        """
        nyquist = 0.5 * fs
        
        if btype == 'low-pass':
            high = highcut / nyquist
            b, a = butter(order, high, btype='low')
        elif btype == 'high-pass':
            low = lowcut / nyquist
            b, a = butter(order, low, btype='high')
        else: # bandpass
            low = lowcut / nyquist
            high = highcut / nyquist
            b, a = butter(order, [low, high], btype='band')
            
        return b, a