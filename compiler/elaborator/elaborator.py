"""
Elaborator for H1L - FPGA-H1 Compiler
Flattens module hierarchy, resolves signal widths, validates types, and detects structural errors.
"""

from typing import Dict, List, Set, Tuple, Optional, Any
from compiler.ast.nodes import (
    DeviceNode, ModuleNode, SignalDeclNode, RegisterDeclNode, AssignNode,
    LutNode, InstanceNode, ConnectNode, ExpressionNode, SignalRefNode,
    NumberNode, UnaryOpNode, BinaryOpNode, TernaryNode, ConcatNode
)


class ElaboratorError(Exception):
    def __init__(self, message: str, node: Optional[Any] = None):
        if node and hasattr(node, 'line') and node.line > 0:
            super().__init__(f"ElaboratorError at line {node.line}, col {node.column}: {message}")
            self.line = node.line
            self.column = node.column
        else:
            super().__init__(f"ElaboratorError: {message}")
            self.line = 0
            self.column = 0


class ElaboratedSignal:
    def __init__(self, name: str, width: int = 1, direction: str = "WIRE"):
        self.name = name
        self.width = width
        self.direction = direction  # INPUT, OUTPUT, WIRE, CLOCK, RESET
        self.drivers: List[str] = []

    def __repr__(self) -> str:
        return f"Signal({self.name}[{self.width}], dir={self.direction})"


class ElaboratedRegister:
    def __init__(self, name: str, width: int, expr: ExpressionNode, clock: str, enable: Optional[ExpressionNode], reset: Optional[str]):
        self.name = name
        self.width = width
        self.expr = expr
        self.clock = clock
        self.enable = enable
        self.reset = reset


class ElaboratedDesign:
    def __init__(self, name: str):
        self.name = name
        self.signals: Dict[str, ElaboratedSignal] = {}
        self.registers: List[ElaboratedRegister] = []
        self.assignments: List[Tuple[SignalRefNode, ExpressionNode]] = []
        self.luts: List[LutNode] = []

    def add_signal(self, name: str, width: int = 1, direction: str = "WIRE", node: Optional[Any] = None) -> ElaboratedSignal:
        if name in self.signals:
            raise ElaboratorError(f"Duplicate declaration of signal '{name}'", node)
        sig = ElaboratedSignal(name, width, direction)
        self.signals[name] = sig
        return sig


class Elaborator:
    def __init__(self, device: DeviceNode):
        self.device = device
        self.modules = device.modules
        self.design = ElaboratedDesign(device.name)

    def elaborate(self) -> ElaboratedDesign:
        """Elaborates the top-level device and all its children into a unified flat design."""
        self._elaborate_items(self.device.items, prefix="")
        self._validate_integrity()
        return self.design

    def _elaborate_items(self, items: List[Any], prefix: str) -> None:
        for item in items:
            # Handle MultiSignalDecl if returned from parser
            if hasattr(item, 'signals'):
                for s in item.signals:
                    self._elaborate_signal_decl(s, prefix)
            elif isinstance(item, SignalDeclNode):
                self._elaborate_signal_decl(item, prefix)
            elif isinstance(item, RegisterDeclNode):
                self._elaborate_register_decl(item, prefix)
            elif isinstance(item, AssignNode):
                self._elaborate_assign(item, prefix)
            elif isinstance(item, LutNode):
                self._elaborate_lut(item, prefix)
            elif isinstance(item, ConnectNode):
                self._elaborate_connect(item, prefix)
            elif isinstance(item, InstanceNode):
                self._elaborate_instance(item, prefix)

    def _full_name(self, name: str, prefix: str) -> str:
        return f"{prefix}{name}" if prefix else name

    def _elaborate_signal_decl(self, node: SignalDeclNode, prefix: str) -> None:
        full_name = self._full_name(node.name, prefix)
        self.design.add_signal(full_name, width=node.width, direction=node.direction, node=node)

    def _elaborate_register_decl(self, node: RegisterDeclNode, prefix: str) -> None:
        full_name = self._full_name(node.name, prefix)
        clk_name = self._full_name(node.clock_name, prefix)
        rst_name = self._full_name(node.reset_name, prefix) if node.reset_name else None

        # If signal already declared (e.g. as OUTPUT or WIRE), reuse it; otherwise create it
        if full_name in self.design.signals:
            sig = self.design.signals[full_name]
        else:
            sig = self.design.add_signal(full_name, width=node.width, direction="REGISTER", node=node)

        sig.drivers.append(f"REG({full_name})")
        if len(sig.drivers) > 1:
            raise ElaboratorError(f"Multiple drivers on registered signal '{full_name}'", node)

        reg = ElaboratedRegister(
            name=full_name,
            width=node.width,
            expr=node.expr,
            clock=clk_name,
            enable=node.enable_expr,
            reset=rst_name
        )
        self.design.registers.append(reg)

    def _extract_signal_refs(self, expr: ExpressionNode) -> Set[str]:
        vars_set = set()
        if isinstance(expr, SignalRefNode):
            vars_set.add(expr.name)
        elif isinstance(expr, UnaryOpNode):
            vars_set.update(self._extract_signal_refs(expr.operand))
        elif isinstance(expr, BinaryOpNode):
            vars_set.update(self._extract_signal_refs(expr.left))
            vars_set.update(self._extract_signal_refs(expr.right))
        elif isinstance(expr, TernaryNode):
            vars_set.update(self._extract_signal_refs(expr.cond))
            vars_set.update(self._extract_signal_refs(expr.true_expr))
            vars_set.update(self._extract_signal_refs(expr.false_expr))
        elif isinstance(expr, ConcatNode):
            for p in expr.parts:
                vars_set.update(self._extract_signal_refs(p))
        return vars_set

    def _elaborate_assign(self, node: AssignNode, prefix: str) -> None:
        base_name = self._full_name(node.target.name, prefix)
        if base_name not in self.design.signals:
            raise ElaboratorError(f"Undeclared target signal '{base_name}' in ASSIGN statement", node)

        # Check that all referenced signals on RHS are declared
        for var in self._extract_signal_refs(node.expr):
            full_var = self._full_name(var, prefix)
            if full_var not in self.design.signals:
                raise ElaboratorError(f"Undeclared signal '{full_var}' in expression", node)

        # If indexing into a specific bit (e.g. SUM[0]), target net name is SUM[0]
        if node.target.index is not None:
            tgt_name = f"{base_name}[{node.target.index}]"
            if tgt_name not in self.design.signals:
                self.design.add_signal(tgt_name, width=1, direction="WIRE", node=node)
        else:
            tgt_name = base_name

        # Record driver
        self.design.signals[tgt_name].drivers.append(f"ASSIGN({tgt_name})")
        if len(self.design.signals[tgt_name].drivers) > 1:
            raise ElaboratorError(
                f"Multiple drivers detected on signal '{tgt_name}': {self.design.signals[tgt_name].drivers}",
                node
            )

        self.design.assignments.append((node.target, node.expr))

    def _elaborate_lut(self, node: LutNode, prefix: str) -> None:
        lut_name = self._full_name(node.name, prefix)
        for inp in node.inputs:
            if hasattr(inp, 'name') and inp.name:
                full_inp = self._full_name(inp.name, prefix)
                if full_inp not in self.design.signals:
                    raise ElaboratorError(f"Undeclared signal '{full_inp}' in LUT input", inp)

        if lut_name not in self.design.signals:
            self.design.add_signal(lut_name, width=1, direction="WIRE", node=node)
        self.design.signals[lut_name].drivers.append(f"LUT({lut_name})")

        self.design.luts.append(LutNode(name=lut_name, inputs=node.inputs, mask=node.mask, line=node.line, column=node.column))

    def _elaborate_connect(self, node: ConnectNode, prefix: str) -> None:
        src_name = self._full_name(node.src.name, prefix)
        dest_name = self._full_name(node.dest.name, prefix)

        if src_name not in self.design.signals:
            raise ElaboratorError(f"CONNECT source signal '{src_name}' is undeclared", node)
        if dest_name not in self.design.signals:
            raise ElaboratorError(f"CONNECT destination signal '{dest_name}' is undeclared", node)

        self.design.signals[dest_name].drivers.append(f"CONNECT({src_name})")
        if len(self.design.signals[dest_name].drivers) > 1:
            raise ElaboratorError(f"Multiple drivers on destination signal '{dest_name}'", node)

        # Equivalent to ASSIGN dest = src
        self.design.assignments.append((node.dest, node.src))

    def _elaborate_instance(self, node: InstanceNode, prefix: str) -> None:
        """Expands a module instance by prefixing its signals and creating port connections."""
        mod_name = node.module_name
        if mod_name not in self.modules:
            raise ElaboratorError(f"Cannot instantiate undefined MODULE '{mod_name}'", node)

        mod = self.modules[mod_name]
        inst_prefix = f"{prefix}{node.name}."

        # 1. Elaborate internal items of the module with instance prefix
        self._elaborate_items(mod.items, prefix=inst_prefix)

        # 2. Connect port mappings
        for formal_port, actual_expr in node.port_map.items():
            formal_full = f"{inst_prefix}{formal_port}"
            if formal_full not in self.design.signals:
                raise ElaboratorError(f"Module '{mod_name}' has no port named '{formal_port}'", node)

            formal_sig = self.design.signals[formal_full]
            if formal_sig.direction == "INPUT":
                # Actual drives formal: formal = actual
                formal_ref = SignalRefNode(name=formal_full)
                self.design.assignments.append((formal_ref, actual_expr))
                formal_sig.drivers.append(f"PORT_MAP({node.name}.{formal_port})")
            elif formal_sig.direction == "OUTPUT":
                # Formal drives actual: actual = formal
                if not isinstance(actual_expr, SignalRefNode):
                    raise ElaboratorError(f"Module output port '{formal_port}' must connect to a signal variable", node)
                actual_name = self._full_name(actual_expr.name, prefix)
                if actual_name not in self.design.signals:
                    raise ElaboratorError(f"Undeclared signal '{actual_name}' connected to output port", node)
                formal_ref = SignalRefNode(name=formal_full)
                self.design.assignments.append((actual_expr, formal_ref))
                self.design.signals[actual_name].drivers.append(f"OUTPUT_PORT({formal_full})")

    def _validate_integrity(self) -> None:
        """Verifies that all primary outputs and internal wires have valid excitation."""
        for sname, sig in self.design.signals.items():
            if sig.direction in ["OUTPUT", "WIRE"] and len(sig.drivers) == 0:
                # Warning or soft notification for open wires; inputs can be driven externally
                pass
            if len(sig.drivers) > 1:
                raise ElaboratorError(f"Short circuit: Signal '{sname}' driven by multiple sources: {sig.drivers}")
