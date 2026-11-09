# FPGA-H1 — Phase 6.1: Corrected & Verified Bill of Materials (BOM)

## 1. Executive Summary & Corrections from Phase 6

During the Phase 6 preliminary feasibility study, the bill of materials estimated 17 active ICs using 74HC157 quad multiplexers. The Phase 6.1 electrical audit uncovered that the 74HC157 shares a single select pin across all 4 channels, preventing independent BLE bypass selection.

### Engineering Correction
- Replaced two 74HC157 multiplexers with **three CD74HC4053 triple 2:1 multiplexers** (with 100% independent select lines).
- Added an on-board **AP2112K-3.3V 600mA LDO regulator** to power the entire board cleanly from USB 5V.
- The verified IC count is **20 ICs total** (19 digital ICs + 1 LDO regulator).

---

## 2. Definitive Bill of Materials (`FPGA-H1-PROTOTYPE-001`)

| Item # | Ref Designator | Component Name / Description | Manufacturer & Part Number | Package | Qty | Verified Supplier | Verified Unit (USD) | Total Cost (USD) | Compatible Alternatives |
| :---: | :--- | :--- | :--- | :---: | :---: | :--- | :---: | :---: | :--- |
| **1** | U1 .. U4 | 16-Channel Analog/Digital MUX (LUT4) | **Texas Instruments CD74HC4067SM96** | SSOP-24 | 4 | Mouser / LCSC | $0.68 | $2.72 | NXP 74HC4067DB, Toshiba TC74HC4067 |
| **2** | U5 .. U13 | 8-Bit Shift Register with Latches | **Texas Instruments SN74HC595DR** | SOIC-16 | 9 | Electrocomp / LCSC | $0.22 | $1.98 | Nexperia 74HC595D, OnSemi MC74HC595 |
| **3** | U14, U15 | Dual Positive-Edge D-Type Flip-Flop | **Texas Instruments SN74HC74DR** | SOIC-14 | 2 | Electrocomp / LCSC | $0.18 | $0.36 | Nexperia 74HC74D, Toshiba TC74HC74 |
| **4** | U16..U18 | Triple 2-Channel Analog Multiplexer | **Texas Instruments CD74HC4053M96** | SOIC-16 | 3 | Mouser / LCSC | $0.32 | $0.96 | Nexperia 74HC4053D, OnSemi MC74HC4053 |
| **5** | U19 | Configuration Bridge Microcontroller | **Raspberry Pi Pico (RP2040)** | Module | 1 | MercadoLibre / Pi | $6.50 | $6.50 | Waveshare RP2040-Zero, Seeed Xiao |
| **6** | U20 | Low-Dropout 3.3V 600mA Voltage Reg | **Diodes Inc. AP2112K-3.3TRG1** | SOT-23-5| 1 | LCSC / Mouser | $0.35 | $0.35 | TI TPS73633, Microchip MIC5219 |
| **7** | C1 .. C19| Ceramic Decoupling Capacitors 0.1 uF | Yageo CC0805KRX7R9BB104 | 0805 SMD | 19 | LCSC / Local | $0.02 | $0.38 | Any 0805 X7R 50V 100nF |
| **8** | C20, C21| Tantalum Bulk Capacitors 10 uF 16V | Kemet T491A106K016AT | 1206 SMD | 2 | LCSC / Local | $0.18 | $0.36 | Murata 10uF 16V X5R Ceramic |
| **9** | R1 .. R4 | LED Current Limiting Resistors 1k 5% | 0805 SMD Resistor 1k | 0805 SMD | 4 | Local Stock | $0.01 | $0.04 | Standard 0805 1k |
| **10**| R5 .. R20| Input Pull-down Resistors 100k 5% | 0805 SMD Resistor 100k | 0805 SMD | 16 | Local Stock | $0.01 | $0.16 | Standard 0805 100k |
| **11**| R21..R23| Control Pull-up Resistors 10k 5% | 0805 SMD Resistor 10k | 0805 SMD | 3 | Local Stock | $0.01 | $0.03 | Standard 0805 10k |
| **12**| LED1..LED4| Surface Mount LEDs (Output Status) | Everlight 19-217/GHC-YR1S2/3T | 0805 Green | 4 | Local Stock | $0.05 | $0.20 | Any 0805 Green LED |
| **13**| J1 | 16-Bit Logic Input Header (2x8 pin) | 2.54mm Dual Row Male Header | THT | 1 | Local Stock | $0.30 | $0.30 | Standard 2.54mm pitch |
| **14**| J2 | 4-Bit Logic Output Header (1x6 pin) | 2.54mm Single Row Male Header | THT | 1 | Local Stock | $0.15 | $0.15 | Standard 2.54mm pitch |
| **15**| J3 | Control Header (1x5 pin 2.54mm) | 2.54mm Single Row Male Header | THT | 1 | Local Stock | $0.15 | $0.15 | Standard 2.54mm pitch |
| **16**| J4, J5 | Female Header Sockets for Pico (1x20)| 2.54mm Female Socket Header | THT | 2 | Local Stock | $0.40 | $0.80 | Standard 20-pin socket |
| **17**| PCB | 2-Layer FR4 Prototype Board (100x80) | JLCPCB / Custom Fabrication | FR4 2-Layer | 1 | JLCPCB (5 pcs) | $2.50 | $2.50 | PCBWay, OSHPark |
| **TOTAL** | — | **Complete Assembled Prototype** | — | — | **71** | — | **$18.94 USD** | **$21,780 ARS** |

*(Converted at Argentine MEP Rate: \$1,150 ARS/USD. Local procurement in Buenos Aires at Electrocomponentes / GM Electrónica adds ~\$3.50 USD in local retail markup, yielding an estimated total of **\$22.50 USD / \$25,800 ARS**).*
