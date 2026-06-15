# Project Overview - **Load cell**

This document describes the Bill of Materials (BOM), hardware connections, and software components of a system designed to monitor the weight of four 500 mL beakers that gradually fill with water. The system uses an ESP32 microcontroller to interface with load cells and transmit measurement data to a computer for logging and visualization.

The device is intended for use in a constant-head saturated hydraulic conductivity setup. By continuously monitoring the mass of water collected from the outflow of soil cores, the system enables accurate determination of flow rates and supports the calculation of saturated hydraulic conductivity.

---

# Folder structure

- **3D_model/**
  - Fusion 360 design files and STEP models ready for 3D printing.

- **MCU_scr/**
  - PlatformIO project containing the firmware source code for the ESP32 microcontroller.

- **Software/**
  - Python-based graphical user interface (GUI).

- **data/**
  - Calibration files (`.json`) and measurement data.

- **install.bat**
  - Installation script used to verify and install the required software packages and dependencies.
---

# Bill of Materials (BOM)

| Item | Quantity | Description / Purpose | Estimated Cost per piece (Tabao) |
|:---|:---:|:---|:---|
| **ESP32 Devkit-c** | 1 | Microcontroller with high frequencing capabilities. | 65 RMB |
| **1kg Load Cells** | 4 | Straight bar (straight-beam) load cells TAL220. Choose 1kg capacity to account for the beaker's tare weight. | 50 RMB |
| **HX711 Modules** | 4 | 24-bit Analog-to-Digital Converter (ADC) designed specifically for weigh scales. | 39 RMB |
| **Support plates** | 8 | Two plates per load cell (one for the base, one for the beaker platform). | |
| **M4 / M5 Screws & Spacers** | 1 set | Required to mount the load cells to the plates in a "Z" configuration to allow bending. | |
| **Jumper Wires** | 1 pack | Dupont wires (Female-to-Female, Male-to-Male) for connections. |  |
| **Micro-USB / USB-C Cable** | 1 | For powering the ESP32 and serial communication with the computer. |  |

---

# Wiring Connections

The system consists of three main stages of wiring:
1. Load Cell to HX711 Amplifier
2. HX711 Amplifiers to ESP32
3. ESP32 to Computer

## 1. Load Cell to HX711

Each load cell has 4 wires (forming a Wheatstone bridge). Connect them to their respective HX711 module:

| Load Cell Wire Color | HX711 Pin | Description |
|:---|:---|:---|
| **Red** | E+ | Excitation Plus |
| **Black** | E- | Excitation Minus |
| **White** | A- | Signal Minus |
| **Green** | A+ | Signal Plus |

## 2. HX711 to ESP32

Each HX711 requires power and two data pins (Data/DT and Clock/SCK). Since the ESP32 uses 3.3V logic, it's best to power the HX711 modules using the 3.3V pin from the ESP32 to ensure safe logic levels.

| HX711 Pin | ESP32 Pin (Suggested) | Notes |
|:---|:---|:---|
| VCC / VDD | 3V3 | Power (Use 3.3V for logic safety) |
| GND | GND | Ground |
| **Module 1 DT** | GPIO 16 | Data Line for Beaker 1 |
| **Module 1 SCK**| GPIO 17 | Clock Line for Beaker 1 |
| **Module 2 DT** | GPIO 18 | Data Line for Beaker 2 |
| **Module 2 SCK**| GPIO 19 | Clock Line for Beaker 2 |
| **Module 3 DT** | GPIO 22 | Data Line for Beaker 3 |
| **Module 3 SCK**| GPIO 23 | Clock Line for Beaker 3 |
| **Module 4 DT** | GPIO 32 | Data Line for Beaker 4 |
| **Module 4 SCK**| GPIO 33 | Clock Line for Beaker 4 |

## 3. ESP32 to USB Serial Connection 
The ESP32 is connected to the computer via the USB serial connection. 

# Esp 32 programmation
The ESP32 microcontroller (MCU) must be programmed before use. The firmware has been developed using the 'PlatformIO' framework.
Users should refer to the PlatformIO documentation for instructions on setting up the development environment, compiling the project, and uploading the firmware to the ESP32.
Once PlatformIO is installed, open the project folder and follow the standard PlatformIO procedure to build and flash the firmware to the MCU.

---

# How to Use

## 1. First-Time Setup
Before running the software for the first time, you must install the required dependencies:
1. Double-click the `install.bat` file located in the main project folder.
2. This will automatically install all the necessary Python packages. You only need to do this once.

## 2. Running the Software
1. Double-click `Run_Load_Cell.bat` in the main folder to launch the Load Cell Monitor application.
2. Ensure your ESP32 is plugged into the computer via USB.
3. In the application's left panel, click **Refresh Ports**, select the correct COM port for your ESP32, and click **Connect**.

## 3. Calibration
Before starting a measurement, it is highly recommended to calibrate your scales:
1. Ensure the scale platform is empty (or holds an empty beaker), then click **Tare** on the corresponding scale to set its baseline to zero.
2. Place a known weight (e.g., 500g) on the scale.
3. Enter the exact weight in the "Known Wt (g)" box and click **Calibrate**.
4. The software will automatically save a record of this calibration to the `Software/data/calibration_data/calibration_history.csv` file so you can track sensor accuracy over time.

## 4. Logging Data
1. For each scale you want to record, enter a **Name** for your measurement and choose the logging **Interval(s)** (in seconds).
2. Click **Start Logging**.
3. The software will begin recording the weight at your chosen interval. 
4. Measurement data is saved continuously as CSV files inside the `Software/data/` folder.



# Contact 
Rémy Willemet : remy.willemet@ilvo.vlaanderen.be