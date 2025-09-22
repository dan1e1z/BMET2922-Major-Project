from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg
import numpy as np 
from datetime import datetime


class LiveMonitorTab(QtWidgets.QWidget):

    """
    A PyQt5 widget for real-time heart rate monitoring with visual plots and alarm system.
    
    This class provides:
    - Real-time BPM and raw PPG signal visualization
    - User session management and data logging
    - Configurable BPM alarm thresholds with visual/audio alerts
    - Live statistics display
    
    Attributes:
        current_user (str): Currently logged in user
        session_raw_ppg (list): Raw PPG data for current session
        session_start_time (datetime): When current session started
        session_bpm (list): BPM readings for current session
        visual_bpm_data (list): BPM data used for plotting
        visual_raw_pgg_data (list): Raw PPG data used for plotting
        current_bpm (float): Most recent BPM reading
        bpm_low (int): Lower threshold for BPM alarm (default: 40)
        bpm_high (int): Upper threshold for BPM alarm (default: 200)
        alarm_active (bool): Whether alarm is currently triggered
    """
    def __init__(self, system_log):
        super().__init__()

        # User/session management variables
        self.current_user = None  # Currently logged in user
        self.session_raw_ppg = []  # Raw PPG data for current session
        self.session_start_time = None  # Timestamp when session started
        self.session_bpm = []  # BPM readings collected during session

        # System log widget for displaying messages
        self.system_log = system_log

        # Data arrays used for real-time visualization
        self.visual_bpm_data = []  # BPM values to display on chart
        self.visual_raw_pgg_data = []  # Raw PPG values to display on chart
        self.current_bpm = 0  # Most recent BPM reading

        # Default alarm thresholds (adjustable via sliders)
        self.bpm_low = 40   # Lower BPM threshold - triggers "low pulse" alarm
        self.bpm_high = 200  # Upper BPM threshold - triggers "high pulse" alarm

        # Alarm system state
        self.alarm_active = False  # Whether an alarm condition is currently active

        # Initialize the user interface
        self.setup_ui()

    def setup_ui(self):
        """
        Set up the UI for the live monitor tab, including plots and controls with proper layout and stretch factors.
        
        Creates:
        - Two real-time plots (BPM and raw PPG)
        - BPM display and alarm indicators
        - Threshold adjustment sliders
        - Session information display
        """
        # Main vertical layout for the tab
        main_layout = QtWidgets.QVBoxLayout()

        # --- Plots layout ---
        # This layout will stack the BPM and raw PPG plots vertically
        plots_layout = QtWidgets.QVBoxLayout()

        # BPM Plot: Real-time heart rate visualization
        self.bpm_plot = pg.PlotWidget()
        self.bpm_plot.setLabel('left', 'BPM')  # Y-axis label
        self.bpm_plot.setLabel('bottom', 'Time', units='s')  # X-axis label
        self.bpm_plot.showGrid(True, True)  # Show grid lines
        self.bpm_plot.setMouseEnabled(x=False, y=False)  # Disable mouse interaction
        self.bpm_plot.setMenuEnabled(False)  # Disable context menu
        # self.bpm_plot.enableAutoRange(False)  # Prevent auto-scaling
        self.bpm_curve = self.bpm_plot.plot(pen=pg.mkPen('r', width=2))  # Red curve for BPM
        plots_layout.addWidget(self.bpm_plot)

        # Raw PPG Plot: shows raw photoplethysmogram signal
        self.raw_ppg_plot = pg.PlotWidget()
        self.raw_ppg_plot.setLabel('left', 'PPG Raw')  # Y-axis label
        self.raw_ppg_plot.setLabel('bottom', 'Time', units='s')  # X-axis label
        self.raw_ppg_plot.showGrid(True, True)  # Show grid lines
        self.raw_ppg_plot.setMouseEnabled(x=False, y=False)  # Disable mouse interaction
        self.raw_ppg_plot.setMenuEnabled(False)  # Disable context menu
        # self.raw_ppg_plot.enableAutoRange(False)  # Prevent auto-scaling
        self.raw_ppg_curve = self.raw_ppg_plot.plot(pen=pg.mkPen('b', width=2))  # Blue curve for PPG
        plots_layout.addWidget(self.raw_ppg_plot)

        # Session info label (aligned right, can show user/session status)
        self.session_info = QtWidgets.QLabel("Not logged in")
        self.session_info.setAlignment(QtCore.Qt.AlignRight)

        # --- Right side controls ---
        # Controls layout for widgets like BPM display and future controls
        controls_layout = QtWidgets.QVBoxLayout()
        controls_widget = QtWidgets.QWidget()

        # BPM display: shows current BPM value
        self.bpm_display = QtWidgets.QLabel("-- BPM")
        self.bpm_display.setAlignment(QtCore.Qt.AlignCenter)

        # Alarm
        self.alarm_widget = QtWidgets.QLabel("")
        self.alarm_widget.setAlignment(QtCore.Qt.AlignCenter)
        self.alarm_widget.setVisible(False) # Hidden until alarm triggered

        # Stats
        self.current_stats = QtWidgets.QLabel("")
        self.current_stats.setAlignment(QtCore.Qt.AlignCenter)
        self.current_stats.setWordWrap(True)

        # Sliders for warning thresholds
        self.low_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.low_slider.setRange(20, 100)
        self.low_slider.setValue(self.bpm_low)
        self.low_slider.valueChanged.connect(self.update_thresholds)

        self.high_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.high_slider.setRange(120, 250)
        self.high_slider.setValue(self.bpm_high)
        self.high_slider.valueChanged.connect(self.update_thresholds)

        # Labels showing current threshold values
        self.low_label = QtWidgets.QLabel(f"Low BPM Warning: {self.bpm_low}")
        self.high_label = QtWidgets.QLabel(f"High BPM Warning: {self.bpm_high}")

        # Add all controls to the layout
        controls_layout.addWidget(self.bpm_display)
        controls_layout.addWidget(self.alarm_widget)
        controls_layout.addWidget(self.current_stats)
        controls_layout.addWidget(self.low_label)
        controls_layout.addWidget(self.low_slider)
        controls_layout.addWidget(self.high_label)
        controls_layout.addWidget(self.high_slider)
        controls_layout.addStretch()

        
        controls_widget.setLayout(controls_layout)

         # Combine plots (75%) and controls (25%) horizontally
        content_layout = QtWidgets.QHBoxLayout()
        content_layout.addLayout(plots_layout, 3) # 3/4 of space for plots
        content_layout.addWidget(controls_widget, 1) # 1/4 of space for controls
        main_layout.addLayout(content_layout)

        # Add system log widget at the bottom
        main_layout.addWidget(self.system_log)

        # Set the main layout for this tab
        self.setLayout(main_layout)

        #  --- Alarm Blinking System ---
        # Timer for creating blinking alarm effect
        self.alarm_timer = QtCore.QTimer()
        self.alarm_timer.timeout.connect(self.blink_alarm)
        self.alarm_visible = True

    def new_data_received(self, packet):
        """
        Process new data packet from heart rate sensor.
        
        This method:
        1. Extracts BPM and PPG values from the packet
        2. Updates the current BPM display
        3. Checks for alarm conditions (BPM too high/low)
        4. Adds data to session if user is logged in
        5. Updates the real-time plots
        
        Args:
            packet (dict): Data packet containing:
                - 'bpm': Current beats per minute reading
                - 'ppg_values': List of raw PPG sensor values
                
        Returns:
            str or None: Alarm message if alarm state changed, None otherwise
        """
        
        # DEBUGGING PRINTS
        # print("packet: ", packet)
        # print ("bpm: ", packet['bpm'])
        # print("ppg_values:", packet["ppg_values"])

        bpm = packet['bpm']
        self.current_bpm = packet['bpm']

        if  bpm > 0:
            # Update the large BPM display
            self.bpm_display.setText(f"{bpm:.1f} BPM")

            # check for valid bpm (low < bpm < high)
            alarm_msg = self.check_bpm_alarm()
            if alarm_msg:
                return alarm_msg
            

            # add bpm to logined user session data
            # print("self.current_user: ", self.current_user)
            if self.current_user:
                # print("adding bpm to session")
                self.session_bpm.append(bpm)
        else:
            self.bpm_display.setText("-- BPM")

        # Store data for plotting
        self.visual_bpm_data.append(bpm)
        self.visual_raw_pgg_data.extend(packet["ppg_values"])

        # update render plots
        self.update_plots()
        return

    def update_plots(self):
        """
        Update both BPM and PPG plots with latest data.
        
        This method redraws the plot curves with the accumulated data arrays.
        Only updates if there's sufficient data (> 1 point) to avoid errors.
        """
        if len(self.visual_bpm_data) > 1:
            self.bpm_curve.setData(np.arange(len(self.visual_bpm_data)), np.array(self.visual_bpm_data))
        if len(self.visual_raw_pgg_data) > 1:
            self.raw_ppg_curve.setData(np.arange(len(self.visual_raw_pgg_data)), np.array(self.visual_raw_pgg_data))


    def start_session(self, username):
        """
        Start a new monitoring session for a user.
        
        Args:
            username (str): Name of user starting the session
        """
        self.current_user = username
        self.session_start_time = datetime.now()
        self.update_session_info()

    def update_session_info(self):
        """
        Update the session information display with current stats.
        
        Shows:
        - Recording duration
        - Number of BPM samples collected
        - Current and average BPM for the session
        """
        if self.current_user and self.session_start_time:
            duration = datetime.now() - self.session_start_time
            minutes = duration.total_seconds() / 60
            self.session_info.setText(f"Recording: {minutes:.1f} min | Samples: {len(self.session_bpm)}")
            
            # Update current session statistics
            if self.session_bpm:
                current_bpm = self.session_bpm[-1] if self.session_bpm else 0
                avg_bpm = np.mean(self.session_bpm)
                
                stats_text = f"Current: {current_bpm:.1f} BPM\nAvg: {avg_bpm:.1f}"
                self.current_stats.setText(stats_text)
        else:
            self.session_info.setText("Not recording")
            self.current_stats.setText("Please log in to start recording session data")

    def update_thresholds(self):
        """
        Update BPM alarm thresholds based on slider values.
        
        Called automatically when user moves either threshold slider.
        Updates both the internal threshold values and the display labels.
        """
        # Get new threshold values from sliders
        self.bpm_low = self.low_slider.value()
        self.bpm_high = self.high_slider.value()

        # Update the labels to show current threshold values
        self.low_label.setText(f"Low BPM Warning: {self.bpm_low}")
        self.high_label.setText(f"High BPM Warning: {self.bpm_high}")

    def blink_alarm(self):
        """
        Create blinking effect for alarm widget.
        
        This method is called repeatedly by the alarm timer when an alarm is active.
        It toggles the visibility of the alarm widget to create a blinking effect
        that draws attention to the alarm condition.
        """
        if self.alarm_active:
            # Toggle visibility state
            self.alarm_visible = not self.alarm_visible
            self.alarm_widget.setVisible(self.alarm_visible)

    def check_bpm_alarm(self):
        """
        Check current BPM against thresholds and manage alarm state.
        
        **HOW THE ALARM SYSTEM WORKS:**
        
        1. **Threshold Comparison**: Compares current BPM against user-configurable 
           low and high thresholds (default: 40-200 BPM)
           
        2. **Alarm Activation**: 
           - If BPM < low_threshold: Activates "PULSE LOW" alarm
           - If BPM > high_threshold: Activates "PULSE HIGH" alarm
           - If BPM within range: Deactivates any active alarm
           
        3. **Visual Feedback**:
           - Shows warning message in alarm_widget with current BPM
           - Starts blinking timer (500ms intervals) for attention-grabbing effect
           - Uses red text to indicate dangerous condition
           
        4. **State Management**:
           - Tracks previous alarm state to detect transitions
           - Only starts blinking timer when alarm first activates
           - Stops timer and hides alarm when BPM returns to normal
           
        5. **Return Messages**:
           - Returns status message when alarm state changes
           - Used by calling code for logging/notification purposes
           - Messages: "Pulse Low", "Pulse High", "Pulse Normal"
        
        Returns:
            str or None: Message indicating alarm state change, or None if no change
        """
        # Store previous alarm state to detect transitions
        prev_state = self.alarm_active
        msg = None

        # Check for LOW BPM alarm condition
        if self.current_bpm < self.bpm_low:
            self.alarm_active = True
            # Set alarm message with current BPM value
            self.alarm_widget.setText(f"WARNING: PULSE LOW: {self.current_bpm:.1f} BPM")
            
            # Start blinking only if this is a new alarm (state changed)
            if not prev_state:
                self.alarm_timer.start(500)  # Blink every 500ms
                msg = "Pulse Low"  # Message for system log
                
        # Check for HIGH BPM alarm condition  
        elif self.current_bpm > self.bpm_high:
            self.alarm_active = True
            # Set alarm message with current BPM value
            self.alarm_widget.setText(f"WARNING: PULSE HIGH: {self.current_bpm:.1f} BPM")
            
            # Start blinking only if this is a new alarm (state changed)
            if not prev_state:
                self.alarm_timer.start(500)  # Blink every 500ms
                msg = "Pulse High"  # Message for system log
                
        # BPM is within normal range
        else:
            # If we were previously in alarm state, clear the alarm
            if prev_state:
                self.alarm_active = False
                self.alarm_widget.setVisible(False)  # Hide alarm widget
                self.alarm_timer.stop()  # Stop blinking
                msg = "Pulse Normal"  # Message for system log
                
        return msg