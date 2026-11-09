# SISTEMA DE TIPOS Y SEMÁNTICA: LENGUAJE H1L

Proyecto: **FPGA-H1 Virtual Lab**  
Documento: `docs/H1L_TYPE_SYSTEM.md`  
Estado: Fase 3

---

## 1. Tipos Fundamentales en H1L

El sistema de tipos de H1L está estrictamente diseñado para reflejar la física de hardware de interconexión digital:

| Tipo H1L | Notación | Descripción Física | Valores Posibles |
|---|---|---|---|
| **`BIT` (Escalar)** | `WIRE A`, `INPUT CLK` | Un conductor individual (red / net) | `'0'`, `'1'`, `'X'` (indeterminado) |
| **`BUS[W]` (Vectorial)** | `WIRE DATA[8]`, `INPUT A[4]` | Arreglo ordenado de $W$ conductores paralelos | $[0, 2^W - 1]$ |
| **`LITERAL`** | `0x6996`, `0b1010`, `42` | Constante entera evaluada en tiempo de compilación | Sin signo / Con signo según contexto |
| **`CLOCK`** | `CLOCK CLK` | Red de reloj global de baja distorsión (*low-skew*) | Flancos de subida y bajada |
| **`RESET`** | `RESET RST` | Red de inicialización prioritaria | Nivel alto activo |

---

## 2. Reglas de Compatibilidad y Ancho de Señales

1. **Invariante de Asignación:**
   En una asignación `ASSIGN LHS = RHS;` o registro `REGISTER R[N] <= EXPR;`:
   $$\text{width}(\text{LHS}) == \text{width}(\text{RHS})$$
   Si el ancho difiere, el elaborador emite un error de tipo:
   `TypeError: Width mismatch: LHS has width N but RHS produces M bits`.
2. **Extensión de Constantes:**
   Si una constante sin tamaño especificado (ej. `0`) se asigna a un bus de ancho $N$, el compilador realiza extensión a cero automática (*zero-extension*) a $N$ bits.
3. **Indexación y Segmentación (*Slicing*):**
   - Acceso escalar: `A[i]` extrae el bit $i$, produciendo un tipo `BIT` (ancho 1).
   - Acceso de rango: `A[high:low]` extrae $high - low + 1$ bits, produciendo `BUS[high - low + 1]`.
   - Límite estricto: $0 \le low \le high < \text{width}(A)$. Cualquier índice fuera de rango causa error de compilación inmediato.
4. **Concatenación:**
   La sintaxis `{ A, B, C }` produce un nuevo bus con ancho igual a:
   $$\text{width}(\{A, B, C\}) = \text{width}(A) + \text{width}(B) + \text{width}(C)$$

---

## 3. Invariantes de Excitación (Drivers) y Redes

1. **Regla de Conductor Único (Single-Driver Invariant):**
   Toda señal (a excepción de buses con buffers tri-state explícitamente arbitrados) debe tener exactamente un único driver activo:
   $$\forall \text{net } n, \quad |\text{drivers}(n)| == 1$$
   La detección de 0 drivers produce advertencia/error de red flotante; más de 1 driver produce error fatal de contención (`ContentionError`).
2. **Separación de Dominios Secuenciales y Combinacionales:**
   - Un `REGISTER` solo puede ser actualizado en flancos de una señal de tipo `CLOCK`.
   - Las asignaciones `ASSIGN` son puramente combinacionales y libres de lazos de realimentación sin pasar por un registro.
