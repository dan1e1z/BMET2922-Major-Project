# PPG Health Monitor

A real-time Photoplethysmography (PPG) signal visualizer and heart rate monitor with a Python-based GUI.

## Table of Contents

- [PPG Health Monitor](#ppg-health-monitor)
  - [Table of Contents](#table-of-contents)
  - [About The Project](#about-the-project)
    - [Features](#features)
    - [Built With](#built-with)
  - [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
  - [Usage](#usage)

## About The Project

This project, developed for the BMET2922 course, is a desktop application for real-time health monitoring using a PPG sensor connected via Bluetooth. It captures raw PPG data, calculates beats per minute (BPM), and displays the information through an intuitive graphical user interface.

### Features
*   **Live Data Visualization**: Real-time plotting of raw PPG signals and calculated heart rate.
*   **User Account Management**: Simple login system to manage and save session data for different users.
*   **Session History**: Stores and displays historical session data, including average/min/max BPM and duration.
*   **Configurable Alarms**: Set custom high and low BPM thresholds with visual alerts for abnormal readings.
*   **Bluetooth Connectivity**: Connects to an ESP32-based PPG sensor to stream data wirelessly.

### Built With
* [Python](https://www.python.org/)
* [PyQt5](https://riverbankcomputing.com/software/pyqt/) for the Graphical User Interface (GUI)
* [NumPy](https://numpy.org/)
* [PyQtGraph](http://www.pyqtgraph.org/) for high-performance plotting
* [PySerial](https://pyserial.readthedocs.io/) for Bluetooth communication

## Getting Started

This section will guide a user or developer on how to get your project set up and running on their local machine.

### Prerequisites

This project requires Python 3.8+ and `pip` to be installed.

You can install the necessary Python packages using the `requirements.txt` file.

### Installation

1.  **Clone the repository**
   ```sh
   git clone https://github.com/your_username/ppg_health_monitor.git
   cd ppg_health_monitor
   ```

2.  **Create and activate a virtual environment**

    This is highly recommended to avoid conflicts with other Python projects.

    *   On **macOS/Linux**:
        ```sh
        python3 -m venv venv
        source venv/bin/activate
        ```

    *   On **Windows**:
        ```sh
        python -m venv venv
        .\venv\Scripts\activate
        ```

3.  **Install the required packages**

    You can install all dependencies from the `requirements.txt` file.
    ```sh
    pip install -r requirements.txt
    ```

    Alternatively, you can install the project in **editable mode** using its pyproject.toml file.    
    ```sh
    pip install -e .
    ```

## Usage

To run the application, ensure your virtual environment is activated and execute the `main.py` script from the project's root directory:
```sh
python ppg_health_monitor/main.py
```
