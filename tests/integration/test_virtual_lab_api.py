"""
Integration Tests for FPGA-H1 Virtual Lab Backend API & Simulation Engine.
Tests REST API endpoints, full compilation pipeline stages, simulation stepping,
dynamic LUT modification, bitstream download, and benchmarks.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import init_db

init_db()
client = TestClient(app)


def test_health_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert data["architecture"]["lut_type"] == "LUT4"
    assert data["architecture"]["clb_size"] == 4
    assert data["architecture"]["switch_box"] == "Wilton Fs=3"
    assert "8,640" in data["architecture"]["reference_target"]


def test_projects_crud():
    # 1. List seeded projects
    res = client.get("/api/projects")
    assert res.status_code == 200
    projects = res.json()
    assert len(projects) >= 10
    names = [p["name"] for p in projects]
    assert "alu4" in names
    assert "counter4" in names
    assert "pipeline3" in names

    # 2. Create custom project
    create_res = client.post("/api/projects", json={
        "name": "test_inv",
        "description": "Simple inverter test",
        "category": "tests",
        "source_code": "DEVICE INV\nINPUT A\nOUTPUT Y\nASSIGN Y = ~A\nEND\n"
    })
    assert create_res.status_code == 200
    proj_id = create_res.json()["id"]

    # 3. Get project
    get_res = client.get(f"/api/projects/{proj_id}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "test_inv"

    # 4. Delete project
    del_res = client.delete(f"/api/projects/{proj_id}")
    assert del_res.status_code == 200
    assert client.get(f"/api/projects/{proj_id}").status_code == 404


def test_compile_pipeline_stages_alu4():
    proj = [p for p in client.get("/api/projects").json() if p["name"] == "alu4"][0]
    full_proj = client.get(f"/api/projects/{proj['id']}").json()

    compile_res = client.post("/api/compile", json={
        "source_code": full_proj["source_code"],
        "project_id": proj["id"],
        "channel_width": 8
    })
    assert compile_res.status_code == 200
    data = compile_res.json()

    assert data["success"] is True
    assert data["device"] == "ALU4"
    assert data["resources"]["luts_used"] >= 16
    assert data["resources"]["dffs_used"] >= 4
    assert data["resources"]["clbs_used"] >= 4

    # Check all 8 pipeline stages exist and succeeded
    stages = data["stages"]
    stage_keys = ["lexer", "parser", "elaborator", "optimizer", "netlist", "placement", "routing", "bitstream"]
    for k in stage_keys:
        assert k in stages, f"Missing stage {k}"
        assert stages[k]["status"] == "success", f"Stage {k} failed: {stages[k].get('error')}"
        assert stages[k]["duration_ms"] >= 0

    # Bitstream check
    assert data["bitstream_hex"].startswith("48314253")  # 'H1BS'
    assert data["bitstream_size_bytes"] > 0
    assert data["compilation_id"] is not None

    # Placement and routing checks
    assert data["placement"]["grid_w"] >= 2
    assert len(data["placement"]["clbs"]) >= 4
    assert stages["routing"]["routed_nets_pct"] == 100.0


def test_simulation_stepping_and_lut_update():
    # Compile adder4
    adder_code = """
    DEVICE ADDER4
    INPUT A[4], B[4]
    OUTPUT SUM[4]
    LUT FA0(A[0], B[0], 0, 0) = 0x6666
    LUT FA1(A[1], B[1], 0, 0) = 0x6666
    LUT FA2(A[2], B[2], 0, 0) = 0x6666
    LUT FA3(A[3], B[3], 0, 0) = 0x6666
    ASSIGN SUM[0] = FA0
    ASSIGN SUM[1] = FA1
    ASSIGN SUM[2] = FA2
    ASSIGN SUM[3] = FA3
    END
    """
    comp = client.post("/api/compile", json={"source_code": adder_code})
    assert comp.json()["success"] is True

    # 1. Step simulation
    step1 = client.post("/api/simulate/step", json={"inputs": {"A[0]": 1, "B[0]": 1}})
    assert step1.status_code == 200
    st1 = step1.json()
    assert st1["cycle"] == 1
    # FA0 XOR(1, 1) = 0 with mask 0x6666
    assert st1["outputs"]["SUM[0]"] == 0

    # 2. Dynamic LUT mask modification (change FA0 to AND: mask 0x8888)
    lut_up = client.post("/api/lut/update", json={"ble_name": "FA0", "mask": 0x8888})
    assert lut_up.status_code == 200
    assert lut_up.json()["new_mask"] == "0x8888"

    # 3. Step again: with A[0]=1, B[0]=1, AND produces 1
    step2 = client.post("/api/simulate/step", json={"inputs": {"A[0]": 1, "B[0]": 1}})
    assert step2.status_code == 200
    st2 = step2.json()
    assert st2["outputs"]["SUM[0]"] == 1

    # 4. Reset simulation
    rst = client.post("/api/simulate/reset")
    assert rst.status_code == 200
    assert rst.json()["cycle"] == 0


def test_bitstream_download():
    # Compile small circuit
    code = "DEVICE DUMMY\nINPUT I\nOUTPUT O\nASSIGN O = I\nEND\n"
    res = client.post("/api/compile", json={"source_code": code}).json()
    comp_id = res["compilation_id"]
    assert comp_id is not None

    down = client.get(f"/api/bitstream/download/{comp_id}")
    assert down.status_code == 200
    assert down.content[:4] == b"H1BS"
    assert "attachment" in down.headers["content-disposition"]
