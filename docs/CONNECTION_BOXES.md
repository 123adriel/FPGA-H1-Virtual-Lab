# ARQUITECTURA DE CONNECTION BOXES: INTERFAZ CLB-CANAL

Proyecto: **FPGA-H1 Virtual Lab**  
Documento: `docs/CONNECTION_BOXES.md`  
Estado: Fase 2 Aprobada

---

## 1. Función y Ubicación

Las **Connection Boxes (CB)** interconectan los terminales lógicos del Bloque Lógico Configurable (CLB) con las pistas de los canales adyacentes:
- **`CB_X` (Horizontal):** Conecta las entradas y salidas del CLB a las pistas del canal horizontal adyacente (`CHANX`).
- **`CB_Y` (Vertical):** Conecta las entradas y salidas del CLB a las pistas del canal vertical adyacente (`CHANY`).

```
       +---------------------------------------------+
       |             Horizontal Channel              |
       |  Track 0   Track 1   Track 2 ... Track W-1  |
       +------+--------+---------+-----------+-------+
              |        |         |           |
        +-----+--------+---------+-----------+-----+
        |            CONNECTION BOX                |
        |  [ MUX Entrada ]       [ Driver Salida ] |
        +--------+-----------------------+---------+
                 |                       ^
                 v                       |
           CLB Input Pin           CLB Output Pin
```

---

## 2. Flexibilidad de Conexión: $F_{c,in}$ y $F_{c,out}$

Para evitar un número excesivo de transistores de paso que arruinarían la capacitancia y el área del silicio, se define la conectividad fraccional:

1. **Flexibilidad de Entrada ($F_{c,in} = 0.5$):**
   - Cada pin de entrada $I_{pin}$ del CLB puede conectarse al $50\%$ de las pistas del canal mediante un multiplexor de selección.
   - Para un ancho $W = 8$, cada entrada tiene acceso a 4 pistas alternadas:
     $$\text{Tracks}(I_{pin}) = \{(I_{pin} + k) \pmod W \mid k \in [0, \lfloor F_{c,in} \cdot W \rfloor - 1]\}$$
   - El multiplexor garantiza físicamente que a lo sumo **una única pista** sea seleccionada a la vez.

2. **Flexibilidad de Salida ($F_{c,out} = 0.5$):**
   - Cada pin de salida $Y_{pin}$ del CLB puede excitar el $50\%$ de las pistas del canal a través de llaves de tres estados (*tri-state drivers*).
   - Para evitar cortocircuitos eléctricos, la activación de un driver sobre una pista bloquea el acceso de cualquier otro driver simultáneo.

---

## 3. Modelo de Protección Anti-Cortocircuito (Multi-Driver Prevention)

En `ConnectionBox`, la asignación de salida verifica el estado del registro `track_driver`:
```python
if current_driver is not None and current_driver != pin_idx:
    raise RuntimeError(f"Short-circuit conflict: Track already driven by pin {current_driver}")
```
Esta verificación previene tanto errores de síntesis en el ruteador como inyecciones ilegales en bitstreams binarios.
