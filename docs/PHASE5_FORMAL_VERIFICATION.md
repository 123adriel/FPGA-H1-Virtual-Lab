# FPGA-H1 — Phase 5: Formal Logic & Primitive Verification

## 1. Executive Summary

Formal verification provides mathematical guarantees that our hardware primitives (LUT4, DFF, Wilton Switch Box, Connection Box) adhere to discrete digital logic specifications. Unlike heuristic testing, formal verification validates invariant properties across the entire state space of the primitives.

---

## 2. LUT4 Formal Specification & Completeness Proof

The FPGA-H1 4-input Look-Up Table (LUT4) is modeled as a 16-bit static RAM (SRAM) cell array addressed by 4 binary inputs $I_0, I_1, I_2, I_3$.

### 2.1 Mathematical Formulation
For any 4-bit input vector $\vec{I} = (I_0, I_1, I_2, I_3) \in \{0, 1\}^4$, the integer address minterm $m$ is defined as:
$$m(\vec{I}) = \sum_{k=0}^{3} I_k \cdot 2^k \quad \text{where } m \in [0, 15]$$

Let $M \in [0, 65535]$ be the 16-bit configuration mask ($M \in \{0, 1\}^{16}$). The output $Y$ is defined by:
$$Y(M, \vec{I}) = (M \gg m(\vec{I})) \ \& \ 1 = \sum_{m'=0}^{15} \left( \frac{M}{2^{m'}} \pmod 2 \right) \cdot \prod_{k=0}^{3} \left( I_k \cdot m'_k + (1 - I_k)(1 - m'_k) \right)$$

### 2.2 Exhaustive Verification of Primitive Functions
Formal equivalence was verified for all $2^4 = 16$ minterms against canonical logic operators:

| Operator | Canonical Formula | Truth Table Bitmask $M$ | Verification Result |
| :--- | :--- | :---: | :---: |
| **ZERO** | $0$ | `0x0000` | $16/16$ minterms validated ($Y = 0$) |
| **ONE** | $1$ | `0xFFFF` | $16/16$ minterms validated ($Y = 1$) |
| **XOR4** | $I_0 \oplus I_1 \oplus I_2 \oplus I_3$ | `0x6996` | $16/16$ minterms validated (Odd parity) |
| **AND4** | $I_0 \cdot I_1 \cdot I_2 \cdot I_3$ | `0x8000` | $16/16$ minterms validated ($Y = 1 \iff \vec{I}=(1,1,1,1)$) |
| **NOR4** | $\overline{I_0 + I_1 + I_2 + I_3}$ | `0x0001` | $16/16$ minterms validated ($Y = 1 \iff \vec{I}=(0,0,0,0)$) |
| **MUX2to1** | $\overline{S} A + S B$ | `0xACAC` | $16/16$ minterms validated (Multiplexer select) |
| **MAJ3** | $I_0 I_1 + I_0 I_2 + I_1 I_2$ | `0xE8E8` | $16/16$ minterms validated (Full Adder Carry) |

**Theorem 1 (Completeness)**: *A single LUT4 can implement any arbitrary Boolean function $f: \{0, 1\}^4 \to \{0, 1\}$. There exist exactly $2^{2^4} = 2^{16} = 65,536$ unique functions, all addressable by a 16-bit unsigned integer mask.*

---

## 3. D-Type Flip-Flop (DFF) State Transition Verification

The FPGA-H1 DFF incorporates edge-triggered master-slave dynamics with synchronous reset (`SRST`) and clock enable (`CE`).

### 3.1 State Machine Specification
Let $Q_t \in \{0, 1\}$ represent the stored state at discrete step $t$. Let $\text{CLK}_t$ and $\text{CLK}_{t-1}$ be the current and prior clock samples.

$$\text{RisingEdge}_t = (\text{CLK}_t == 1) \land (\text{CLK}_{t-1} == 0)$$

The state update equation is strictly evaluated as:
$$Q_{t+1} = \begin{cases}
0 & \text{if } \text{RisingEdge}_t \land (\text{SRST}_t == 1) \\
D_t & \text{if } \text{RisingEdge}_t \land (\text{SRST}_t == 0) \land (\text{CE}_t == 1) \\
Q_t & \text{otherwise} \quad (\text{Latch state preserved})
\end{cases}$$

### 3.2 Dynamic Invariant Proofs
1. **No Transparent Latching**:
   For all steps where $\text{CLK}_t == 1$ and $\text{CLK}_{t-1} == 1$, varying $D_t \in \{0, 1\}$ resulted in $\Delta Q = 0$. The flip-flop is purely edge-triggered and immune to level-sensitive feedthrough.
2. **Falling Edge Invariance**:
   For all transitions where $\text{CLK}_{t-1} = 1 \to \text{CLK}_t = 0$, $Q_{t+1} = Q_t$ across all values of $D_t$.
3. **Synchronous Reset Dominance**:
   When $\text{RisingEdge}_t = 1$ and $\text{SRST}_t = 1$, $Q_{t+1} = 0$ independently of whether $D_t = 1$ or $\text{CE}_t = 0$.

---

## 4. Interconnect Formal Invariants

### 4.1 Wilton Switch Box ($F_s = 3$) Permutation Invariant
The Wilton switch matrix provides symmetric flexibility $F_s = 3$ by interconnecting 4 planar sides: North ($N$), East ($E$), South ($S$), West ($W$) for track index $t \in [0, W-1]$.

The Wilton diagonal diagonal-shift equations are implemented as:
$$\begin{aligned}
T_{\text{left}}(t) &= t \\
T_{\text{right}}(t) &= (t + 1) \pmod W \\
T_{\text{opp}}(t) &= (t + W - 1) \pmod W
\end{aligned}$$

Every internal node in the Wilton block maintains degree exactly $F_s = 3$. Our formal suite verified that:
1. No self-loops exist: $(Side_A, t) \not\leftrightarrow (Side_A, t)$.
2. Connections are bidirectional: $\text{Connected}(A, t_1 \to B, t_2) \iff \text{Connected}(B, t_2 \to A, t_1)$.
3. Channel tracks are isolated when unconfigured (0 leakage / 0 phantom connections).

### 4.2 Connection Box Short-Circuit Prevention
In physical CMOS FPGA fabrics, two drivers simultaneously asserting conflicting logical levels ($0$ and $1$) onto the same metal routing track create a destructive low-impedance path ($V_{DD} \to V_{SS}$).

**Invariant (Single-Driver Exclusion)**:
$$\forall \text{track } t \in [0, W-1], \quad \sum_{p=0}^{\text{pins}-1} \mathbb{I}_{[\text{Driver}(p) = t]} \le 1$$

Our test suite validated that if Pin $A$ is driving Track $t$, any attempt by Pin $B$ to drive Track $t$ throws a `RuntimeError: Short-circuit conflict`, blocking corrupt bitstreams or malicious routing configurations before hardware simulation.
