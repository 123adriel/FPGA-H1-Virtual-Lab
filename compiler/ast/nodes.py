"""
Abstract Syntax Tree (AST) Nodes - FPGA-H1 Compiler
Typed node classes representing parsed H1L hardware constructs.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any


@dataclass(kw_only=True)
class ASTNode:
    line: int = 0
    column: int = 0


# Expressions
@dataclass(kw_only=True)
class ExpressionNode(ASTNode):
    inferred_width: int = 1


@dataclass(kw_only=True)
class NumberNode(ExpressionNode):
    value: int = 0
    width: Optional[int] = None  # None = unsized literal


@dataclass(kw_only=True)
class SignalRefNode(ExpressionNode):
    name: str = ""
    subfield: Optional[str] = None          # For module instances: inst.pin
    index: Optional[int] = None             # Scalar bit index: sig[2]
    range_high: Optional[int] = None        # Bus slice: sig[7:0]
    range_low: Optional[int] = None


@dataclass(kw_only=True)
class UnaryOpNode(ExpressionNode):
    op: str = ""
    operand: Optional[ExpressionNode] = None


@dataclass(kw_only=True)
class BinaryOpNode(ExpressionNode):
    op: str = ""
    left: Optional[ExpressionNode] = None
    right: Optional[ExpressionNode] = None


@dataclass(kw_only=True)
class TernaryNode(ExpressionNode):
    cond: Optional[ExpressionNode] = None
    true_expr: Optional[ExpressionNode] = None
    false_expr: Optional[ExpressionNode] = None


@dataclass(kw_only=True)
class ConcatNode(ExpressionNode):
    parts: List[ExpressionNode] = field(default_factory=list)


# Declarations & Statements
@dataclass(kw_only=True)
class SignalDeclNode(ASTNode):
    name: str = ""
    width: int = 1
    direction: str = "WIRE"  # "INPUT", "OUTPUT", "INOUT", "WIRE", "CLOCK", "RESET"


@dataclass(kw_only=True)
class RegisterDeclNode(ASTNode):
    name: str = ""
    width: int = 1
    expr: Optional[ExpressionNode] = None
    clock_name: str = "CLK"
    enable_expr: Optional[ExpressionNode] = None
    reset_name: Optional[str] = None


@dataclass(kw_only=True)
class AssignNode(ASTNode):
    target: Optional[SignalRefNode] = None
    expr: Optional[ExpressionNode] = None


@dataclass(kw_only=True)
class LutNode(ASTNode):
    name: str = ""
    inputs: List[ExpressionNode] = field(default_factory=list)
    mask: int = 0x0000


@dataclass(kw_only=True)
class InstanceNode(ASTNode):
    name: str = ""
    module_name: str = ""
    port_map: Dict[str, ExpressionNode] = field(default_factory=dict)


@dataclass(kw_only=True)
class ConnectNode(ASTNode):
    src: Optional[SignalRefNode] = None
    dest: Optional[SignalRefNode] = None


@dataclass(kw_only=True)
class ModuleNode(ASTNode):
    name: str = ""
    items: List[ASTNode] = field(default_factory=list)


@dataclass(kw_only=True)
class DeviceNode(ASTNode):
    name: str = ""
    items: List[ASTNode] = field(default_factory=list)
    modules: Dict[str, ModuleNode] = field(default_factory=dict)
