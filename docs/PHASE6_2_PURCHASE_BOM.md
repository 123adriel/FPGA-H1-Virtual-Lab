# FPGA-H1 — Phase 6.2: Definitive Pre-Purchase Bill of Materials (BOM)

## 1. Executive Summary & Hardware Accounting Updates

Following the Phase 6.2 pre-purchase design freeze, two integrated circuits were added to provide **dedicated, uncompromised Clock Enable (`CE`) and Synchronous Reset (`SRST`)** without reducing the 4-input LUT4 logic capacity:
1. **`U21`**: **SN74HC157DR** (Quad 2:1 Multiplexer for Clock Enable data recirculation).
2. **`U22`**: **SN74HC08DR** (Quad 2-Input AND Gate for Synchronous Reset gating).

### Total Board Component Counts:
- **Active Integrated Circuits**: **22 ICs** (21 digital logic ICs + 1 LDO voltage regulator).
- **Passive Components**: 21 ceramic decoupling capacitors, 2 tantalum bulk capacitors, 23 resistors, 4 LEDs.
- **Connectors**: 3 pin headers (J1, J2, J3) + 2 female socket strips for the Pico (J4, J5).

---

## 2. Definitive Pre-Purchase BOM (`FPGA-H1-PROTOTYPE-001`)

| Item | Ref Des | Description / Function | Manufacturer Part # | Pkg | Qty | Verified Supplier | Unit (USD) | Total (USD) | Total (ARS @ MEP $1,150) |
| :---: | :--- | :--- | :--- | :---: | :---: | :--- | :---: | :---: | :---: |
| **1** | U1 .. U4 | 16-Channel Analog/Digital MUX (LUT4) | **CD74HC4067SM96** (TI) | SSOP-24 | 4 | Mouser / LCSC | $0.68 | $2.72 | $3,128 |
| **2** | U5 .. U13 | 8-Bit Shift Register (72-Bit Config) | **SN74HC595DR** (TI) | SOIC-16 | 9 | Electrocomp / LCSC | $0.22 | $1.98 | $2,277 |
| **3** | U14, U15 | Dual Positive-Edge D-Type Flip-Flop | **SN74HC74DR** (TI) | SOIC-14 | 2 | Electrocomp / LCSC | $0.18 | $0.36 | $414 |
| **4** | U16..U18 | Triple 2-Channel MUX (Bypass & Carry)| **CD74HC4053M96** (TI) | SOIC-16 | 3 | Mouser / LCSC | $0.32 | $0.96 | $1,104 |
| **5** | U19 | Configuration Bridge Microcontroller | **Raspberry Pi Pico (RP2040)** | Module | 1 | MercadoLibre / Pi | $6.50 | $6.50 | $7,475 |
| **6** | U20 | 3.3V 600mA Low-Dropout Regulator | **AP2112K-3.3TRG1** (Diodes) | SOT-23-5| 1 | Mouser / LCSC | $0.35 | $0.35 | $403 |
| **7** | **U21** | Quad 2:1 Multiplexer (Clock Enable) | **SN74HC157DR** (TI) | SOIC-16 | 1 | Electrocomp / LCSC | $0.22 | $0.22 | $253 |
| **8** | **U22** | Quad 2-Input AND Gate (Sync Reset) | **SN74HC08DR** (TI) | SOIC-14 | 1 | Electrocomp / LCSC | $0.18 | $0.18 | $207 |
| **9** | C1 .. C21 | Ceramic Decoupling Caps 0.1 uF 50V X7R| Yageo CC0805KRX7R9BB104 | 0805 SMD | 21 | LCSC / Local | $0.02 | $0.42 | $483 |
| **10**| C22, C23 | Tantalum Bulk Capacitors 10 uF 16V | Kemet T491A106K016AT | 1206 SMD | 2 | LCSC / Local | $0.18 | $0.36 | $414 |
| **11**| R1 .. R4 | LED Current Limiting Resistors 1k 5% | Standard 0805 1k | 0805 SMD | 4 | Local Stock | $0.01 | $0.04 | $46 |
| **12**| R5 .. R20| Input Pull-down Resistors 100k 5% | Standard 0805 100k | 0805 SMD | 16 | Local Stock | $0.01 | $0.16 | $184 |
| **13**| R21..R23| Control Pull-up Resistors 10k 5% | Standard 0805 10k | 0805 SMD | 3 | Local Stock | $0.01 | $0.03 | $35 |
| **14**| LED1..LED4| Output Indicator Green LEDs | Everlight SMD 0805 Green | 0805 SMD | 4 | Local Stock | $0.05 | $0.20 | $230 |
| **15**| J1 | 16-Bit Logic Input Header (2x8 pin) | 2.54mm Dual Row Male Header | THT | 1 | Local Stock | $0.30 | $0.30 | $345 |
| **16**| J2 | 4-Bit Logic Output Header (1x6 pin) | 2.54mm Single Row Male Header | THT | 1 | Local Stock | $0.15 | $0.15 | $173 |
| **17**| J3 | Control & Clock Header (1x5 pin) | 2.54mm Single Row Male Header | THT | 1 | Local Stock | $0.15 | $0.15 | $173 |
| **18**| J4, J5 | Female Socket Headers for Pico (1x20)| 2.54mm Female Socket Strip | THT | 2 | Local Stock | $0.40 | $0.80 | $920 |
| **19**| PCB | 2-Layer FR4 Prototype Board (100x80) | JLCPCB / Custom Fab (5 pcs) | FR4 2-Layer | 1 | JLCPCB | $2.50 | $2.50 | $2,875 |
| **TOTAL** | — | **Complete Assembled Prototype Board** | — | — | **75** | — | — | **$19.42 USD** | **$22,333 ARS** |

*(Procurement via Argentine local retail at Electrocomponentes / GM Electrónica adds ~\$3.50 USD in local distributor markup, yielding **\$22.90 USD / \$26,300 ARS**).*

---

## 3. Two-Tier Procurement Strategy

To maximize cost efficiency and eliminate risk:

### Tier 1: Single-LUT Breadboard Evaluation Kit (~$9.50 USD / $10,900 ARS)
Procure only the components required for the Phase 6.2 laboratory test plan:
- 1 $\times$ CD74HC4067 (DIP-24 or breakout): \$0.85
- 2 $\times$ SN74HC595 (DIP-16): \$0.50
- 1 $\times$ Raspberry Pi Pico: \$6.50
- Passives & breadboard jumpers: \$1.65
- **Purpose**: Verify SPI loading and measure physical propagation delays on an oscilloscope before committing to full board assembly.

### Tier 2: Complete 1-CLB Hardware Fabrication (~$19.42 USD / $22,300 ARS)
Procure the full 75-component BOM and submit Gerber files for 5 PCBs to JLCPCB.
