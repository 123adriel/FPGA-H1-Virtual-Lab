# FPGA-H1 — Phase 6.2: Physical Single-LUT4 Laboratory Bring-Up & Test Plan

## 1. Objective & Philosophy of Experimental Staging

Before purchasing components for the full 22-IC board or submitting Gerber files for PCB manufacturing, the fundamental building block—**a single physical 4-input Look-Up Table (LUT4)**—must be assembled on a benchtop breadboard or breakout PCB and experimentally characterized.

> [!IMPORTANT]
> **Physical Proof Mandate**: No software simulation or datasheet interpolation replaces empirical oscilloscope measurements on physical silicon. This test plan defines the exact laboratory procedure to measure real propagation delay, signal rise/fall times, and truth table fidelity on hardware.

---

## 2. Experimental Setup & Breadboard Schematic

### Required Benchtop Equipment:
- 1 $\times$ Raspberry Pi Pico (RP2040) connected to workstation via USB.
- 1 $\times$ **CD74HC4067** (16-channel analog/digital MUX, DIP-24 or SSOP-24 on breakout).
- 2 $\times$ **SN74HC595** (8-bit shift registers with latches, DIP-16 or SOIC-16 on breakout).
- 3 $\times$ **$0.1 \ \mu\text{F}$ ceramic decoupling capacitors** (placed across $V_{CC}$ and GND of each IC).
- 1 $\times$ 2-channel Digital Storage Oscilloscope (DSO, $\ge 50\text{ MHz}$ bandwidth, 10X passive probes).
- Solderless breadboard and jumper wires.

```mermaid
flowchart LR
    PICO["Raspberry Pi Pico (3.3V)"]
    U_LOW["74HC595 #1 (Low Byte 0..7)"]
    U_HIGH["74HC595 #2 (High Byte 8..15)"]
    MUX["74HC4067 (16:1 LUT4)"]
    SCOPE["Oscilloscope Ch1 & Ch2"]

    PICO -->|GPIO 16: MOSI| U_HIGH
    U_HIGH -->|Pin 9: Q7S| U_LOW
    PICO -->|GPIO 18: SCK| U_LOW & U_HIGH
    PICO -->|GPIO 19: LATCH| U_LOW & U_HIGH
    
    U_LOW -->|Q_A..Q_H (Bits 0..7)| MUX
    U_HIGH -->|Q_A..Q_H (Bits 8..15)| MUX
    
    PICO -->|GPIO 2..5: Inputs I0..I3| MUX
    MUX -->|Pin 1: Output Z| SCOPE
    PICO -->|GPIO 2: Input I0 Sync| SCOPE
```

---

## 3. Physical Breadboard Wiring Netlist

### 3.1 Power Rails:
- Pico `Pin 36 (3V3_OUT)` $\to$ Breadboard Red Rail (`+3.3V`).
- Pico `Pin 38 (GND)` $\to$ Breadboard Blue Rail (`GND`).
- Place one $0.1 \ \mu\text{F}$ capacitor directly between Pin 24 ($V_{CC}$) and Pin 12 (GND) of 74HC4067.
- Place one $0.1 \ \mu\text{F}$ capacitor directly between Pin 16 ($V_{CC}$) and Pin 8 (GND) of both 74HC595s.

### 3.2 74HC595 Shift Cascade:
- Pico `GPIO 16 (MOSI)` $\to$ U_HIGH Pin 14 (`SER`).
- U_HIGH Pin 9 (`QH'`) $\to$ U_LOW Pin 14 (`SER`).
- Pico `GPIO 18 (SCK)` $\to$ U_LOW Pin 11 & U_HIGH Pin 11 (`SRCLK`).
- Pico `GPIO 19 (LATCH)` $\to$ U_LOW Pin 12 & U_HIGH Pin 12 (`RCLK`).
- Pin 10 (`/SRCLR`) on both 595s $\to$ Tied to `+3.3V`.
- Pin 13 (`/OE`) on both 595s $\to$ Tied to `GND`.

### 3.3 74HC4067 LUT Core:
- U_LOW Pins 15, 1..7 ($Q_A..Q_H$) $\to$ 74HC4067 Pins 9..2 ($Y_0..Y_7$).
- U_HIGH Pins 15, 1..7 ($Q_A..Q_H$) $\to$ 74HC4067 Pins 23..16 ($Y_8..Y_{15}$).
- 74HC4067 Pin 15 (`/E`) $\to$ Tied to `GND`.
- Pico `GPIO 2, 3, 4, 5` $\to$ 74HC4067 Pins 10, 11, 14, 9 ($S_0, S_1, S_2, S_3$).
- 74HC4067 Pin 1 ($Z$, LUT Output) $\to$ Oscilloscope Channel 2 probe.

---

## 4. Laboratory Execution Protocol (Step-by-Step)

### Step 1: Power Rail & Quiescent Current Check
1. Power Pico via USB.
2. Measure voltage at Pin 24 of 74HC4067: must read **$3.30\text{V} \pm 0.05\text{V}$**.
3. Measure static current draw of the 3 ICs: must be **$< 50 \ \mu\text{A}$**.

### Step 2: Test Pattern Battery (Truth Table Verification)
Execute the MicroPython automated verification script on the Pico, applying the canonical test masks:

| Test # | Function Name | 16-Bit Mask | Expected Physical Output Across All 16 Minterms | Pass Criteria |
| :---: | :--- | :---: | :--- | :--- |
| **T1** | All-Zero Quiescent | `0x0000` | $Y = 0\text{V}$ for all 16 addresses | Digital 0 on all minterms |
| **T2** | All-One VCC Rail | `0xFFFF` | $Y = 3.3\text{V}$ for all 16 addresses | Digital 1 on all minterms |
| **T3** | Single Minterm Walk | `0x0001` .. `0x8000` | Exactly 1 active minterm outputs 3.3V; 15 minterms output 0V | Decoupling of all 16 address paths |
| **T4** | 4-Input XOR (Parity)| `0x6996` | $Y = 3.3\text{V}$ if odd number of inputs are HIGH, else $0\text{V}$ | 100% vector match on all 16 states |
| **T5** | 4-Input AND | `0x8000` | $Y = 3.3\text{V} \iff (I_3, I_2, I_1, I_0) = (1, 1, 1, 1)$ | Single minterm 15 assertion |
| **T6** | 4-Input OR | `0xFFFE` | $Y = 0\text{V} \iff (I_3, I_2, I_1, I_0) = (0, 0, 0, 0)$ | 15 minterms high |
| **T7** | 2-to-1 Multiplexer | `0x00CA` | $S_0=0 \implies Y = D_0$; $S_0=1 \implies Y = D_1$ | Clean multiplexer steering |

### Step 3: Oscilloscope Timing & Propagation Measurements
1. Connect **Scope Channel 1** (10X probe) to `GPIO 2` ($S_0$, address LSB).
2. Connect **Scope Channel 2** (10X probe) to `Pin 1` ($Z$, LUT output).
3. Set Pico to toggle $S_0$ continuously at $100\text{ kHz}$ with mask `0x5555` ($Y = \overline{S_0}$).
4. Set Scope trigger to Channel 1 rising edge (threshold at 1.65V).
5. **Measure**:
   - $t_{\text{pd,LH}}$: Time from 50% point of $S_0$ rising edge to 50% point of $Z$ rising edge.
   - $t_{\text{pd,HL}}$: Time from 50% point of $S_0$ falling edge to 50% point of $Z$ falling edge.
   - Rise Time ($t_r$): Time from 10% to 90% of $Z$ waveform.
   - Fall Time ($t_f$): Time from 90% to 10% of $Z$ waveform.
6. **Pass Criteria**:
   - Propagation delay $t_{\text{pd}} \le 45\text{ ns}$ (typical expected: $\approx 22\text{ ns}$).
   - Waveform clean with $< 200\text{ mV}$ ringing and zero monotonic reversals.
