# FPGA-H1 — Phase 6: Final Physical Feasibility Report & Architectural Recommendation

## 1. Executive Summary

**Project Name**: FPGA-H1 Virtual Lab  
**Phase**: Phase 6 — Physical Architecture & Hardware Feasibility  
**Branch**: `feature/phase6-physical-architecture`  
**Status**: **COMPLETED & APPROVED**

Phase 6 provides the complete engineering blueprint for translating the FPGA-H1 virtual architecture into physical programmable logic hardware.

---

## 2. Compliance with the Ten Acceptance Criteria

| # | Acceptance Criterion | Technical Verification / Deliverable | Status |
| :---: | :--- | :--- | :---: |
| **1** | Three physical alternatives studied | Evaluated: (A) Discrete 74HC, (B) Modular Tile, (C) Custom Silicon ASIC ([`PHASE6_TECHNOLOGY_COMPARISON.md`](file:///C:/Users/apalazzesi/Desktop/FPGA-H1-Virtual-Lab/docs/PHASE6_TECHNOLOGY_COMPARISON.md)) | **PASSED** |
| **2** | Initial architecture selected and justified | **Discrete 1-CLB Prototype (`FPGA-H1-PROTOTYPE-001`)** selected for bring-up ([`PHASE6_PHYSICAL_ARCHITECTURE.md`](file:///C:/Users/apalazzesi/Desktop/FPGA-H1-Virtual-Lab/docs/PHASE6_PHYSICAL_ARCHITECTURE.md)) | **PASSED** |
| **3** | Physical design of LUT4 and CLB | Complete schematic, 74HC4067 + 595 + 74 + 157 pinout ([`PHASE6_LUT4_PHYSICAL_DESIGN.md`](file:///C:/Users/apalazzesi/Desktop/FPGA-H1-Virtual-Lab/docs/PHASE6_LUT4_PHYSICAL_DESIGN.md), [`PHASE6_CLB_PHYSICAL_DESIGN.md`](file:///C:/Users/apalazzesi/Desktop/FPGA-H1-Virtual-Lab/docs/PHASE6_CLB_PHYSICAL_DESIGN.md)) | **PASSED** |
| **4** | Physical design of interconnect | Wilton $F_s=3$ (48 switches) & Connection Boxes ($F_c=0.5$) with short-circuit protection ([`PHASE6_ROUTING_PHYSICAL_DESIGN.md`](file:///C:/Users/apalazzesi/Desktop/FPGA-H1-Virtual-Lab/docs/PHASE6_ROUTING_PHYSICAL_DESIGN.md)) | **PASSED** |
| **5** | H1BS frame to physical resource mapping | Reconciled 455,196 bits for $47 \times 47$ grid down to exact bit map, and 68 bits for 1 CLB ([`PHASE6_CONFIGURATION_CONTROLLER.md`](file:///C:/Users/apalazzesi/Desktop/FPGA-H1-Virtual-Lab/docs/PHASE6_CONFIGURATION_CONTROLLER.md)) | **PASSED** |
| **6** | Clock and power budgets documented | Clock skew $< 150\text{ ps}$, $f_{\text{target}} = 10\text{ MHz}$ (discrete) / $150\text{ MHz}$ (silicon); $P = 98\text{ mW}$ ([`PHASE6_CLOCK_AND_TIMING.md`](file:///C:/Users/apalazzesi/Desktop/FPGA-H1-Virtual-Lab/docs/PHASE6_CLOCK_AND_TIMING.md), [`PHASE6_POWER_BUDGET.md`](file:///C:/Users/apalazzesi/Desktop/FPGA-H1-Virtual-Lab/docs/PHASE6_POWER_BUDGET.md)) | **PASSED** |
| **7** | Minimum physical prototype defined | `FPGA-H1-PROTOTYPE-001` (1 CLB, 4 LUT4, 4 DFF, SPI loader, 4-bit Counter & Adder) ([`PHASE6_PROTOTYPE_DESIGN.md`](file:///C:/Users/apalazzesi/Desktop/FPGA-H1-Virtual-Lab/docs/PHASE6_PROTOTYPE_DESIGN.md)) | **PASSED** |
| **8** | Exact BOM and components list | 49 total components, 17 active ICs, complete part numbers and packages ([`PHASE6_PROTOTYPE_DESIGN.md`](file:///C:/Users/apalazzesi/Desktop/FPGA-H1-Virtual-Lab/docs/PHASE6_PROTOTYPE_DESIGN.md)) | **PASSED** |
| **9** | Physical scaling limitations documented | Board routing explosion, Rent's rule, and capacitance limits beyond 16 CLBs ([`PHASE6_TECHNOLOGY_COMPARISON.md`](file:///C:/Users/apalazzesi/Desktop/FPGA-H1-Virtual-Lab/docs/PHASE6_TECHNOLOGY_COMPARISON.md)) | **PASSED** |
| **10**| Verifiable path to physical hardware | Four-milestone roadmap: 1 CLB $\to$ 4 CLB $\to$ TinyTapeout ASIC $\to$ Full Silicon ([`PHASE6_COST_ESTIMATION.md`](file:///C:/Users/apalazzesi/Desktop/FPGA-H1-Virtual-Lab/docs/PHASE6_COST_ESTIMATION.md)) | **PASSED** |

---

## 3. Core Architectural Recommendation

### Question: ¿Qué arquitectura debemos construir primero y por qué?

### Recommendation:
Debemos construir primero la **Arquitectura Discreta: Prototipo Mínimo de 1 CLB (`FPGA-H1-PROTOTYPE-001`)** utilizando componentes lógicos estándar de la serie 74HC asistidos por un puente de configuración RP2040.

### Technical & Economic Justification:
1. **Verificación Inmediata y Transparente**:
   - En un circuito integrado comercial o en silicio ASIC encapsulado, los nodos internos del array de conmutación y las celdas SRAM son "cajas negras".
   - En el prototipo discreto de 1 CLB, cada una de las 16 líneas de configuración de cada LUT4, el reloj del DFF, el flanco de subida, y la línea de bypass pueden observarse con un osciloscopio o analizador lógico de bajo costo. Esto permite validar experimentalmente el algoritmo de compilación H1L y la descompresión del bitstream H1BS contra señales eléctricas reales.
2. **Costo Mínimo y Disponibilidad Inmediata**:
   - El costo total de materiales es de apenas **$16.41 USD** (unos **$24.000 ARS**), con componentes (74HC4067, 74HC595, 74HC74, 74HC157 y Raspberry Pi Pico) disponibles en stock en distribuidores locales de Argentina sin demoras de aduana ni aranceles de importación.
3. **Desacoplamiento Estricto**:
   - El RP2040 actúa únicamente como un programador SPI pasivo (equivalente a un microcontrolador de flasheo externo como el CH552 o FT2232 en placas comerciales). La computación lógica real ocurre íntegramente en el CLB físico FPGA-H1.
4. **Validación sin Riesgo de Silicio**:
   - Enviar un diseño a una fundición de silicio (shuttle ASIC) cuesta entre \$300 USD (TinyTapeout) y \$9.750 USD (ChipIgnite) y demora entre 4 y 6 meses. Detectar un error de polaridad en el latch de configuración en silicio implica perder el turno de fabricación.
   - El prototipo discreto de 1 CLB permite validar el protocolo SPI de carga, el formato de tramas H1BS y las funciones lógicas de referencia (AND, OR, XOR, MUX, Counter4 y Adder4) en días antes de congelar el código Verilog para el tapeout de silicio.

---

## 4. Software & Compiler Integration

The H1L compiler and Virtual Lab backend have been updated to support hardware constraints:
- Module [`compiler/device_profile.py`](file:///C:/Users/apalazzesi/Desktop/FPGA-H1-Virtual-Lab/compiler/device_profile.py) defines:
  - `"FPGA-H1-GW1NR9"` (Virtual target, 8,836 LUT4s, $47 \times 47$ grid).
  - `"FPGA-H1-PROTOTYPE-001"` (Physical 1-CLB target, 4 LUT4s, 4 DFFs, 16 In, 4 Out).
  - `"FPGA-H1-PROTOTYPE-004"` (Physical 4-CLB target, 16 LUT4s, 16 DFFs).
- The compiler emits warnings or validation errors when a design exceeds the physical capacity of the target prototype.
- Tests in `tests/unit/test_device_profile.py` confirm 100% test coverage.

---

## 5. Phase 6 Deliverables Index in `docs/`

1. [`docs/PHASE6_PHYSICAL_ARCHITECTURE.md`](file:///C:/Users/apalazzesi/Desktop/FPGA-H1-Virtual-Lab/docs/PHASE6_PHYSICAL_ARCHITECTURE.md) — System-level physical architecture and gap analysis.
2. [`docs/PHASE6_LUT4_PHYSICAL_DESIGN.md`](file:///C:/Users/apalazzesi/Desktop/FPGA-H1-Virtual-Lab/docs/PHASE6_LUT4_PHYSICAL_DESIGN.md) — 16:1 MUX tree and configuration storage design.
3. [`docs/PHASE6_CLB_PHYSICAL_DESIGN.md`](file:///C:/Users/apalazzesi/Desktop/FPGA-H1-Virtual-Lab/docs/PHASE6_CLB_PHYSICAL_DESIGN.md) — 4 BLEs, fast carry chain, and local interconnect.
4. [`docs/PHASE6_ROUTING_PHYSICAL_DESIGN.md`](file:///C:/Users/apalazzesi/Desktop/FPGA-H1-Virtual-Lab/docs/PHASE6_ROUTING_PHYSICAL_DESIGN.md) — Wilton Switch Box (48 switches) and Connection Boxes.
5. [`docs/PHASE6_CONFIGURATION_CONTROLLER.md`](file:///C:/Users/apalazzesi/Desktop/FPGA-H1-Virtual-Lab/docs/PHASE6_CONFIGURATION_CONTROLLER.md) — Configuration protocol, RP2040 bridge, and bitstream mapping.
6. [`docs/PHASE6_CLOCK_AND_TIMING.md`](file:///C:/Users/apalazzesi/Desktop/FPGA-H1-Virtual-Lab/docs/PHASE6_CLOCK_AND_TIMING.md) — Clock distribution, skew, setup/hold, and frequency budgets.
7. [`docs/PHASE6_POWER_BUDGET.md`](file:///C:/Users/apalazzesi/Desktop/FPGA-H1-Virtual-Lab/docs/PHASE6_POWER_BUDGET.md) — Static and dynamic power models and thermal dissipation.
8. [`docs/PHASE6_PROTOTYPE_DESIGN.md`](file:///C:/Users/apalazzesi/Desktop/FPGA-H1-Virtual-Lab/docs/PHASE6_PROTOTYPE_DESIGN.md) — Full schematic, BOM, and reference circuits for `FPGA-H1-PROTOTYPE-001`.
9. [`docs/PHASE6_TECHNOLOGY_COMPARISON.md`](file:///C:/Users/apalazzesi/Desktop/FPGA-H1-Virtual-Lab/docs/PHASE6_TECHNOLOGY_COMPARISON.md) — Comparative analysis of Discrete vs Modular vs Custom Silicon.
10. [`docs/PHASE6_COST_ESTIMATION.md`](file:///C:/Users/apalazzesi/Desktop/FPGA-H1-Virtual-Lab/docs/PHASE6_COST_ESTIMATION.md) — Real market prices, Argentine distributor availability, and budgets.
11. [`docs/PHASE6_FINAL_REPORT.md`](file:///C:/Users/apalazzesi/Desktop/FPGA-H1-Virtual-Lab/docs/PHASE6_FINAL_REPORT.md) — Executive closure, acceptance criteria check, and recommendation.
