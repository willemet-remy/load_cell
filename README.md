# Project Overview - Load cell

This document outlines the Bill of Materials (BOM) and connection for monitoring the weight of four 500ml beakers filling with water slowly. The system uses an ESP32 microcontroller to interface with load cells and transmits the data to a computer. This load cell will be use in a constant head soil saturated conductivity set-up. It will allow the flow measurements passing trough a soil core. 

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

# Implementation Options

Here are the different ways you can tackle the data transmission and processing.

## USB Serial Connection (Recommended for Simplicity)
- **How it works:** The ESP32 is plugged into the computer via USB. A Python/R script on the computer reads the COM port in real-time.
- **Pros:** Extremely simple to code. Very reliable (no network dropouts). Powers the ESP32 directly from the PC.
- **Cons:** The ESP32 must be physically tethered to the computer.

---

# Questions
1. Where to order the components.
2. How to produce the mechanical mounting for the load cells. 
3. Can we have access to electronic equipment: cables (4 cores and 2 cores) and soldering iron
4. How to produce the 8 supports. Is there a 3D printer that I can use somewhere?  


### Contact 
Rémy Willemet : remy.willemet@ilvo.vlaanderen.be