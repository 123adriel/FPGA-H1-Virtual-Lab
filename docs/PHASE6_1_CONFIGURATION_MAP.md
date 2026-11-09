# FPGA-H1 — Phase 6.1: Configuration Memory Architecture & 72-Bit Physical Mapping

## 1. 74HC595 Scan Chain Architecture

In `FPGA-H1-PROTOTYPE-001`, the configuration memory is formed by a daisy-chained cascade of **nine 74HC595 8-bit shift registers** ($9 \times 8 = \mathbf{72 \text{ bits}}$).

```mermaid
flowchart LR
    SPI_MOSI["RP2040 MOSI"] --> U13["IC 9: Control<br/>(Bypass & Carry)"]
    U13 -->|Q7S| U12["IC 8: LUT3 High"]
    U12 -->|Q7S| U11["IC 7: LUT3 Low"]
    U11 -->|Q7S| U10["IC 6: LUT2 High"]
    U10 -->|Q7S| U9["IC 5: LUT2 Low"]
    U9 -->|Q7S| U8["IC 4: LUT1 High"]
    U8 -->|Q7S| U7["IC 3: LUT1 Low"]
    U7 -->|Q7S| U6["IC 2: LUT0 High"]
    U6 -->|Q7S| U5["IC 1: LUT0 Low"]
    U5 -->|Q7S| SPI_MISO["RP2040 MISO<br/>(Readback / Verify)"]
```

---

## 2. Reconciling 68 Bits vs 72 Physical Register Bits

In Phase 6, the preliminary allocation considered 68 configuration bits (64 LUT bits + 4 bypass bits), leaving 4 outputs of the 9th register unused.

### Final Allocation: 100% Hardware Utilization
By dedicating the remaining 4 bits to **Independent Carry Multiplexer Selection (`CARRY_EN_0..3`)**, the full 72-bit physical capacity of the nine 74HC595 ICs is utilized with **zero wasted outputs**:

$$\mathbf{72 \text{ Bits Total}} = \underbrace{64 \text{ Bits}}_{\text{4 LUT4 Truth Tables}} + \underbrace{4 \text{ Bits}}_{\text{BLE Bypass Multiplexers}} + \underbrace{4 \text{ Bits}}_{\text{BLE Carry Multiplexers}}$$

---

## 3. Complete Physical Bit Mapping Table

The table below defines the exact hardware assignment of every bit in the 9-byte configuration packet:

| Byte Index | Shift Register IC | Bit Index | Register Output Pin | Hardware Net Destination | Functional Description |
| :---: | :---: | :---: | :---: | :--- | :--- |
| **Byte 0** | **U5 (IC 1)** | Bit 0 | $Q_A$ (Pin 15) | `LUT0_CFG[0]` | LUT0 Minterm 0 (`0000`) |
| | | Bits 1..7 | $Q_B .. Q_H$ | `LUT0_CFG[1..7]` | LUT0 Minterms 1..7 |
| **Byte 1** | **U6 (IC 2)** | Bits 8..15 | $Q_A .. Q_H$ | `LUT0_CFG[8..15]` | LUT0 Minterms 8..15 |
| **Byte 2** | **U7 (IC 3)** | Bits 16..23 | $Q_A .. Q_H$ | `LUT1_CFG[0..7]` | LUT1 Minterms 0..7 |
| **Byte 3** | **U8 (IC 4)** | Bits 24..31 | $Q_A .. Q_H$ | `LUT1_CFG[8..15]` | LUT1 Minterms 8..15 |
| **Byte 4** | **U9 (IC 5)** | Bits 32..39 | $Q_A .. Q_H$ | `LUT2_CFG[0..7]` | LUT2 Minterms 0..7 |
| **Byte 5** | **U10 (IC 6)** | Bits 40..47 | $Q_A .. Q_H$ | `LUT2_CFG[8..15]` | LUT2 Minterms 8..15 |
| **Byte 6** | **U11 (IC 7)** | Bits 48..55 | $Q_A .. Q_H$ | `LUT3_CFG[0..7]` | LUT3 Minterms 0..7 |
| **Byte 7** | **U12 (IC 8)** | Bits 56..63 | $Q_A .. Q_H$ | `LUT3_CFG[8..15]` | LUT3 Minterms 8..15 |
| **Byte 8** | **U13 (IC 9)** | Bit 64 | $Q_A$ (Pin 15) | `BLE0_BYPASS` | 1 = Combinational LUT, 0 = DFF Registered |
| | | Bit 65 | $Q_B$ (Pin 1) | `BLE1_BYPASS` | 1 = Combinational LUT, 0 = DFF Registered |
| | | Bit 66 | $Q_C$ (Pin 2) | `BLE2_BYPASS` | 1 = Combinational LUT, 0 = DFF Registered |
| | | Bit 67 | $Q_D$ (Pin 3) | `BLE3_BYPASS` | 1 = Combinational LUT, 0 = DFF Registered |
| | | Bit 68 | $Q_E$ (Pin 4) | `BLE0_CARRY_EN`| 1 = Arithmetic Carry Propagate/Generate, 0 = Normal Logic |
| | | Bit 69 | $Q_F$ (Pin 5) | `BLE1_CARRY_EN`| 1 = Arithmetic Carry Propagate/Generate, 0 = Normal Logic |
| | | Bit 70 | $Q_G$ (Pin 6) | `BLE2_CARRY_EN`| 1 = Arithmetic Carry Propagate/Generate, 0 = Normal Logic |
| | | Bit 71 | $Q_H$ (Pin 7) | `BLE3_CARRY_EN`| 1 = Arithmetic Carry Propagate/Generate, 0 = Normal Logic |

---

## 4. Transmission Protocol & Shifting Sequence

1. **Shift Order**:
   - The stream enters serial-in at **U13 (IC 9)** and cascades down to **U5 (IC 1)**.
   - Therefore, the **first bit transmitted over `MOSI` is Bit 0 (`LUT0_CFG[0]`)**, which traverses all 72 flip-flops until settling into $Q_A$ of U5.
   - The **last bit transmitted is Bit 71 (`BLE3_CARRY_EN`)**, which remains in $Q_H$ of U13.
2. **Glitch-Free Latching (`CFG_LATCH`)**:
   - While shifting 72 clock cycles on `CFG_SCK`, storage register clock `RCLK` remains LOW. The parallel outputs $Q_A..Q_H$ maintain their prior state.
   - Once all 72 bits are loaded and verified, the RP2040 asserts a positive pulse on `CFG_LATCH` ($t_w \ge 20\text{ ns}$).
   - All 72 configuration signals update **simultaneously in $< 15\text{ ns}$**.
3. **SPI Interruption & CRC-32 Protection**:
   - If transmission is aborted prematurely (e.g. fewer than 72 bits received, or CRC-32 fails), `CFG_LATCH` is never pulsed.
   - The shift registers are cleared via `/SRCLR` and the fabric continues running its prior valid configuration without undefined states.
4. **Configuration Readback (`MISO`)**:
   - Serial output pin $Q7S$ (Pin 9) of U5 connects back to the RP2040 `MISO` pin.
   - By clocking an additional 72 dummy bits, the RP2040 can read back the exact bitstream currently in the shift chain to verify configuration integrity before pulsing `CFG_LATCH`.
