# ARQUITECTURA DEL COMPILADOR H1L: MANUAL TÉCNICO

Proyecto: **FPGA-H1 Virtual Lab**  
Documento: `docs/H1L_COMPILER.md`  
Estado: Fase 3 Aprobada

---

## 1. Visión General del Pipeline de Compilación

El compilador **H1L** transforma código fuente de descripción de hardware en un FPGA-H1 completamente configurado, ubicado, enrutado y listo para simular:

```
+---------------+      +----------------+      +-------------------+
|  Código H1L   | ---> |  Lexer H1L     | ---> |  Parser EBNF      |
|  (.h1l)       |      |  (Token Stream)|      |  (Typed AST)      |
+---------------+      +----------------+      +-------------------+
                                                         |
                                                         v
+---------------+      +----------------+      +-------------------+
| CircuitEngine | <--- | Technology     | <--- | Elaborator        |
| (Simulación)  |      | Mapper (LUT4)  |      | (Hierarchy/Types) |
+---------------+      +----------------+      +-------------------+
        |                      |
        v                      v
+---------------+      +----------------+      +-------------------+
|  2D Placement | ---> |  Pathfinder    | ---> |  Bitstream H1BS   |
|  (Annealing)  |      |  Routing Grid  |      |  (.h1b con CRC32) |
+---------------+      +----------------+      +-------------------+
```

---

## 2. Etapas Internas del Compilador

### Etapa 1: Análisis Léxico (`compiler/lexer/`)
- Convierte el texto fuente en una secuencia de objetos `Token`.
- Rastrea línea y columna exactas en cada token.
- Omite comentarios de una línea (`#`, `//`) y multilínea (`/* ... */`).
- Reconoce números decimales, binarios (`0b...`) y hexadecimales (`0x...`).

### Etapa 2: Análisis Sintáctico (`compiler/parser/`)
- Implementa descenso recursivo guiado por la gramática formal EBNF ([`docs/H1L_GRAMMAR.ebnf`](file:///C:/Users/apalazzesi/Desktop/FPGA-H1-Virtual-Lab/docs/H1L_GRAMMAR.ebnf)).
- Expresiones con precedencia matemática estricta (Ternario `? :`, Bitwise `|`, `^`, `&`, Comparadores `==, !=, <, <=, >, >=`, Aritméticos `+, -`).
- Emite excepciones `ParserError` con contexto de línea y columna.

### Etapa 3: Elaboración Semántica y Sistema de Tipos (`compiler/elaborator/`)
- Resuelve la jerarquía de submódulos `MODULE`, aplanando nombres con prefijos (`u0.a`, `u0.sum`).
- Verifica la compatibilidad de anchos de buses de señal.
- Garantiza la regla de conductor único (*Single-Driver Invariant*).

### Etapa 4: Technology Mapping a LUT4 y DFF (`compiler/optimizer/`)
- Mapea cualquier expresión booleana de hasta 4 variables en **1 única celda LUT4** mediante la evaluación de su tabla de verdad de 16 minitérminos.
- Para expresiones con más de 4 variables, aplica recursivamente la **Descomposición de Shannon**:
  $$F(x_1, \dots, x_k) = \overline{x_1} \cdot F(0, x_2, \dots, x_k) + x_1 \cdot F(1, x_2, \dots, x_k)$$
  realizada físicamente mediante un árbol de LUT4s con multiplexores 2:1 (`mask 0xCACA`).

### Etapa 5: Empaquetado CLB, Placement y Routing
- Empaqueta las LUT4s y DFFs en celdas lógicas básicas BLE y CLBs de 4 celdas.
- Ejecuta ubicación espacial minimizando HPWL por recocido simulado.
- Enruta las señales con el motor **Pathfinder** con heurística $A^*$.

### Etapa 6: Generación de Bitstream Binario H1BS
- Codifica las tablas de verdad de las LUT4, registros y la matriz de conmutación de Switch Boxes y Connection Boxes en formato binario estructurado en tramas con suma de verificación **CRC-32**.
