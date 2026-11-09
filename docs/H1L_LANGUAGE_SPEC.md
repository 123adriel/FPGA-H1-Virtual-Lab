# ESPECIFICACIÓN DEL LENGUAJE H1L (HARDWARE 1 LANGUAGE)

Proyecto: **FPGA-H1 Virtual Lab**  
Documento: `docs/H1L_LANGUAGE_SPEC.md`  
Estado: Fase 3

---

## 1. Misión y Filosofía de Diseño

**H1L** es un lenguaje de descripción de circuitos diseñado específicamente para la arquitectura FPGA-H1.

A diferencia de los lenguajes de software imperativo (como C o Python), H1L no describe instrucciones secuenciales para un procesador. Describe **topología de silicio, funciones booleanas concurrentes y almacenamiento secuencial en registros**, compilándose directamente hacia celdas LUT4, flip-flops D y matrices de conmutación.

---

## 2. Estructura de un Archivo H1L

Un archivo H1L contiene una definición principal `DEVICE` y opcionalmente submódulos jerárquicos reutilizables `MODULE`:

```h1l
MODULE HALF_ADDER
    INPUT A, B
    OUTPUT SUM, COUT
    ASSIGN SUM = A ^ B
    ASSIGN COUT = A & B
END

DEVICE ADDER4
    INPUT A[4], B[4]
    OUTPUT SUM[4], COUT
    
    # Submódulos o expresiones directas
    ASSIGN SUM = A + B
END
```

---

## 3. Primitivas del Lenguaje

### 3.1 Declaración de Puertos y Señales
- `INPUT A[4], B[4]`: Puertos de entrada primaria del chip.
- `OUTPUT Y[4], ZERO, CARRY`: Puertos de salida hacia pads externos.
- `WIRE TMP[4]`: Conductores internos para interconexión combinacional.
- `CLOCK CLK`: Señal de sincronización de flanco de subida.
- `RESET RST`: Señal de inicialización de flip-flops.

### 3.2 Registros Secuenciales (`REGISTER`)
Modelan D-Flip-Flops físicos dentro de los Basic Logic Elements (BLE):
```h1l
REGISTER COUNTER[4] <= COUNTER + 1 CLOCK CLK RESET RST
REGISTER Q[8] <= DATA_IN CLOCK CLK ENABLE WRITE_EN
```

### 3.3 Asignaciones Combinacionales (`ASSIGN`)
Sintetizan árboles booleanos hacia celdas Look-Up Table (LUT4):
```h1l
ASSIGN RESULT = (OP == 0) ? (A + B) :
                (OP == 1) ? (A - B) :
                (OP == 2) ? (A & B) : (A | B)
```

### 3.4 Primitiva de Bajo Nivel: Celda LUT Directa (`LUT`)
Permite mapear explícitamente cualquier máscara hexadecimal de 16 bits:
```h1l
LUT L0(A, B, C, D) = 0x6996
```

### 3.5 Instanciación de Submódulos (`INSTANCE`)
Permite reutilizar bloques jerárquicos con mapeo explícito de puertos:
```h1l
INSTANCE U0 OF HALF_ADDER ( A => A[0], B => B[0], SUM => S[0], COUT => C0 )
```
