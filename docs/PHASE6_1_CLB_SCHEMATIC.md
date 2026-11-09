# FPGA-H1 — Phase 6.1: Physical CLB Electrical Schematic & Pin-to-Pin Netlist

## 1. Electrical Architecture Overview

`FPGA-H1-PROTOTYPE-001` is implemented on a **2-Layer FR4 printed circuit board ($100 \times 80\text{ mm}$)** operating at a unified supply voltage of **$V_{CC} = +3.3\text{V}$**.

```mermaid
flowchart TD
    subgraph Power ["Power & Supply"]
        USB["USB 5V (from PC)"] --> LDO["3.3V Low-Dropout Regulator (AP2112K)"]
        LDO --> VCC["+3.3V Power Plane"]
        VCC --> DECOUP["18 x 0.1uF Decoupling + 2 x 10uF Tantalum"]
    end

    subgraph HostBridge ["RP2040 Config Bridge"]
        PICO["Raspberry Pi Pico Module"]
        PICO -->|SPI (MOSI, SCK, LATCH)| CFG_CHAIN
        PICO -->|Control (RST_N, CLK_OUT)| CONTROL_BUS
    end

    subgraph LogicTile ["1-CLB FPGA-H1 Core"]
        CFG_CHAIN["9 x 74HC595 Shift Chain (72 Bits)"]
        LUT_ARRAY["4 x 74HC4067 (4 x LUT4 16:1 Mux)"]
        DFF_ARRAY["2 x 74HC74 (4 x DFF Registers)"]
        MUX_ARRAY["3 x 74HC4053 (Independent 2:1 Bypass & Carry Muxes)"]
        
        CFG_CHAIN -->|64 LUT Bits| LUT_ARRAY
        CFG_CHAIN -->|4 Bypass Bits| MUX_ARRAY
        CFG_CHAIN -->|4 Carry Bits| MUX_ARRAY
        LUT_ARRAY --> DFF_ARRAY & MUX_ARRAY
        DFF_ARRAY --> MUX_ARRAY
    end

    subgraph IO_Headers ["External Physical Interface"]
        J_IN["J1: 16-Bit Logic Input Header"] --> LUT_ARRAY
        MUX_ARRAY --> J_OUT["J2: 4-Bit Logic Output Header"]
        CONTROL_BUS --> DFF_ARRAY
    end
```

---

## 2. Integrated Circuit (IC) Netlist & Reference Designators

| Designator | Component Model | Package | Quantity | Subsystem / Electrical Function |
| :---: | :--- | :--- | :---: | :--- |
| **U1** | **CD74HC4067SM96** | SSOP-24 | 1 | **BLE 0 Look-Up Table** (LUT4 16:1 Multiplexer) |
| **U2** | **CD74HC4067SM96** | SSOP-24 | 1 | **BLE 1 Look-Up Table** (LUT4 16:1 Multiplexer) |
| **U3** | **CD74HC4067SM96** | SSOP-24 | 1 | **BLE 2 Look-Up Table** (LUT4 16:1 Multiplexer) |
| **U4** | **CD74HC4067SM96** | SSOP-24 | 1 | **BLE 3 Look-Up Table** (LUT4 16:1 Multiplexer) |
| **U5, U6** | **SN74HC595DR** | SOIC-16 | 2 | **LUT 0 Configuration Storage** (Low Byte, High Byte) |
| **U7, U8** | **SN74HC595DR** | SOIC-16 | 2 | **LUT 1 Configuration Storage** (Low Byte, High Byte) |
| **U9, U10** | **SN74HC595DR** | SOIC-16 | 2 | **LUT 2 Configuration Storage** (Low Byte, High Byte) |
| **U11, U12**| **SN74HC595DR** | SOIC-16 | 2 | **LUT 3 Configuration Storage** (Low Byte, High Byte) |
| **U13** | **SN74HC595DR** | SOIC-16 | 1 | **Architectural Control Latch** (4 Bypass bits + 4 Carry bits) |
| **U14** | **SN74HC74DR** | SOIC-14 | 1 | **BLE 0 & BLE 1 D-Type Flip-Flops** |
| **U15** | **SN74HC74DR** | SOIC-14 | 1 | **BLE 2 & BLE 3 D-Type Flip-Flops** |
| **U16** | **CD74HC4053M96** | SOIC-16 | 1 | **BLE 0, 1, 2 Bypass Multiplexers** (3 Indep. 2:1 Muxes) |
| **U17** | **CD74HC4053M96** | SOIC-16 | 1 | **BLE 3 Bypass + BLE 0, 1 Carry Muxes** (3 Indep. 2:1 Muxes) |
| **U18** | **CD74HC4053M96** | SOIC-16 | 1 | **BLE 2, 3 Carry Muxes + Spare** (3 Indep. 2:1 Muxes) |
| **U19** | **Raspberry Pi Pico** | Module | 1 | **Configuration Controller Bridge** (RP2040) |
| **Total ICs**| — | — | **19 ICs**| Full 1-CLB Prototype Board |

---

## 3. Detailed Pin-to-Pin Wiring Netlist

### 3.1 Configuration Scan Chain Cascade
- `RP2040 GPIO 16 (MOSI)` $\to$ `U13 Pin 14 (SER)`
- `U13 Pin 9 (QH')` $\to$ `U12 Pin 14 (SER)`
- `U12 Pin 9 (QH')` $\to$ `U11 Pin 14 (SER)`
- `U11 Pin 9 (QH')` $\to$ `U10 Pin 14 (SER)`
- `U10 Pin 9 (QH')` $\to$ `U9 Pin 14 (SER)`
- `U9 Pin 9 (QH')` $\to$ `U8 Pin 14 (SER)`
- `U8 Pin 9 (QH')` $\to$ `U7 Pin 14 (SER)`
- `U7 Pin 9 (QH')` $\to$ `U6 Pin 14 (SER)`
- `U6 Pin 9 (QH')` $\to$ `U5 Pin 14 (SER)`
- `U5 Pin 9 (QH')` $\to$ `RP2040 GPIO 17 (MISO)` (Configuration Verification Readback)
- **Common Clocks & Controls (Tied to all U5..U13 in parallel)**:
  - `RP2040 GPIO 18 (SCK)` $\to$ Pin 11 (`SRCLK`)
  - `RP2040 GPIO 19 (LATCH)` $\to$ Pin 12 (`RCLK`)
  - `RP2040 GPIO 20 (OE_N)` $\to$ Pin 13 (`/OE`) (Pulled up to 3.3V via 10k resistor)
  - Pin 10 (`/SRCLR`) $\to$ Tied to `+3.3V` via 10k resistor.

### 3.2 LUT4 Core Connections (U1 .. U4)
- **LUT 0 (U1)**:
  - Pins 9, 10, 11, 14 ($S_3, S_2, S_1, S_0$) $\to$ `IN[3], IN[2], IN[1], IN[0]` (Header J1)
  - Pins 9..2, 23..16 ($Y_0..Y_{15}$) $\to$ Driven by `U5` ($Q_A..Q_H$) and `U6` ($Q_A..Q_H$)
  - Pin 15 (`/E`) $\to$ Tied to `GND` (Permanently enabled) or RP2040 `/MUTE`
  - Pin 1 ($Z$) $\to$ `LUT0_OUT` net $\to$ Connects to:
    - U14 Pin 2 ($D$ input of DFF 0)
    - U16 Pin 12 (Input 1 of Bypass Mux 0)
    - U17 Pin 1 (Select input of Carry Mux 0)

### 3.3 Independent Bypass Multiplexers (U16, U17: 74HC4053)
Each channel of 74HC4053 has its own independent select pin:
- **BLE 0 Bypass (U16 Channel A)**:
  - Pin 11 ($S_A$) $\to$ `U13 Pin 15 (Q_A, BLE0_BYPASS)`
  - Pin 12 ($2X$, Select=1) $\to$ `LUT0_OUT`
  - Pin 13 ($1X$, Select=0) $\to$ `BLE0_Q` (U14 Pin 5)
  - Pin 14 ($X$, Output) $\to$ `OUT[0]` (Header J2)
- **BLE 1 Bypass (U16 Channel B)**:
  - Pin 10 ($S_B$) $\to$ `U13 Pin 1 (Q_B, BLE1_BYPASS)`
  - Pin 1 ($2Y$, Select=1) $\to$ `LUT1_OUT`
  - Pin 2 ($1Y$, Select=0) $\to$ `BLE1_Q` (U14 Pin 9)
  - Pin 15 ($Y$, Output) $\to$ `OUT[1]` (Header J2)
- **BLE 2 Bypass (U16 Channel C)**:
  - Pin 9 ($S_C$) $\to$ `U13 Pin 2 (Q_C, BLE2_BYPASS)`
  - Pin 3 ($2Z$, Select=1) $\to$ `LUT2_OUT`
  - Pin 5 ($1Z$, Select=0) $\to$ `BLE2_Q` (U15 Pin 5)
  - Pin 4 ($Z$, Output) $\to$ `OUT[2]` (Header J2)
- **BLE 3 Bypass (U17 Channel A)**:
  - Pin 11 ($S_A$) $\to$ `U13 Pin 3 (Q_D, BLE3_BYPASS)`
  - Pin 12 ($2X$, Select=1) $\to$ `LUT3_OUT`
  - Pin 13 ($1X$, Select=0) $\to$ `BLE3_Q` (U15 Pin 9)
  - Pin 14 ($X$, Output) $\to$ `OUT[3]` (Header J2)

---

## 4. Hardware Headers & Peripheral Protection

### 4.1 Header Pinouts
- **J1: Logic Inputs (2x8 pin, 2.54mm pitch)**:
  - Pins 1..16: `IN[0]` through `IN[15]`.
  - Each input line is protected by a **100k pull-down resistor** to prevent floating CMOS gates when unconnected.
- **J2: Logic Outputs (1x6 pin, 2.54mm pitch)**:
  - Pin 1: `OUT[0]` (Buffered to green LED 1)
  - Pin 2: `OUT[1]` (Buffered to green LED 2)
  - Pin 3: `OUT[2]` (Buffered to green LED 3)
  - Pin 4: `OUT[3]` (Buffered to green LED 4)
  - Pin 5: `COUT` (Carry-out status)
  - Pin 6: `GND`
- **J3: Control & Clock (1x5 pin, 2.54mm pitch)**:
  - Pin 1: `SYS_CLK` (Clock input from RP2040 or external function generator)
  - Pin 2: `FAB_RST_N` (Active-low reset input)
  - Pin 3: `CIN` (Carry-in input)
  - Pin 4: `+3.3V`
  - Pin 5: `GND`
