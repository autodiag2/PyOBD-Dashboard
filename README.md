# PyOBD Professional Dashboard

A modern, open-source OBD-II diagnostic tool and dashboard built with Python. Designed to work with **ELM327 USB adapters**, this tool allows you to monitor vehicle sensors in real-time, read/clear check engine lights, and log data for analysis.

## Features

*   **Live Dashboard:** Real-time visualization of RPM, Speed, Coolant Temp, Voltage, and more.
*   **Customizable Layout:** Toggle which sensors you want to see on the screen via the Settings tab.
*   **Data Logging:** Automatically save sensor data to CSV files for Excel/Sheets analysis.
*   **Diagnostics:** Read and Clear Diagnostic Trouble Codes (DTCs / Check Engine Light).
*   **Safety Backups:** "Full Backup" feature saves a snapshot of the car's state (Freeze Frame data + Codes) to a JSON file before you wipe them.
*   **Simulation Mode:** Develop and test the UI without being connected to a car.
*   **Dark Mode UI:** Built with `CustomTkinter` for a modern look.

## Hardware Requirements

*   **Computer:** Windows, Linux, or macOS.
*   **Adapter:** ELM327 USB Adapter.
    *   *Recommended:* Version with **PIC18F25K80** chip and **FTDI** or **CH340** USB drivers.
    *   *Note:* Avoid generic "blue" KKL/VAG-COM cables; they are not ELM327 compatible.

## 📦 Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/YOUR_USERNAME/PyOBD-Dashboard.git
    cd PyOBD-Dashboard
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Connect your Adapter:**
    *   Plug the ELM327 USB into your computer.
    *   Plug the other end into your car's OBD-II port.
    *   Turn the ignition to **ON** (Engine can be off or running).

## Usage

Run the main script:
```bash
python src/main.py
```
## Disclaimer
This software is provided "as is". Clearing fault codes does not fix the underlying mechanical problem. Always backup your codes using the "Full Backup" feature before clearing them so you have a record for your mechanic.

##  License

Open Source. Feel free to fork and improve!