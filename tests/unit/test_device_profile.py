"""
Unit Tests for FPGA-H1 Device Profiles and Hardware Feasibility Constraints
"""

import pytest
from compiler.device_profile import get_profile, validate_circuit_against_profile, PROFILES
from compiler.compiler import H1LCompiler
from fastapi.testclient import TestClient
from backend.main import app


def test_profile_lookup_and_defaults():
    p_default = get_profile()
    assert p_default.name == "FPGA-H1-GW1NR9"
    assert p_default.category == "virtual"
    assert p_default.lut_count == 8836

    p_proto = get_profile("FPGA-H1-PROTOTYPE-001")
    assert p_proto.name == "FPGA-H1-PROTOTYPE-001"
    assert p_proto.category == "physical"
    assert p_proto.lut_count == 4
    assert p_proto.clb_count == 1

    p_proto4 = get_profile("FPGA-H1-PROTOTYPE-004")
    assert p_proto4.lut_count == 16
    assert p_proto4.clb_count == 4


def test_prototype_001_compilation_success_under_limit():
    compiler = H1LCompiler(device_profile="FPGA-H1-PROTOTYPE-001")
    code = """
    DEVICE SMALL_AND
    INPUT A, B
    OUTPUT Y
    ASSIGN Y = A & B
    END
    """
    res = compiler.compile(code)
    assert res.success is True
    assert res.lut_count == 1
    assert res.profile_validation["valid"] is True
    assert len(res.warnings) == 0


def test_prototype_001_warning_on_capacity_exceeded():
    compiler = H1LCompiler(device_profile="FPGA-H1-PROTOTYPE-001")
    # Circuit requesting 5 LUTs (exceeding 4 LUT capacity of PROTOTYPE-001)
    code = """
    DEVICE OVERFLOW_CIRCUIT
    INPUT A, B, C, D, E, F
    OUTPUT Y1, Y2, Y3, Y4, Y5
    ASSIGN Y1 = A & B
    ASSIGN Y2 = B | C
    ASSIGN Y3 = C ^ D
    ASSIGN Y4 = D & E
    ASSIGN Y5 = E | F
    END
    """
    res = compiler.compile(code)
    assert res.lut_count == 5
    assert res.profile_validation["valid"] is False
    assert any("LUT capacity exceeded" in w for w in res.warnings)


def test_api_profiles_endpoint():
    client = TestClient(app)
    response = client.get("/api/profiles")
    assert response.status_code == 200
    data = response.json()
    assert "FPGA-H1-GW1NR9" in data
    assert "FPGA-H1-PROTOTYPE-001" in data
    assert data["FPGA-H1-PROTOTYPE-001"]["lut_count"] == 4
