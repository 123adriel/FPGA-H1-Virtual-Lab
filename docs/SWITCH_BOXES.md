# ARQUITECTURA DE SWITCH BOXES: TOPOLOGÍA WILTON (Fs = 3)

Proyecto: **FPGA-H1 Virtual Lab**  
Documento: `docs/SWITCH_BOXES.md`  
Estado: Fase 2 Aprobada

---

## 1. Visión General y Topología

En una arquitectura FPGA Island-Style, las **Switch Boxes (SB)** se ubican en cada intersección ortogonal de canales horizontales (`CHANX`) y verticales (`CHANY`).

Para FPGA-H1 se seleccionó la topología **Wilton Switch Box** con flexibilidad de conmutación $F_s = 3$ (cada terminal se conecta exactamente a otros 3 terminales en diferentes direcciones).

A diferencia de la topología trivial o desconectada (*Subset Switch Box*), donde la pista $i$ solo puede conectarse a la pista $i$ al doblar (lo que causa fragmentación de redes y falta de acceso a terminales diagonales), la topología Wilton introduce una rotación modular al girar, lo que permite que una señal cambie de pista tras un giro:

```
                  NORTH [0..W-1]
                      | | | |
             +--------+-+-+-+--------+
             |                       |
WEST [0..W-1]--                     -- EAST [0..W-1]
             |      SWITCH BOX       |
             |    (Wilton Fs = 3)    |
             +--------+-+-+-+--------+
                      | | | |
                  SOUTH [0..W-1]
```

---

## 2. Ecuaciones Canónicas de Conexión

Sea $W$ el ancho del canal (número de pistas paralelas) y $t \in [0, W - 1]$ el índice de pista:

### 2.1 Conexiones Rectas (Straight)
- **Norte a Sur:**
  $$T(\text{NORTH}, t) \longleftrightarrow T(\text{SOUTH}, t)$$
- **Este a Oeste:**
  $$T(\text{EAST}, t) \longleftrightarrow T(\text{WEST}, t)$$

### 2.2 Conexiones en Giro (Turns con Desplazamiento Modular)
- **Norte a Oeste:**
  $$T(\text{NORTH}, t) \longleftrightarrow T(\text{WEST}, (t + 1) \pmod W)$$
- **Norte a Este:**
  $$T(\text{NORTH}, t) \longleftrightarrow T(\text{EAST}, (t + W - 1) \pmod W)$$
- **Sur a Oeste:**
  $$T(\text{SOUTH}, t) \longleftrightarrow T(\text{WEST}, (t + W - 1) \pmod W)$$
- **Sur a Este:**
  $$T(\text{SOUTH}, t) \longleftrightarrow T(\text{EAST}, (t + 1) \pmod W)$$

Cada una de estas 6 familias de conexiones está gobernada por un transistor de paso o puerta de transmisión programable mediante 1 bit de configuración SRAM en el bitstream.

---

## 3. Cantidad Total de Switches por Bloque

Para un ancho de canal $W$:
$$\text{Switches por SB} = 6 \cdot W$$

| Ancho de Canal $W$ | Switches Programables por SB | Representación Binaria en H1BS |
|---|---|---|
| $W = 4$ | $24$ interruptores | 3 bytes (empaquetado en uint32) |
| $W = 6$ | $36$ interruptores | 5 bytes (empaquetado en uint64) |
| $W = 8$ | $48$ interruptores | 6 bytes (empaquetado en uint64) |
| $W = 16$ | $96$ interruptores | 12 bytes |

---

## 4. Detección de Conflictos y Reglas Eléctricas

1. **Unicidad de Excitación:** En cualquier instante, un conductor físico sólo puede ser excitado por un único punto conductor.
2. **Detección de Cortocircuitos:** Si el enrutador o un bitstream corrupto intenta activar simultáneamente múltiples caminos que convergen dos drivers distintos sobre una misma pista, el motor de validación aborta la carga y reporta colisión de señal.
