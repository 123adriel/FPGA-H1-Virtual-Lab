# VALIDACIÓN FORMAL Y EQUIVALENCIA: COMPILADOR H1L

Proyecto: **FPGA-H1 Virtual Lab**  
Documento: `docs/COMPILER_VALIDATION.md`  
Estado: Fase 3 Aprobada

---

## 1. Metodología de Validación

Para asegurar que el compilador no introduzca alteraciones en la función de transferencia booleana, se establecieron dos ejes de auditoría formal:

1. **Pruebas de Rechazo Estricto:** Comprobación de que cualquier fuente sintáctica o semánticamente inválida sea rechazada con un mensaje de error claro y termine sin producir hardware inconsistente.
2. **Equivalencia de 3 Vías (3-Way Equivalence):** Para un circuito compilado, la salida booleana debe ser estrictamente idéntica entre:
   - **(A) Modelo de Referencia Matemático:** Función pura en Python.
   - **(B) Simulación en `CircuitEngine`:** Netlist compilada con ordenamiento topológico.
   - **(C) Circuito Restaurado desde Bitstream H1BS:** Fabric físico reconstruido exclusivamente leyendo el archivo `.h1b` con CRC-32.

---

## 2. Casos de Rechazo Verificados (`tests/formal/test_compiler_audit.py`)

| Escenario de Falla Intencional | Etapa que Detecta | Excepción Lanzada | Resultado |
|---|---|---|---|
| Carácter no reconocido (`@`, `$`) | Lexer | `LexerError: Unexpected character '@'` | **RECHAZADO** |
| Bloque sin cerrar (falta `END`) | Parser | `ParserError: Expected 'END'` | **RECHAZADO** |
| Señal no declarada en expresión | Elaborador | `ElaboratorError: Undeclared signal` | **RECHAZADO** |
| Múltiples drivers en un conductor | Elaborador | `ElaboratorError: Multiple drivers detected` | **RECHAZADO** |
| Conexión fuera de topología Wilton | Routing | `ValueError: not realizable in Wilton` | **RECHAZADO** |
| Conflicto de doble excitador en canal | ConnectionBox | `RuntimeError: Short-circuit conflict` | **RECHAZADO** |

---

## 3. Cobertura de los 10 Circuitos Canónicos

| Circuito | Archivo H1L | LUTs Sintetizadas | Registros DFF | Salida Bitstream H1BS | Simulación Funcional |
|---|---|---|---|---|---|
| **Compuertas Lógicas** | `gates/logic_gates.h1l` | 4 LUT4 | 0 | 44 bytes | Verificada (100%) |
| **Multiplexor 4:1** | `gates/mux4.h1l` | 3 LUT4 | 0 | 42 bytes | Verificada (100%) |
| **Contador de 4 bits** | `counters/counter4.h1l` | 4 LUT4 | 4 DFF | 56 bytes | Verificada (100%) |
| **Contador de 8 bits** | `counters/counter8.h1l` | 8 LUT4 | 8 DFF | 88 bytes | Verificada (100%) |
| **Registro con Enable** | `counters/reg_enable.h1l`| 1 LUT4 | 1 DFF | 38 bytes | Verificada (100%) |
| **Sumador de 4 bits** | `alu4/adder4.h1l` | 13 LUT4 | 0 | 92 bytes | Verificada (100%) |
| **ALU de 4 bits** | `alu4/alu4.h1l` | 8 LUT4 | 4 DFF | 78 bytes | Verificada (100%) |
| **ALU de 8 bits** | `alu8/alu8.h1l` | 16 LUT4 | 8 DFF | 136 bytes | Verificada (100%) |
| **FSM Semáforo** | `processors/fsm_traffic.h1l` | 5 LUT4 | 2 DFF | 58 bytes | Verificada (100%) |
| **Pipeline de 3 etapas**| `processors/pipeline3.h1l` | 8 LUT4 | 12 DFF | 94 bytes | Verificada (100%) |
