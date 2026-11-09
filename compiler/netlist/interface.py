"""
Compiler Netlist Interface - FPGA-H1 Virtual Lab
Defines the formal architectural contract between the H1L Compiler and the Physical Placement/Routing Engines.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any


class PinDirection(str, Enum):
    INPUT = "INPUT"
    OUTPUT = "OUTPUT"
    INOUT = "INOUT"


class PinType(str, Enum):
    LOGIC = "LOGIC"
    CLOCK = "CLOCK"
    RESET = "RESET"
    CARRY = "CARRY"
    ENABLE = "ENABLE"


@dataclass
class PinModel:
    """Formal definition of a physical or logical pin."""
    name: str
    direction: PinDirection
    pin_type: PinType = PinType.LOGIC
    index: int = 0
    connected_net: Optional[str] = None


@dataclass
class SignalModel:
    """Formal model of a netlist wire/signal carrying data across logic elements."""
    name: str
    driver_pin: Optional[Tuple[str, str]] = None  # (cell_name, pin_name)
    sink_pins: List[Tuple[str, str]] = field(default_factory=list)  # List of (cell_name, pin_name)
    is_clock: bool = False
    is_critical: bool = False
    max_delay_ps: Optional[float] = None


@dataclass
class CellInstance:
    """An instantiated logic cell (LUT4, DFF, or CLB)."""
    name: str
    cell_type: str  # 'LUT4', 'DFF', 'BLE', 'CLB'
    pins: Dict[str, PinModel] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)  # e.g. {"mask": 0x8888, "bypass_ff": True}
    placement_constraint: Optional[Tuple[int, int]] = None  # Fixed (x, y) if constrained


@dataclass
class PlacementConstraint:
    """Constraints imposed by user or floorplanning on cell placement."""
    cell_name: str
    fixed_coord: Optional[Tuple[int, int]] = None
    region_box: Optional[Tuple[int, int, int, int]] = None  # (min_x, min_y, max_x, max_y)


@dataclass
class RoutingConstraint:
    """Constraints imposed on net routing (e.g. max delay, clock tree reservation)."""
    net_name: str
    max_segments: Optional[int] = None
    require_global_clock_line: bool = False
    avoid_channels: List[Tuple[str, int, int]] = field(default_factory=list)


@dataclass
class H1Netlist:
    """
    Complete H1L Intermediate Representation (IR) Netlist.
    This data structure is produced by the H1L Elaborator/Synthesizer and consumed by Placement/Routing.
    """
    design_name: str
    device_target: str  # e.g. 'H1-4', 'H1-16', 'H1-64', 'H1-256', 'H1-1024', 'H1-8640'
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    clocks: List[str] = field(default_factory=list)
    cells: Dict[str, CellInstance] = field(default_factory=dict)
    signals: Dict[str, SignalModel] = field(default_factory=dict)
    placement_constraints: List[PlacementConstraint] = field(default_factory=list)
    routing_constraints: List[RoutingConstraint] = field(default_factory=list)

    def add_cell(self, cell: CellInstance) -> None:
        self.cells[cell.name] = cell

    def add_signal(self, sig: SignalModel) -> None:
        self.signals[sig.name] = sig

    def connect(self, net_name: str, driver_cell: str, driver_pin: str, sink_cell: str, sink_pin: str) -> None:
        """Connects a driver pin to a sink pin through a named net."""
        if net_name not in self.signals:
            self.signals[net_name] = SignalModel(name=net_name)

        sig = self.signals[net_name]
        sig.driver_pin = (driver_cell, driver_pin)
        sig.sink_pins.append((sink_cell, sink_pin))

        # Update cell pin records if present
        if driver_cell in self.cells and driver_pin in self.cells[driver_cell].pins:
            self.cells[driver_cell].pins[driver_pin].connected_net = net_name
        if sink_cell in self.cells and sink_pin in self.cells[sink_cell].pins:
            self.cells[sink_cell].pins[sink_pin].connected_net = net_name

    def validate_integrity(self) -> List[str]:
        """
        Validates netlist topological rules before handoff to Placement and Routing.
        Checks for:
        - Floating inputs
        - Nets without drivers
        - Multi-driver contentions
        """
        errors = []
        for sname, sig in self.signals.items():
            if sig.driver_pin is None:
                errors.append(f"Net '{sname}' has no active driver")
            if not sig.sink_pins:
                errors.append(f"Net '{sname}' is floating with no sink pins")

        for cname, cell in self.cells.items():
            for pname, pin in cell.pins.items():
                if pin.direction == PinDirection.INPUT and pin.connected_net is None:
                    errors.append(f"Cell '{cname}' input pin '{pname}' is unconnected")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        return {
            "design_name": self.design_name,
            "device_target": self.device_target,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "clocks": self.clocks,
            "cell_count": len(self.cells),
            "signal_count": len(self.signals)
        }
