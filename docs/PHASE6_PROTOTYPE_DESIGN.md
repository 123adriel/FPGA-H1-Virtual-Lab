# FPGA-H1 — Phase 6: Minimum Physical Prototype Design (`FPGA-H1-PROTOTYPE-001`)

## 1. Prototype Overview & Mission

The **`FPGA-H1-PROTOTYPE-001`** is the initial physical implementation of the FPGA-H1 architecture. It serves as the physical proof-of-concept demonstrating:
1. True programmable hardware logic (not hardwired gates).
2. Direct programming from binary **H1BS bitstreams** compiled by the H1L toolchain.
3. Decoupled execution between the configuration bridge and the logic fabric.
4. Correct synchronous sequential behavior (DFF edge triggering, synchronous reset, and clock enable).

```mermaid
flowchart TD
    subgraph HostPC ["Host PC / Workstation"]
        H1L["H1L Compiler / Virtual Lab IDE"]
    end

    subgraph Bridge ["Configuration & Supervisory Bridge (RP2040)"]
        USB["USB CDC Serial"] --> MCU_CORE["ARM Cortex-M0+"]
        MCU_CORE --> SPI_MASTER["Hardware SPI / PIO Master"]
    end

    subgraph ProtoBoard ["FPGA-H1-PROTOTYPE-001 (1 CLB Physical Board)"]
        SPI_SLAVE["CFG SPI Bus (MOSI, SCK, LATCH)"]
        SHIFT_CHAIN["9 x 74HC595 (68-bit Scan Chain)"]
        LUT_ARRAY["4 x 74HC4067 (4 x LUT4 16:1 Mux)"]
        DFF_ARRAY["2 x 74HC74 (4 x DFF Registers)"]
        MUX_ARRAY["2 x 74HC157 (Bypass & Carry Muxes)"]
        IO_HEADERS["Physical I/O Headers (16 In, 4 Out, CLK, RST)"]
        
        SPI_SLAVE --> SHIFT_CHAIN
        SHIFT_CHAIN -->|LUT Masks (64b)| LUT_ARRAY
        SHIFT_CHAIN -->|Bypass Bits (4b)| MUX_ARRAY
        IO_HEADERS <--> LUT_ARRAY & DFF_ARRAY & MUX_ARRAY
    end

    H1L -->|H1BS Bitstream (USB)| USB
    SPI_MASTER -->|SPI Shift Clock & Data| SPI_SLAVE
```

---

## 2. Complete Bill of Materials (BOM) for 1 Prototype Board

| Item # | Reference Designator | Component Name / Description | Manufacturer Part Number | Package | Qty | Unit Cost (USD) | Total Cost (USD) |
| :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| 1 | U1, U2, U3, U4 | 16-Channel Analog/Digital MUX (LUT4) | **CD74HC4067SM96** (TI) | SOIC-24 | 4 | $0.85 | $3.40 |
| 2 | U5 .. U13 | 8-Bit Serial-In Parallel-Out Shift Reg | **SN74HC595DR** (TI) | SOIC-16 | 9 | $0.28 | $2.52 |
| 3 | U14, U15 | Dual D-Type Positive-Edge Flip-Flop | **SN74HC74DR** (TI) | SOIC-14 | 2 | $0.22 | $0.44 |
| 4 | U16, U17 | Quad 2:1 Data Selector / Mux (Bypass) | **SN74HC157DR** (TI) | SOIC-16 | 2 | $0.25 | $0.50 |
| 5 | U18 | Companion Config Bridge Microcontroller | **Raspberry Pi Pico (RP2040)** | Module | 1 | $4.00 | $4.00 |
| 6 | C1 .. C18 | Ceramic Decoupling Capacitors 0.1 uF | 0805 SMD X7R 50V | 0805 | 18 | $0.02 | $0.36 |
| 7 | C19, C20 | Bulk Tantalum Capacitors 10 uF 16V | 1206 SMD | 1206 | 2 | $0.15 | $0.30 |
| 8 | J1 | Main Logic Input Header (2x8 pin 2.54mm) | Male Pin Header | Through-hole | 1 | $0.35 | $0.35 |
| 9 | J2 | Main Logic Output Header (1x4 pin 2.54mm)| Male Pin Header | Through-hole | 1 | $0.15 | $0.15 |
| 10| J3 | Clock / Control Header (1x4 pin 2.54mm) | Male Pin Header | Through-hole | 1 | $0.15 | $0.15 |
| 11| LED1..LED4| Surface Mount LEDs (Output Monitor) | 0805 Green LED | 0805 | 4 | $0.05 | $0.20 |
| 12| R1 .. R4 | LED Current Limiting Resistors 1k 5% | 0805 SMD | 0805 | 4 | $0.01 | $0.04 |
| 13| PCB | 2-Layer FR4 Prototype PCB (100x80mm) | Custom Fabrication | 2-Layer | 1 | $4.00 | $4.00 |
| **TOTAL** | — | **Complete Assembled Prototype Board** | — | — | **49** | — | **$16.41** |

*(Note: In batches of 5 boards, the unit cost drops to under **$12.50 USD**).*

---

## 3. Demonstration & Hardware Bring-Up Circuits

The 1 CLB prototype provides 4 LUT4s and 4 DFFs, capable of executing all standard digital circuit primitives:

### Circuit 1: Combinational Logic Gates (AND, OR, XOR, NOT)
- **H1L Implementation**:
  ```h1l
  DEVICE GATES4
  INPUT A, B
  OUTPUT Y_AND, Y_OR, Y_XOR, Y_NOT
  ASSIGN Y_AND = A & B
  ASSIGN Y_OR  = A | B
  ASSIGN Y_XOR = A ^ B
  ASSIGN Y_NOT = ~A
  END
  ```
- **Hardware Mapping**:
  - BLE0: Mask `0x8888` (AND) $\to$ $O_0$.
  - BLE1: Mask `0xEEEE` (OR) $\to$ $O_1$.
  - BLE2: Mask `0x6996` (XOR) $\to$ $O_2$.
  - BLE3: Mask `0x5555` (NOT) $\to$ $O_3$.
  - Bypass bits: All 4 BLEs set to `bypass_ff = True` (Combinational direct).

### Circuit 2: 4-Bit Synchronous Up-Counter
- **H1L Implementation**:
  ```h1l
  DEVICE COUNTER4
  INPUT CLK, RST, CE
  OUTPUT Q[4]
  REGISTER CNT[4] CLOCK CLK RESET RST ENABLE CE
  ASSIGN CNT = CNT + 1
  ASSIGN Q = CNT
  END
  ```
- **Hardware Mapping**:
  - BLE0: $Q_0$ toggles on every active clock edge ($T_0 = 1$).
  - BLE1: $Q_1$ toggles when $Q_0 = 1$ ($T_1 = Q_0$).
  - BLE2: $Q_2$ toggles when $Q_0 \land Q_1 = 1$.
  - BLE3: $Q_3$ toggles when $Q_0 \land Q_1 \land Q_2 = 1$.
  - Bypass bits: All 4 BLEs set to `bypass_ff = False` (Registered DFF mode).
  - Validates: Rising-edge clocking, state retention, synchronous clear, and clock enable.

### Circuit 3: 4-Bit Full Adder
- **H1L Implementation**:
  ```h1l
  DEVICE ADDER4
  INPUT A[4], B[4], CIN
  OUTPUT S[4], COUT
  ASSIGN {COUT, S} = A + B + CIN
  END
  ```
- **Hardware Mapping**:
  - Uses the 4 BLEs in arithmetic mode with the dedicated hardware carry chain (`CIN` $\to$ BLE0 $\to$ BLE1 $\to$ BLE2 $\to$ BLE3 $\to$ `COUT`).
  - Evaluates all 512 input combinations in real-time.

---

## 4. Expansion Plan: 4-CLB Modular Array (`FPGA-H1-PROTOTYPE-004`)

Following validation of `PROTOTYPE-001`, the design scales to a 4-CLB ($2 \times 2$ grid) carrier board:
- **Capacity**: 16 LUT4s, 16 DFFs, 4 Wilton Switch Boxes, 16 Connection Boxes.
- **Form Factor**: 4-layer FR4 PCB ($120 \times 120\text{ mm}$).
- **Interconnect**: Four 74CBT3257 high-speed bus switch ICs per switch box.
- **Capabilities**: Capable of hosting complete 4-bit ALUs (`ALU4`), 8-state sequence detectors, or 3-stage register pipelines (`pipeline3`).
