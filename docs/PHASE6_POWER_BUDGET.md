# FPGA-H1 — Phase 6: Power & Thermal Budget Analysis

## 1. Electrical Power Model

Power consumption in CMOS programmable logic devices consists of two distinct components:

$$P_{\text{total}} = P_{\text{static}} + P_{\text{dynamic}}$$

### 1.1 Static Power Dissipation
Static power is consumed whenever power is applied, regardless of clock switching:
$$P_{\text{static}} = V_{CC} \times \sum I_{\text{quiescent}}$$
Dominated by subthreshold drain leakage, gate tunneling leakage, and quiescent supply currents ($I_{CC}$) in off-the-shelf ICs.

### 1.2 Dynamic Power Dissipation
Dynamic power is consumed during logic transitions charging and discharging node capacitances:
$$P_{\text{dynamic}} = \sum_{i} \alpha_i \cdot C_{L, i} \cdot V_{CC}^2 \cdot f$$
Where:
- $\alpha_i$: Node switching activity factor ($0 \le \alpha \le 1$; typical average $\alpha \approx 0.125$).
- $C_{L, i}$: Total lumped load capacitance of the node (input gates + interconnect parasitics).
- $V_{CC}$: Core operating voltage.
- $f$: Clock switching frequency.

---

## 2. Datasheet-Based Component Power Breakdown

Parameters extracted from manufacturer datasheets (Texas Instruments 74HC series and SkyWater 130nm standard cells):

| Component / Subsystem | Part Number / Technology | Quiescent Current ($I_{CC}$) | Power Dissipation Capacitance ($C_{PD}$) | Typical Static Power @ 5.0V |
| :--- | :--- | :---: | :---: | :---: |
| **16:1 Multiplexer (LUT4)** | 74HC4067 | $8.0 \ \mu\text{A}$ max | $45\text{ pF}$ | $40 \ \mu\text{W}$ |
| **8-Bit Shift Register (Cfg)**| 74HC595 | $8.0 \ \mu\text{A}$ max | $30\text{ pF}$ | $40 \ \mu\text{W}$ |
| **Dual DFF (Registers)** | 74HC74 | $4.0 \ \mu\text{A}$ max | $24\text{ pF}$ | $20 \ \mu\text{W}$ |
| **Quad 2:1 Mux (Bypass/Carry)**| 74HC157 | $8.0 \ \mu\text{A}$ max | $32\text{ pF}$ | $40 \ \mu\text{W}$ |
| **Bus Switch (Routing Hop)** | 74CBT3257 | $3.0 \ \mu\text{A}$ max | $10\text{ pF}$ | $15 \ \mu\text{W}$ |
| **Config Controller Bridge** | RP2040 (Dual Core) | $18.0\text{ mA}$ typ | Embedded | $60\text{ mW}$ |
| **Silicon Standard Cell CLB** | SkyWater 130nm ($1.8\text{V}$) | $2.5\text{ nA}$ per cell | $4.2\text{ fF}$ per node | $4.5 \text{ nW}$ per CLB |

---

## 3. Power Budget by Scale

### 3.1 Single-CLB Prototype (`FPGA-H1-PROTOTYPE-001`, 4 LUT4, 4 DFF @ 10 MHz, 5.0V)
- **Active IC Count**: 17 Discrete ICs (4 $\times$ 74HC4067, 9 $\times$ 74HC595, 2 $\times$ 74HC74, 2 $\times$ 74HC157).
- **Static Quiescent Consumption**:
  $$I_{\text{static}} = 17 \text{ ICs} \times 8 \ \mu\text{A} \approx 136 \ \mu\text{A} \implies P_{\text{static}} = 5.0\text{V} \times 136 \ \mu\text{A} = \mathbf{0.68 \text{ mW}}$$
- **Dynamic Logic Consumption (@ 10 MHz, $\alpha=0.15$)**:
  $$C_{\text{eff}} = (4 \times 45\text{pF}) + (2 \times 24\text{pF}) + (2 \times 32\text{pF}) = 292\text{ pF}$$
  $$P_{\text{dyn, logic}} = 0.15 \times (292 \times 10^{-12}) \times (5.0)^2 \times (10 \times 10^6) = \mathbf{10.95 \text{ mW}}$$
- **Configuration Controller (RP2040 in standby / supervisory mode)**: $\mathbf{65.0 \text{ mW}}$
- **I/O LEDs and Pin Drivers**: $\mathbf{25.0 \text{ mW}}$
$$\mathbf{P_{\text{total, 1-CLB Prototype}}} = 0.68\text{ mW} + 10.95\text{ mW} + 65.0\text{ mW} + 25.0\text{ mW} \approx \mathbf{97.63 \text{ mW}} \ (\approx 0.1 \text{ W})$$
*Power supply: Powered directly from standard USB 5V (draws ~20 mA, well within 500 mA USB limit).*

### 3.2 Quad-CLB Prototype (`FPGA-H1-PROTOTYPE-004`, 16 LUT4, 16 DFF @ 10 MHz)
- **Active IC Count**: 68 Logic ICs + 16 Switch Box ICs = 84 ICs.
- **Static Consumption**: $84 \times 8 \ \mu\text{A} \times 5.0\text{V} = 3.36\text{ mW}$.
- **Dynamic Consumption**: $43.8\text{ mW}$.
- **Controller & I/O**: $95.0\text{ mW}$.
$$\mathbf{P_{\text{total, 4-CLB Prototype}}} \approx \mathbf{142.2 \text{ mW}} \ (\approx 0.14 \text{ W})$$

### 3.3 Scalability Limit: 16-CLB Discrete Array (64 LUT4s)
- **Active IC Count**: 336 ICs.
- **Estimated Power**: $\approx \mathbf{650 \text{ mW}}$.
- *Note*: While power is manageable (<1W), the board complexity (over 4,000 solder joints) makes 16 CLBs the practical upper limit for discrete logic.

### 3.4 Full-Scale Custom Silicon ASIC ($47 \times 47$ Grid, 8,836 LUTs @ 150 MHz, 1.8V)
- **Static Leakage ($2,209$ CLBs + $2,304$ SBs)**: $\approx \mathbf{12.5 \text{ mW}}$.
- **Dynamic Switching Power**:
  - $8,836$ active BLEs with average node capacitance $C_L = 15\text{ fF}$, switching factor $\alpha = 0.125$:
  $$P_{\text{dyn, core}} = 8836 \times 0.125 \times (15 \times 10^{-15}) \times (1.8)^2 \times (150 \times 10^6) = \mathbf{8.05 \text{ mW}}$$
  - **Clock Distribution Network**: $\mathbf{18.2 \text{ mW}}$
  - **I/O Ring (188 Pads @ 3.3V, 25 MHz, 15 pF load)**: $\approx \mathbf{115.0 \text{ mW}}$
$$\mathbf{P_{\text{total, Custom Silicon Fabric}}} \approx 12.5 + 8.05 + 18.2 + 115.0 \approx \mathbf{153.75 \text{ mW}} \ (\approx 0.15 \text{ W})$$
*Comparison*: The Gowin GW1NR-9 operates at ~120 mW to 250 mW under similar logic loads. The FPGA-H1 silicon architecture exhibits competitive power efficiency.

---

## 4. Thermal Analysis & Cooling Requirements

### Thermal Dissipation Formula
$$\Delta T = T_J - T_A = P_{\text{diss}} \times \theta_{JA}$$
Where:
- $T_J$: Junction temperature (Max rating: $125^\circ\text{C}$).
- $T_A$: Ambient room temperature ($25^\circ\text{C}$).
- $\theta_{JA}$: Junction-to-ambient thermal resistance ($^\circ\text{C/W}$).

| Device Prototype | Package Type | Total Dissipation | Package $\theta_{JA}$ | Estimated $\Delta T$ | Cooling Solution |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **`FPGA-H1-PROTOTYPE-001`** | Discrete SOIC/TSSOP | $0.10 \text{ W}$ total | $85^\circ\text{C/W}$ per IC | $+0.5^\circ\text{C}$ (Negligible) | Natural air convection (No heatsink) |
| **`FPGA-H1-PROTOTYPE-004`** | Discrete 4-Layer PCB | $0.14 \text{ W}$ total | $75^\circ\text{C/W}$ per IC | $+0.8^\circ\text{C}$ | Natural air convection (No heatsink) |
| **Custom Silicon ASIC** | QFN-88 ($10 \times 10\text{ mm}$)| $0.15 \text{ W}$ | $32^\circ\text{C/W}$ | $+4.8^\circ\text{C}$ ($T_J \approx 30^\circ\text{C}$) | Exposed ground thermal pad on PCB |

**Conclusion**: Neither the discrete prototypes nor the custom silicon ASIC require active cooling or forced air; thermal dissipation is well within passive convection limits.
