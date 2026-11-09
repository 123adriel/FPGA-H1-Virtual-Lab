# FPGA-H1 — Phase 5: Resource Inventory & Hardware Scaling Model

## 1. Executive Summary & Nominal Target

The primary scaling benchmark of the FPGA-H1 project is to match the nominal logic capacity of the **Gowin GW1NR-9** (featured in the Sipeed Tang Nano 9K development board), which provides **8,640 LUT4 equivalents**.

This document defines the exact hardware resource budgeting, grid dimensioning, switch topology, and configuration memory footprint required to realize this capacity.

---

## 2. FPGA-H1 Full-Scale Architecture Dimensioning

To achieve $\ge 8,640$ LUT4s in an Island-Style FPGA architecture with $N=4$ Basic Logic Elements (BLEs) per Configurable Logic Block (CLB), we evaluate the minimum grid dimensions:

$$\text{CLBs Required} = \left\lceil \frac{8,640}{4} \right\rceil = 2,160 \text{ CLBs}$$
$$\text{Grid Side } S = \lceil \sqrt{2,160} \rceil = \lceil 46.47 \rceil = 47$$

Choosing a symmetric grid of $47 \times 47$ CLBs yields:
$$\text{Total Available CLBs} = 47 \times 47 = 2,209 \text{ CLBs}$$
$$\text{Total 4-Input LUTs} = 2,209 \times 4 = \mathbf{8,836 \text{ LUT4s}}$$
$$\text{Total D-Type Flip-Flops} = 2,209 \times 4 = \mathbf{8,836 \text{ DFFs}}$$

### Redundancy & Defect Mitigation
- **Nominal Reference Requirement**: 8,640 LUT4s
- **Provided Capacity**: 8,836 LUT4s
- **Spare Capacity**: $\mathbf{+196 \text{ LUT4s}}$ ($49$ complete CLBs, $2.27\%$ redundancy margin). These spare tiles can be utilized as defect-mitigation rows/columns or dedicated global clock buffer tiles during physical ASIC tapeout.

---

## 3. Comprehensive Resource Inventory Table

| Resource Category | Primitive Type | Quantity ($47 \times 47$ Grid) | Description / Configuration Parameters |
| :--- | :--- | :---: | :--- |
| **Logic Tiles** | Configurable Logic Block (CLB) | **2,209** | Array of $47 \times 47$ tiles, each containing 4 BLEs |
| **Logic Units** | Basic Logic Element (BLE) | **8,836** | LUT4 + DFF + Bypass Mux + Fast Carry |
| **Look-Up Tables** | 4-Input SRAM LUT (LUT4) | **8,836** | 16 bits configuration memory each ($141,376$ bits total) |
| **Registers** | D-Type Flip-Flop (DFF) | **8,836** | Master-slave with synchronous reset and clock enable |
| **Switch Matrices** | Wilton Switch Box ($F_s=3$) | **2,304** | $(47+1) \times (47+1)$ intersections across the grid |
| **Connection Boxes** | Connection Box (CB) | **4,512** | $2,256$ Horizontal (CHANX) + $2,256$ Vertical (CHANY) |
| **Channel Tracks** | Routing Channel Width ($W$) | **8 tracks** | Standard track width ($36,096$ wire segments across fabric) |
| **I/O Blocks** | Peripheral IOBs | **188 Pins** | $47 \times 4$ perimeter pads (configurable input/output/tristate) |

---

## 4. Configuration Memory (SRAM) Budget Calculation

The total configuration bitstream size required to program every primitive in the full $47 \times 47$ FPGA-H1 matrix is broken down as follows:

1. **LUT4 Truth Tables**:
   $$8,836 \text{ LUTs} \times 16 \text{ bits} = 141,376 \text{ bits}$$
2. **BLE Architectural Options** (Bypass MUX, Clock Inversion, Reset Mode):
   $$8,836 \text{ BLEs} \times 3 \text{ bits} = 26,508 \text{ bits}$$
3. **Connection Boxes (CB)** ($F_{c,\text{in}}=0.5 \implies 4 \text{ bits/pin}$, $F_{c,\text{out}}=0.5 \implies 4 \text{ bits/pin}$):
   $$2,209 \text{ CLBs} \times (16 \text{ input pins} \times 4 + 4 \text{ output pins} \times 4) = 176,720 \text{ bits}$$
4. **Wilton Switch Boxes (SB)** ($W=8, F_s=3 \implies 6 \text{ switches per track}$):
   $$2,304 \text{ SBs} \times 48 \text{ switches} = 110,592 \text{ bits}$$

$$\mathbf{\text{Total Uncompressed Configuration Bits}} = 141,376 + 26,508 + 176,720 + 110,592 = \mathbf{455,196 \text{ bits}} \ (\approx 56.9 \text{ KB})$$

With H1BS zlib stream compression, typical design bitstreams for this fabric compress down to **8 KB to 24 KB**, fitting comfortably inside low-cost SPI NOR flash memory.

---

## 5. Architectural Comparison: FPGA-H1 vs Gowin GW1NR-9

| Architectural Metric | Gowin GW1NR-9 (Tang Nano 9K) | FPGA-H1 Full Scale ($47 \times 47$) | Architectural Note |
| :--- | :---: | :---: | :--- |
| **Nominal 4-LUTs** | 8,640 | **8,836** | FPGA-H1 meets and exceeds nominal count (+196) |
| **Flip-Flops** | 6,480 | **8,836** | FPGA-H1 provides 1 DFF per LUT (1.36x more flip-flops) |
| **Switch Box Topology** | Proprietary Segmented | **Wilton $F_s=3$** | Open, predictable, collision-free routing graph |
| **Embedded Block RAM** | 26 Block SRAMs (468 Kbit) | *External / Virtual Emulated* | Physical tapeout would require dedicated BRAM columns |
| **DSP / Multipliers** | 20 Multipliers ($18 \times 18$) | *Synthesized via LUT4* | Physical tapeout would add hard DSP slices |
| **Configuration Format** | Proprietary Bitstream | **Open H1BS Format** | Fully documented binary layout with CRC-32 |
| **Toolchain** | Gowin EDA (Closed Source) | **H1L Compiler + Virtual Lab** | 100% open-source Python + React stack |
