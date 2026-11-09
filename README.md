# FPGA-H1 Virtual Lab

Laboratorio de investigación, simulación, optimización y diseño de arquitecturas FPGA experimentales de bajo costo, escalable desde 4 LUT4 hasta 8.640 LUT4 (referencia: Gowin GW1NR-9 / Tang Nano 9K).

---

## 🚀 Misión del Proyecto

FPGA-H1 no utiliza un FPGA comercial como solución final. Investiga cómo construir una arquitectura lógica programable propia y abierta:
1. **Modelado Matemático Determinista:** Celdas LUT4 de 16 bits de SRAM, D-Flip-Flops con reset síncrono/asíncrono y multiplexor de bypass combinacional/secuencial.
2. **Red de Interconexión Conmutable (Island-Style Routing):** Canales ortogonales $X/Y$, Switch Boxes Wilton ($F_s = 3$) y Connection Boxes (CB) con algoritmo Pathfinder para resolución de congestión negociada.
3. **Formato de Bitstream Binario Propietario (H1BS):** Formato basado en tramas con validación por redundancia cíclica (CRC32 IEEE 802.3).
4. **Primer Circuito Completo (ALU4):** ALU de 4 bits implementada exclusivamente con recursos lógicos nativos (ADD, SUB, AND, OR, XOR, NOT, CMP y salida registrada).
5. **Simulación y Benchmarking de Alto Rendimiento:** > 13.6 Millones de evaluaciones LUT4/segundo y > 5.100 ciclos de simulación completa por segundo.

---

## 📂 Estructura del Repositorio

```
FPGA-H1-Virtual-Lab/
├── docs/
│   ├── ARCHITECTURE.md          # Arquitectura general y comparación con Gowin GW1NR-9
│   ├── LOGIC_MODEL.md           # Modelo matemático formal de la LUT4 y BLE
│   ├── ROUTING_MODEL.md         # Comparación de 3 arquitecturas de ruteo y Switch Boxes
│   ├── CONFIGURATION_FORMAT.md  # Especificación del bitstream binario H1BS
│   ├── ROADMAP.md               # Hoja de ruta de ingeniería en 10 fases
│   ├── HARDWARE_MAPPING.md      # Análisis físico (74HC, RP2040, CPLD, ASIC SkyWater 130nm)
│   ├── INFRASTRUCTURE_AUDIT.md  # Inventario de servidores y GPUs auditados
│   └── PHASE1_EVALUATION_REPORT.md # Resultados de pruebas y métricas de rendimiento
├── architecture/
│   └── blocks/
│       ├── lut4/
│       │   ├── lut4_core.py     # Celda elemental LUT4 (16 bits de configuración)
│       │   ├── ble.py           # Basic Logic Element (LUT4 + DFF + Bypass + Carry)
│       │   └── clb.py           # Configurable Logic Block (Cluster de 4 BLEs)
│       └── flipflops/
│           └── dff.py           # D-Flip-Flop con async/sync reset y clock enable
├── simulator/
│   └── logic/
│       └── engine.py            # Motor de simulación funcional y topológica
├── compiler/
│   └── bitstream/
│       └── bitstream_codec.py   # Codificador y decodificador binario H1BS con CRC32
├── examples/
│   └── alu4/
│       └── alu4_circuit.py      # ALU de 4 bits completa construida en FPGA-H1
├── tests/
│   ├── unit/                    # 16 pruebas unitarias (LUT4, DFF, BLE, CLB, Bitstream)
│   └── integration/             # Pruebas de integración de ALU4 (256 ADDs, 256 SUBs, Lógica)
└── benchmarks/
    └── scripts/
        └── benchmark_lut_engine.py # Script de telemetría y medición de velocidad
```

---

## ⚡ Ejecución de Pruebas y Benchmarks

### 1. Ejecución de Pruebas Unitarias
```bash
python -m pytest tests/unit -v
```

### 2. Ejecución de Pruebas de Integración (ALU4)
```bash
python -m pytest tests/integration -v
```

### 3. Ejecución de la Suite de Benchmarking
```bash
python benchmarks/scripts/benchmark_lut_engine.py
```

---

## 📊 Métricas de Desempeño Medidas (Fase 1)

- **Evaluaciones brutas de LUT4:** **13.684.616 evals/seg**.
- **Ciclos de simulación de circuito completo ALU4:** **5.158 ciclos/seg**.
- **Memoria RAM ocupada por el proceso:** **15.71 MB RSS**.
- **Tasa de éxito en pruebas formales:** **100% (19/19 suites aprobadas)**.
