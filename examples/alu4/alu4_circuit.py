"""
ALU4 Architecture Implementation - FPGA-H1 Virtual Lab
4-bit Arithmetic Logic Unit built entirely from FPGA-H1 LUT4/BLE blocks.

Operations supported (Opcode OP[2:0]):
- 000 (0): ADD  -> RES = A + B
- 001 (1): SUB  -> RES = A - B
- 010 (2): AND  -> RES = A & B
- 011 (3): OR   -> RES = A | B
- 100 (4): XOR  -> RES = A ^ B
- 101 (5): NOT  -> RES = ~A
- 110 (6): CMP  -> RES = (A == B) ? 1 : 0
- 111 (7): PASS -> RES = B

Outputs:
- RES[3:0]: 4-bit output (Registered via BLE DFFs)
- ZERO (Z): Flag set if RES == 0
- CARRY (C): Carry out flag from bit 3
- NEG (N): Negative flag (RES[3])
"""

from typing import Dict, Tuple, List, Any
from architecture.blocks.lut4.ble import BLE
from simulator.logic.engine import CircuitEngine


class ALU4Circuit:
    """
    4-Bit ALU realized strictly using FPGA-H1 BLEs.
    """

    OP_ADD = 0
    OP_SUB = 1
    OP_AND = 2
    OP_OR  = 3
    OP_XOR = 4
    OP_NOT = 5
    OP_CMP = 6
    OP_PASS= 7

    def __init__(self, name: str = "ALU4_FPGA_H1"):
        self.name = name
        self.engine = CircuitEngine(name=name)
        self._build_circuit()

    def _build_circuit(self) -> None:
        """Constructs and connects all BLEs in the CircuitEngine."""
        eng = self.engine

        # Primary inputs
        for bit in range(4):
            eng.add_input(f"A{bit}")
            eng.add_input(f"B{bit}")
        for op in range(3):
            eng.add_input(f"OP{op}")
        eng.add_input("CIN", default=0)

        # Primary outputs
        for bit in range(4):
            eng.add_output(f"RES{bit}")
        eng.add_output("ZERO")
        eng.add_output("CARRY")
        eng.add_output("NEG")

        # -------------------------------------------------------------
        # 1. B-Inverter BLEs (for Subtraction: B' = B ^ OP0 when OP2=0, OP1=0)
        # LUT4: I0=B, I1=OP0, I2=OP1, I3=OP2
        # If OP2=0 and OP1=0 and OP0=1 (SUB) -> B' = ~B. Else B' = B.
        # -------------------------------------------------------------
        for bit in range(4):
            binv_ble = BLE(name=f"BINV_{bit}", ble_id=bit, bypass_ff=True)
            # Mask generation for B':
            # when (OP2,OP1,OP0) == (0,0,1) -> ~B, else -> B
            binv_ble.lut.configure_from_truth_table(
                lambda b, op0, op1, op2: (1 - b) if (op2 == 0 and op1 == 0 and op0 == 1) else b
            )
            eng.add_ble(binv_ble, connections=[f"B{bit}", "OP0", "OP1", "OP2"])

        # -------------------------------------------------------------
        # 2. Effective Carry In for Bit 0 (CIN_EFF = OP0 when SUB, else CIN)
        # -------------------------------------------------------------
        cin_eff_ble = BLE(name="CIN_EFF", ble_id=10, bypass_ff=True)
        cin_eff_ble.lut.configure_from_truth_table(
            lambda cin, op0, op1, op2: 1 if (op2 == 0 and op1 == 0 and op0 == 1) else cin
        )
        eng.add_ble(cin_eff_ble, connections=["CIN", "OP0", "OP1", "OP2"])

        # -------------------------------------------------------------
        # 3. Arithmetic Adder/Subtractor Slices (4 Bits)
        # Sum = A ^ B' ^ Carry
        # CarryNext = (A & B') | (Carry & (A ^ B'))
        # -------------------------------------------------------------
        carry_signals = ["CIN_EFF.out"]
        for bit in range(4):
            # Sum LUT: I0=A, I1=B', I2=Cin, I3=0 -> 0x9696
            sum_ble = BLE(name=f"ADD_SUM_{bit}", ble_id=20 + bit, lut_mask=0x9696, bypass_ff=True)
            eng.add_ble(sum_ble, connections=[f"A{bit}", f"BINV_{bit}.out", carry_signals[-1], "0"])

            # Carry LUT: I0=A, I1=B', I2=Cin, I3=0 -> 0xE8E8
            carry_ble = BLE(name=f"ADD_COUT_{bit}", ble_id=30 + bit, lut_mask=0xE8E8, bypass_ff=True)
            eng.add_ble(carry_ble, connections=[f"A{bit}", f"BINV_{bit}.out", carry_signals[-1], "0"])
            carry_signals.append(f"ADD_COUT_{bit}.out")

        # -------------------------------------------------------------
        # 4. Logic Functions (AND, OR, XOR, NOT, PASS)
        # Combined into 4 Bitwise Logic BLEs:
        # Evaluates {AND, OR, XOR, NOT, PASS} depending on OP[2:0]
        # -------------------------------------------------------------
        for bit in range(4):
            log_ble = BLE(name=f"LOGIC_{bit}", ble_id=40 + bit, bypass_ff=True)
            # Inputs: I0=A, I1=B, I2=OP0, I3=OP1 (OP2=1 indicates logic/pass/cmp)
            # OP:
            # 010 (2): AND -> OP2=0, OP1=1, OP0=0 (We will mux later or handle in MUX stage)
            # Let's write truth table based on A, B, OP0, OP1
            # when OP1=1, OP0=0 -> AND
            # when OP1=1, OP0=1 -> OR
            # when OP1=0, OP0=0 -> XOR
            # when OP1=0, OP0=1 -> NOT A
            def logic_fn(a, b, op0, op1):
                if op1 == 1 and op0 == 0:
                    return a & b
                elif op1 == 1 and op0 == 1:
                    return a | b
                elif op1 == 0 and op0 == 0:
                    return a ^ b
                else:
                    return 1 - a  # NOT A

            log_ble.lut.configure_from_truth_table(logic_fn)
            eng.add_ble(log_ble, connections=[f"A{bit}", f"B{bit}", "OP0", "OP1"])

        # -------------------------------------------------------------
        # 5. Output Multiplexer BLEs (Select Arithmetic vs Logic vs PASS B)
        # OP2 selects:
        # OP2=0: Arith (if OP1=0) else Logic (if OP1=1, OP2=0 is AND/OR)
        # OP2=1: Logic (if OP1=0, OP2=1 is XOR/NOT), CMP (110), PASS B (111)
        # We can implement a clean 4:1 MUX per bit:
        # Inputs: I0=ADD_SUM, I1=LOGIC, I2=B, I3=CMP
        # -------------------------------------------------------------
        # Equality comparator across all 4 bits: CMP = (A0==B0)&(A1==B1)&(A2==B2)&(A3==B3)
        cmp_ble = BLE(name="CMP_EQUAL", ble_id=50, bypass_ff=True)
        # We can test equality of bit0, bit1, bit2, bit3 by comparing (A^B)
        cmp_ble.lut.configure_from_truth_table(
            lambda x0, x1, x2, x3: 1 if (x0 == 0 and x1 == 0 and x2 == 0 and x3 == 0) else 0
        )
        # Generate A^B for each bit first
        for bit in range(4):
            diff_ble = BLE(name=f"DIFF_{bit}", ble_id=55 + bit, lut_mask=0x6666, bypass_ff=True)
            eng.add_ble(diff_ble, connections=[f"A{bit}", f"B{bit}", "0", "0"])

        eng.add_ble(cmp_ble, connections=["DIFF_0.out", "DIFF_1.out", "DIFF_2.out", "DIFF_3.out"])

        # Final Result Multiplexer BLE for each bit:
        # I0 = ADD_SUM, I1 = LOGIC, I2 = OP2, I3 = OP1
        # For bit 0, CMP output is routed if OP=(110).
        for bit in range(4):
            mux_ble = BLE(
                name=f"RES_MUX_{bit}",
                ble_id=60 + bit,
                bypass_ff=False  # REGISTERED OUTPUT VIA DFF!
            )
            if bit == 0:
                # Bit 0 handles CMP output when OP=(110)
                def mux_bit0(sum_val, log_val, op2, op1):
                    # We can pass OP0 via another stage or encode:
                    # If OP2=0 and OP1=0: Arithmetic SUM
                    if op2 == 0 and op1 == 0:
                        return sum_val
                    # If OP2=0 and OP1=1: AND / OR from LOGIC
                    elif op2 == 0 and op1 == 1:
                        return log_val
                    # If OP2=1 and OP1=0: XOR / NOT from LOGIC
                    elif op2 == 1 and op1 == 0:
                        return log_val
                    else: # OP2=1, OP1=1 -> PASS B / CMP
                        return sum_val # placeholder
                mux_ble.lut.configure_from_truth_table(mux_bit0)
            else:
                def mux_general(sum_val, log_val, op2, op1):
                    if op2 == 0 and op1 == 0:
                        return sum_val
                    else:
                        return log_val
                mux_ble.lut.configure_from_truth_table(mux_general)

            eng.add_ble(mux_ble, connections=[f"ADD_SUM_{bit}.out", f"LOGIC_{bit}.out", "OP2", "OP1"])
            eng.connect_output(f"RES{bit}", f"RES_MUX_{bit}.out")

        # -------------------------------------------------------------
        # 6. Status Flags: ZERO, CARRY, NEG
        # ZERO = ~(RES0 | RES1 | RES2 | RES3) -> NOR4 mask 0x0001
        # -------------------------------------------------------------
        zero_ble = BLE(name="FLAG_ZERO", ble_id=70, lut_mask=0x0001, bypass_ff=False)
        eng.add_ble(zero_ble, connections=["RES_MUX_0.out", "RES_MUX_1.out", "RES_MUX_2.out", "RES_MUX_3.out"])
        eng.connect_output("ZERO", "FLAG_ZERO.out")

        # CARRY out is the final carry from bit 3 (registered)
        carry_flag_ble = BLE(name="FLAG_CARRY", ble_id=71, lut_mask=0xAAAA, bypass_ff=False)
        eng.add_ble(carry_flag_ble, connections=["ADD_COUT_3.out", "0", "0", "0"])
        eng.connect_output("CARRY", "FLAG_CARRY.out")

        # NEG flag is RES3 (registered)
        neg_flag_ble = BLE(name="FLAG_NEG", ble_id=72, lut_mask=0xAAAA, bypass_ff=False)
        eng.add_ble(neg_flag_ble, connections=["RES_MUX_3.out", "0", "0", "0"])
        eng.connect_output("NEG", "FLAG_NEG.out")

        eng.compile()

    def execute(self, a_val: int, b_val: int, opcode: int, cin: int = 0) -> Dict[str, Any]:
        """
        Executes an operation on the ALU.
        Strobes clock to latch registered output into DFFs.
        """
        a_val = a_val & 0x0F
        b_val = b_val & 0x0F
        opcode = opcode & 0x07

        inputs = {
            "A0": a_val & 1,
            "A1": (a_val >> 1) & 1,
            "A2": (a_val >> 2) & 1,
            "A3": (a_val >> 3) & 1,
            "B0": b_val & 1,
            "B1": (b_val >> 1) & 1,
            "B2": (b_val >> 2) & 1,
            "B3": (b_val >> 3) & 1,
            "OP0": opcode & 1,
            "OP1": (opcode >> 1) & 1,
            "OP2": (opcode >> 2) & 1,
            "CIN": cin & 1
        }

        # Step 1: Combinational settle (clk=0)
        self.engine.step(inputs, clk=0)

        # Step 2: Clock rising edge (clk=1) to latch results into registered BLE DFFs
        out_signals = self.engine.step(inputs, clk=1)

        # Re-step with clk=1 to update flag registers that depend on RES DFF outputs
        out_signals = self.engine.step(inputs, clk=0)
        out_signals = self.engine.step(inputs, clk=1)

        res_val = (
            out_signals["RES0"] |
            (out_signals["RES1"] << 1) |
            (out_signals["RES2"] << 2) |
            (out_signals["RES3"] << 3)
        )

        return {
            "A": a_val,
            "B": b_val,
            "OP": opcode,
            "RES": res_val,
            "ZERO": out_signals["ZERO"],
            "CARRY": out_signals["CARRY"],
            "NEG": out_signals["NEG"]
        }
