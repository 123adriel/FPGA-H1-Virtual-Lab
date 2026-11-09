# FORMATO DE CONFIGURACIÓN BINARIO: BITSTREAM H1BS

Proyecto: **FPGA-H1 Virtual Lab**  
Documento: `CONFIGURATION_FORMAT.md`  
Estado: Fase 0 / Fase 1

---

## 1. Estructura General del Archivo Bitstream (.h1b)

El bitstream de FPGA-H1 adopta un formato binario estructurado en tramas (*frame-based*), transportable, versionado e independiente del sustrato físico:

```
+-------------------------------------------------------------------+
| MAGIC HEADER (4 bytes: 'H', '1', 'B', 'S')                        |
+-------------------------------------------------------------------+
| VERSION (1 byte) | ARCH_FAMILY (2 bytes) | FLAGS (1 byte)         |
+-------------------------------------------------------------------+
| METADATA_LENGTH (2 bytes)                                         |
+-------------------------------------------------------------------+
| METADATA PAYLOAD (JSON UTF-8, variable)                           |
+-------------------------------------------------------------------+
| FRAME 0 (Type, Target, Length, Payload)                           |
+-------------------------------------------------------------------+
| FRAME 1 (Type, Target, Length, Payload)                           |
+-------------------------------------------------------------------+
| ...                                                               |
+-------------------------------------------------------------------+
| FRAME N (Type = 0xFF: END_OF_STREAM)                              |
+-------------------------------------------------------------------+
| CRC32 (4 bytes, Little Endian, IEEE 802.3)                        |
+-------------------------------------------------------------------+
```

---

## 2. Definición de Campos del Encabezado

| Campo | Offset | Tamaño | Tipo | Descripción |
|---|---|---|---|---|
| `Magic` | 0x00 | 4 bytes | ASCII | Cadena fija `0x48 0x31 0x42 0x53` (`"H1BS"`). |
| `Version` | 0x04 | 1 byte | uint8 | Versión de la especificación (Actual: `0x01`). |
| `ArchFamily` | 0x05 | 2 bytes | uint16 | Identificador de modelo: `0x0004` (4 LUT), `0x0010` (16 LUT), `0x0040` (64 LUT), `0x0100` (256 LUT), `0x0400` (1024 LUT), `0x1000` (4096 LUT), `0x21C0` (8640 LUT). |
| `Flags` | 0x07 | 1 byte | bitmask | `b0`: Compresión RLE activa; `b1`: Encriptación mock; `b2..b7`: Reservados. |
| `MetadataLen`| 0x08 | 2 bytes | uint16 | Tamaño en bytes del bloque de metadatos JSON. |
| `Metadata` | 0x0A | Variable | UTF-8 | Diccionario con nombre del diseño, fecha, autor, hash del fuente H1L. |

---

## 3. Catálogo de Tramas de Configuración (Frames)

Cada trama comienza con un prefijo de 4 bytes:
`[FrameType: 1 byte] [TargetID: 2 bytes] [PayloadLen: 1 byte] [Payload: N bytes]`

### 3.1 Trama Tipo 0x01 — Configuración LUT4 / BLE
- `TargetID`: Índice global del BLE (`0` a `N_LUTS - 1`).
- `PayloadLen`: 4 bytes.
- `Payload`:
  - Bytes 0-1: Máscara booleana de 16 bits de la LUT4 (`C_int`, Little Endian).
  - Byte 2: Flags de configuración BLE:
    - Bit 0: `BYPASS_FF` (1 = Salida combinacional directa; 0 = Salida registrada por DFF).
    - Bit 1: `CARRY_ENABLE` (1 = Activa multiplexor de acarreo rápido).
    - Bit 2: `INVERT_CLK` (1 = Disparo en flanco descendente).
  - Byte 3: Reservado / Alineación.

### 3.2 Trama Tipo 0x02 — Configuración Secuencial DFF
- `TargetID`: Índice global del BLE/DFF.
- `PayloadLen`: 2 bytes.
- `Payload`:
  - Byte 0: `INIT_VALUE` (0 o 1) y `RESET_MODE` (0 = Asíncrono, 1 = Síncrono).
  - Byte 1: `ENABLE_SENSITIVITY` (0 = Activo en alto, 1 = Activo en bajo).

### 3.3 Trama Tipo 0x03 — Configuración Switch Box (SB)
- `TargetID`: Identificador de coordenada `(X << 8) | Y`.
- `PayloadLen`: Variable dependiente del ancho de canal $W$ (Típicamente 4 a 16 bytes).
- `Payload`: Matriz de bits que activa los interruptores de paso (Wilton Cross-points) entre pistas $N, S, E, W$.

### 3.4 Trama Tipo 0x04 — Configuración Connection Box (CB)
- `TargetID`: Identificador de CLB / canal.
- `PayloadLen`: Selectores de multiplexores para conectar pines de entrada/salida a pistas de canal.

### 3.5 Trama Tipo 0x05 — Bloque de Entrada / Salida (IOB)
- `TargetID`: Índice de pin I/O físico.
- `PayloadLen`: 2 bytes (Dirección: Entrada, Salida, Bidireccional; Pull-up; Pull-down; Slew rate).

### 3.6 Trama Tipo 0xFF — Fin de Flujo (End of Stream)
- Señaliza la culminación de la secuencia de configuración antes del bloque de integridad.

---

## 4. Integridad y Verificación (CRC-32)

Los últimos 4 bytes del archivo contienen el valor de redundancia cíclica calculado sobre la totalidad del flujo desde el offset `0x00` hasta el final del payload de la trama `0xFF`:
- Polinomio generador: `0xEDB88320` (Estándar IEEE 802.3 Ethernet / ZIP).
- Valor inicial: `0xFFFFFFFF`.
- XOR de salida: `0xFFFFFFFF`.

Si el bitstream presenta corrupción en disco o transmisión, el cargador rechaza el bitstream y aborta la activación lógica, previniendo estados indeterminados o cortocircuitos lógicos en la matriz de ruteo.
