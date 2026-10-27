# DIAGRAMA DE CICLO DE VIDA DE UNA CARRERA
**Caso:** La Gran Liga de Apuestas de Medianos EIA  
**Organización:** Salchipapa Maker Racing S.A.S.  
**Artefacto:** `P1-ART-009D`  
**Uso:** Apoyo visual de la presentación (Slide 04) y del documento técnico. Fuente complementaria de `01_requisitos_y_negocio.md` (P1-1.2).

---

```mermaid
stateDiagram-v2
    direction LR
    [*] --> PROGRAMADA : Creación y programación

    PROGRAMADA --> ABIERTA : Apertura de ventana de apuestas
    ABIERTA --> CERRADA : Hora de inicio (reloj del servidor)
    CERRADA --> EN_CURSO : Bandera de salida
    EN_CURSO --> FINALIZADA : Cruzar la meta
    FINALIZADA --> LIQUIDADA : Resultado oficial + liquidación de premios
    LIQUIDADA --> [*]

    PROGRAMADA --> CANCELADA : Cancelación (+ reembolso 100 %)
    ABIERTA --> CANCELADA : Cancelación (+ reembolso 100 %)
    CERRADA --> CANCELADA : Cancelación (+ reembolso 100 %)
    EN_CURSO --> CANCELADA : Cancelación (+ reembolso 100 %)
    CANCELADA --> [*]

    note right of ABIERTA
        Ventana con cuotas estimadas.
        El cierre NO depende de una
        orden manual del operador.
    end note
    note right of CERRADA
        Inmutable: ninguna apuesta
        se admite con
        CLOCK_TIMESTAMP() >= start_time.
    end note
    note left of LIQUIDADA
        Sin ganadores: 100 % devuelto,
        motivo SIN_APUESTAS_GANADORAS,
        sin pasar por CANCELADA.
    end note
```

### Reglas representadas (Fuente: `01_requisitos_y_negocio.md`, PDF pág. 3):
- Ciclo formal: `PROGRAMADA → ABIERTA → CERRADA → EN_CURSO → FINALIZADA → LIQUIDADA`.
- `CANCELADA` es alcanzable desde cualquier estado anterior a `FINALIZADA`, con devolución íntegra del 100 %.
- La cancelación es un incidente operativo; la ausencia de ganadores es un desenlace deportivo válido (la carrera llega a `LIQUIDADA`).
