"""
FPGA-H1 Device Profiles - Hardware Specifications and Constraints
==================================================================
Defines device target profiles for the FPGA-H1 toolchain, differentiating:
1. Virtual Full-Scale Matrix: FPGA-H1-GW1NR9 (8,836 LUT4s, 47x47 grid, W=8)
2. Physical First Prototype: FPGA-H1-PROTOTYPE-001 (4 LUT4s, 1 CLB, 1x1 grid)
3. Physical Quad-CLB Prototype: FPGA-H1-PROTOTYPE-004 (16 LUT4s, 4 CLBs, 2x2 grid)
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class DeviceProfile:
    name: str
    category: str  # "virtual" or "physical"
    grid_w: int
    grid_h: int
    clb_count: int
    lut_count: int
    dff_count: int
    channel_width: int
    max_inputs: int
    max_outputs: int
    clock_frequency_mhz_est: float
    description: str


# Predefined official profiles
PROFILES: Dict[str, DeviceProfile] = {
    "FPGA-H1-GW1NR9": DeviceProfile(
        name="FPGA-H1-GW1NR9",
        category="virtual",
        grid_w=47,
        grid_h=47,
        clb_count=2209,
        lut_count=8836,
        dff_count=8836,
        channel_width=8,
        max_inputs=188,
        max_outputs=188,
        clock_frequency_mhz_est=150.0,
        description="Full-scale virtual architecture matching nominal Gowin GW1NR-9 capacity (8,640 LUT4 nominal + 196 spare)."
    ),
    "FPGA-H1-PROTOTYPE-001": DeviceProfile(
        name="FPGA-H1-PROTOTYPE-001",
        category="physical",
        grid_w=1,
        grid_h=1,
        clb_count=1,
        lut_count=4,
        dff_count=4,
        channel_width=4,
        max_inputs=16,
        max_outputs=4,
        clock_frequency_mhz_est=10.0,
        description="First physical discrete/ASIC prototype: 1 CLB (4 BLEs = 4 LUT4 + 4 DFF) for didactic and hardware bring-up."
    ),
    "FPGA-H1-PROTOTYPE-004": DeviceProfile(
        name="FPGA-H1-PROTOTYPE-004",
        category="physical",
        grid_w=2,
        grid_h=2,
        clb_count=4,
        lut_count=16,
        dff_count=16,
        channel_width=4,
        max_inputs=32,
        max_outputs=16,
        clock_frequency_mhz_est=10.0,
        description="Second-stage physical prototype: 4 CLBs (16 BLEs = 16 LUT4 + 16 DFF) with 4 Wilton Switch Boxes."
    )
}


def get_profile(name: Optional[str] = None) -> DeviceProfile:
    """Returns requested device profile; defaults to virtual FPGA-H1-GW1NR9."""
    if not name:
        return PROFILES["FPGA-H1-GW1NR9"]
    normalized = name.strip().upper()
    if normalized in PROFILES:
        return PROFILES[normalized]
    # Check aliases
    if "001" in normalized or "PROTO" in normalized or "PROTOTYPE" in normalized:
        return PROFILES["FPGA-H1-PROTOTYPE-001"]
    return PROFILES["FPGA-H1-GW1NR9"]


def validate_circuit_against_profile(profile: DeviceProfile, lut_count: int, dff_count: int, inputs_count: int, outputs_count: int) -> List[str]:
    """Checks circuit utilization against physical profile constraints and returns warnings/errors."""
    issues = []
    if lut_count > profile.lut_count:
        issues.append(
            f"Device '{profile.name}' LUT capacity exceeded: circuit requires {lut_count} LUTs, device only supports {profile.lut_count}."
        )
    if dff_count > profile.dff_count:
        issues.append(
            f"Device '{profile.name}' DFF capacity exceeded: circuit requires {dff_count} DFFs, device only supports {profile.dff_count}."
        )
    if inputs_count > profile.max_inputs:
        issues.append(
            f"Device '{profile.name}' input pin limit exceeded: circuit requires {inputs_count} inputs, device provides {profile.max_inputs}."
        )
    if outputs_count > profile.max_outputs:
        issues.append(
            f"Device '{profile.name}' output pin limit exceeded: circuit requires {outputs_count} outputs, device provides {profile.max_outputs}."
        )
    return issues
