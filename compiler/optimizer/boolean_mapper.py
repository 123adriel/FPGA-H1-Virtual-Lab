"""
Boolean Optimizer & Technology Mapper - FPGA-H1 Compiler
Synthesizes AST expressions into canonical LUT4 truth tables and sequential BLEs.
Implements Shannon decomposition for expressions with > 4 inputs.
"""

from typing import Dict, List, Set, Tuple, Optional, Any, Callable
from compiler.ast.nodes import (
    ExpressionNode, SignalRefNode, NumberNode, UnaryOpNode,
    BinaryOpNode, TernaryNode, ConcatNode
)


class MappedLUT:
    def __init__(self, name: str, inputs: List[str], mask: int, output_wire: str):
        self.name = name
        self.inputs = inputs  # Up to 4 input signal names
        self.mask = mask      # 16-bit integer configuration
        self.output_wire = output_wire

    def __repr__(self) -> str:
        return f"MappedLUT({self.name}, in={self.inputs}, mask=0x{self.mask:04X} -> {self.output_wire})"


class MappedDFF:
    def __init__(self, name: str, d_wire: str, q_wire: str, clock: str, enable: Optional[str] = None, reset: Optional[str] = None):
        self.name = name
        self.d_wire = d_wire
        self.q_wire = q_wire
        self.clock = clock
        self.enable = enable
        self.reset = reset

    def __repr__(self) -> str:
        return f"MappedDFF({self.name}, D={self.d_wire} -> Q={self.q_wire}, CLK={self.clock})"


class BooleanMapper:
    """
    Technology mapper: transforms elaborated expressions into networks of LUT4s and DFFs.
    """

    def __init__(self):
        self.lut_counter = 0
        self.dff_counter = 0
        self.wire_counter = 0
        self.mapped_luts: List[MappedLUT] = []
        self.mapped_dffs: List[MappedDFF] = []

    def _alloc_wire(self, prefix: str = "w") -> str:
        w = f"{prefix}_{self.wire_counter}"
        self.wire_counter += 1
        return w

    def _alloc_lut_name(self, prefix: str = "LUT") -> str:
        name = f"{prefix}_{self.lut_counter}"
        self.lut_counter += 1
        return name

    def _alloc_dff_name(self, prefix: str = "DFF") -> str:
        name = f"{prefix}_{self.dff_counter}"
        self.dff_counter += 1
        return name

    def extract_variables(self, expr: ExpressionNode) -> Set[str]:
        """Collects all unique variable names referenced in the expression."""
        vars_set = set()
        if isinstance(expr, SignalRefNode):
            sig_name = expr.name
            if expr.subfield:
                sig_name = f"{expr.name}.{expr.subfield}"
            if expr.index is not None:
                sig_name = f"{sig_name}[{expr.index}]"
            vars_set.add(sig_name)
        elif isinstance(expr, UnaryOpNode):
            vars_set.update(self.extract_variables(expr.operand))
        elif isinstance(expr, BinaryOpNode):
            vars_set.update(self.extract_variables(expr.left))
            vars_set.update(self.extract_variables(expr.right))
        elif isinstance(expr, TernaryNode):
            vars_set.update(self.extract_variables(expr.cond))
            vars_set.update(self.extract_variables(expr.true_expr))
            vars_set.update(self.extract_variables(expr.false_expr))
        return vars_set

    def eval_expr_boolean(self, expr: ExpressionNode, env: Dict[str, int]) -> int:
        """Evaluates an AST expression given a binary environment."""
        if isinstance(expr, NumberNode):
            return expr.value & 1

        elif isinstance(expr, SignalRefNode):
            sig_name = expr.name
            if expr.subfield:
                sig_name = f"{expr.name}.{expr.subfield}"
            if expr.index is not None:
                sig_name = f"{sig_name}[{expr.index}]"
            return env.get(sig_name, 0) & 1

        elif isinstance(expr, UnaryOpNode):
            val = self.eval_expr_boolean(expr.operand, env)
            if expr.op in ["~", "!"]:
                return 1 - val
            elif expr.op == "-":
                return (-val) & 1
            return val

        elif isinstance(expr, BinaryOpNode):
            l = self.eval_expr_boolean(expr.left, env)
            r = self.eval_expr_boolean(expr.right, env)
            op = expr.op
            if op == "&":
                return l & r
            elif op == "|":
                return l | r
            elif op == "^":
                return l ^ r
            elif op == "==":
                return 1 if l == r else 0
            elif op == "!=":
                return 1 if l != r else 0
            elif op == "<":
                return 1 if l < r else 0
            elif op == "<=":
                return 1 if l <= r else 0
            elif op == ">":
                return 1 if l > r else 0
            elif op == ">=":
                return 1 if l >= r else 0
            elif op == "+":
                return (l + r) & 1
            elif op == "-":
                return (l - r) & 1
            elif op == "*":
                return (l * r) & 1
            raise ValueError(f"Unknown binary operator '{op}'")

        elif isinstance(expr, TernaryNode):
            c = self.eval_expr_boolean(expr.cond, env)
            return self.eval_expr_boolean(expr.true_expr, env) if c else self.eval_expr_boolean(expr.false_expr, env)

        return 0

    def map_scalar_expression(self, expr: ExpressionNode, output_wire: Optional[str] = None) -> str:
        """
        Maps a 1-bit boolean expression to one or more LUT4s.
        If inputs <= 4, produces exactly 1 LUT4.
        If inputs > 4, applies Shannon expansion.
        """
        out_wire = output_wire or self._alloc_wire("lut_out")
        vars_list = sorted(list(self.extract_variables(expr)))

        if len(vars_list) == 0:
            # Constant expression
            val = self.eval_expr_boolean(expr, {})
            mask = 0xFFFF if val else 0x0000
            lut = MappedLUT(self._alloc_lut_name("CONST"), ["0", "0", "0", "0"], mask, out_wire)
            self.mapped_luts.append(lut)
            return out_wire

        elif len(vars_list) <= 4:
            # Fits in a single LUT4
            padded_inputs = list(vars_list)
            while len(padded_inputs) < 4:
                padded_inputs.append("0")  # Tie unused inputs to 0

            # Compute truth table mask (16 bits)
            mask = 0
            for idx in range(16):
                env = {}
                for bit_idx, vname in enumerate(vars_list):
                    env[vname] = (idx >> bit_idx) & 1
                out_bit = self.eval_expr_boolean(expr, env) & 1
                mask |= (out_bit << idx)

            lut = MappedLUT(self._alloc_lut_name("LOGIC"), padded_inputs, mask, out_wire)
            self.mapped_luts.append(lut)
            return out_wire

        else:
            # Shannon Decomposition on first variable
            split_var = vars_list[0]
            # Create subexpressions with split_var=0 and split_var=1
            # Realized via MUX 2:1 between F0 and F1
            # F(x) = (split_var) ? F1 : F0
            # Synthesize subexpressions recursively
            f0_wire = self.map_scalar_expression(self._substitute_const(expr, split_var, 0))
            f1_wire = self.map_scalar_expression(self._substitute_const(expr, split_var, 1))

            # MUX2:1 LUT4: I0=F0, I1=F1, I2=SEL(split_var), I3=0 -> mask 0xCACA
            mux_lut = MappedLUT(
                self._alloc_lut_name("SHANNON_MUX"),
                [f0_wire, f1_wire, split_var, "0"],
                0xCACA,
                out_wire
            )
            self.mapped_luts.append(mux_lut)
            return out_wire

    def _substitute_const(self, expr: ExpressionNode, var_name: str, val: int) -> ExpressionNode:
        """Helper to substitute variable with a constant in AST for Shannon decomposition."""
        if isinstance(expr, SignalRefNode):
            sig_name = expr.name
            if expr.subfield:
                sig_name = f"{expr.name}.{expr.subfield}"
            if expr.index is not None:
                sig_name = f"{sig_name}[{expr.index}]"
            if sig_name == var_name:
                return NumberNode(value=val, line=expr.line, column=expr.column)
            return expr
        elif isinstance(expr, UnaryOpNode):
            return UnaryOpNode(op=expr.op, operand=self._substitute_const(expr.operand, var_name, val), line=expr.line, column=expr.column)
        elif isinstance(expr, BinaryOpNode):
            return BinaryOpNode(
                op=expr.op,
                left=self._substitute_const(expr.left, var_name, val),
                right=self._substitute_const(expr.right, var_name, val),
                line=expr.line, column=expr.column
            )
        elif isinstance(expr, TernaryNode):
            return TernaryNode(
                cond=self._substitute_const(expr.cond, var_name, val),
                true_expr=self._substitute_const(expr.true_expr, var_name, val),
                false_expr=self._substitute_const(expr.false_expr, var_name, val),
                line=expr.line, column=expr.column
            )
        return expr
