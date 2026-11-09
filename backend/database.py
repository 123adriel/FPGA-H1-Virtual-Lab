"""
SQLite Database Layer - FPGA-H1 Virtual Lab
Stores projects, compilation history, and performance benchmarks.
"""

import sqlite3
import os
import json
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional

DB_PATH = Path(__file__).resolve().parent / "fpga_h1.db"


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        category TEXT DEFAULT 'general',
        source_code TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS compilations (
        id TEXT PRIMARY KEY,
        project_id TEXT,
        success INTEGER NOT NULL,
        device_name TEXT,
        lut_count INTEGER DEFAULT 0,
        dff_count INTEGER DEFAULT 0,
        clb_count INTEGER DEFAULT 0,
        io_pins INTEGER DEFAULT 0,
        bitstream_hex TEXT,
        bitstream_size_bytes INTEGER DEFAULT 0,
        stages_data TEXT,
        placement_data TEXT,
        routing_data TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS benchmarks (
        id TEXT PRIMARY KEY,
        scale_name TEXT NOT NULL,
        target_luts INTEGER NOT NULL,
        grid_w INTEGER NOT NULL,
        grid_h INTEGER NOT NULL,
        compile_time_ms REAL NOT NULL,
        placement_time_ms REAL NOT NULL,
        routing_time_ms REAL NOT NULL,
        bitstream_time_ms REAL NOT NULL,
        sim_step_us REAL NOT NULL,
        memory_kb REAL NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    conn.close()

    # Seed default examples if table is empty
    seed_examples_if_empty()


def seed_examples_if_empty():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as cnt FROM projects")
    count = cur.fetchone()["cnt"]

    if count == 0:
        base_dir = Path(__file__).resolve().parent.parent / "examples"
        example_files = [
            ("alu4", "alu4/alu4.h1l", "4-bit Arithmetic Logic Unit with Add, Sub, AND, OR, XOR and Flag generation"),
            ("adder4", "alu4/adder4.h1l", "4-bit Ripple Carry Full Adder with direct LUT4 truth tables"),
            ("alu8", "alu8/alu8.h1l", "8-bit Arithmetic Logic Unit supporting multi-bus arithmetic"),
            ("counter4", "counters/counter4.h1l", "4-bit synchronous binary up-counter with registered DFFs"),
            ("counter8", "counters/counter8.h1l", "8-bit synchronous binary counter"),
            ("reg_enable", "counters/reg_enable.h1l", "4-bit register with synchronous clock enable and load"),
            ("logic_gates", "gates/logic_gates.h1l", "Basic digital combinational gates (AND, OR, XOR, NOT)"),
            ("mux4", "gates/mux4.h1l", "4-to-1 multiplexer circuit with 2-bit select bus"),
            ("fsm_traffic", "processors/fsm_traffic.h1l", "Traffic light Finite State Machine controller with sequential state transitions"),
            ("pipeline3", "processors/pipeline3.h1l", "3-stage pipelined compute circuit with intermediate registers")
        ]

        for name, rel_path, desc in example_files:
            file_path = base_dir / rel_path
            if file_path.exists():
                code = file_path.read_text(encoding="utf-8")
                category = rel_path.split("/")[0]
                cur.execute(
                    "INSERT INTO projects (id, name, description, category, source_code) VALUES (?, ?, ?, ?, ?)",
                    (str(uuid.uuid4()), name, desc, category, code)
                )

        conn.commit()

    conn.close()


def list_projects() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, description, category, created_at, updated_at FROM projects ORDER BY name ASC")
    rows = cur.fetchall()
    projects = [dict(r) for r in rows]
    conn.close()
    return projects


def get_project(project_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def create_or_update_project(name: str, source_code: str, description: str = "", category: str = "custom", project_id: Optional[str] = None) -> Dict[str, Any]:
    conn = get_db_connection()
    cur = conn.cursor()

    if project_id:
        cur.execute(
            "UPDATE projects SET name = ?, source_code = ?, description = ?, category = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (name, source_code, description, category, project_id)
        )
        pid = project_id
    else:
        pid = str(uuid.uuid4())
        cur.execute(
            "INSERT INTO projects (id, name, description, category, source_code) VALUES (?, ?, ?, ?, ?)",
            (pid, name, description, category, source_code)
        )

    conn.commit()
    conn.close()
    return get_project(pid) # type: ignore


def save_compilation(project_id: Optional[str], result_data: Dict[str, Any]) -> str:
    comp_id = str(uuid.uuid4())
    conn = get_db_connection()
    cur = conn.cursor()

    res = result_data.get("resources", {})
    cur.execute("""
    INSERT INTO compilations (
        id, project_id, success, device_name, lut_count, dff_count, clb_count, io_pins,
        bitstream_hex, bitstream_size_bytes, stages_data, placement_data, routing_data
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        comp_id,
        project_id,
        1 if result_data.get("success") else 0,
        result_data.get("device", ""),
        res.get("luts_used", 0),
        res.get("dffs_used", 0),
        res.get("clbs_used", 0),
        res.get("io_pins", 0),
        result_data.get("bitstream_hex", ""),
        result_data.get("bitstream_size_bytes", 0),
        json.dumps(result_data.get("stages", {})),
        json.dumps(result_data.get("placement", {})),
        json.dumps(result_data.get("routing", {}))
    ))

    conn.commit()
    conn.close()
    return comp_id


def save_benchmark(data: Dict[str, Any]) -> str:
    bid = str(uuid.uuid4())
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO benchmarks (
        id, scale_name, target_luts, grid_w, grid_h, compile_time_ms,
        placement_time_ms, routing_time_ms, bitstream_time_ms, sim_step_us, memory_kb
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        bid,
        data["scale_name"],
        data["target_luts"],
        data["grid_w"],
        data["grid_h"],
        data["compile_time_ms"],
        data["placement_time_ms"],
        data["routing_time_ms"],
        data["bitstream_time_ms"],
        data["sim_step_us"],
        data["memory_kb"]
    ))
    conn.commit()
    conn.close()
    return bid


def get_latest_benchmarks() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM benchmarks ORDER BY target_luts ASC")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]
