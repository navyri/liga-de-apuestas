<!-- BANNER:INICIO (bloque estetico; omitido en el PDF consolidado) -->
<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&height=170&color=6B0F1A&text=CICLO%20DE%20VIDA%20DE%20UNA%20CARRERA%20%28FSM%29&fontColor=F4ECE4&fontSize=44&fontAlignY=34&desc=PROGRAMADA%2C%20ABIERTA%2C%20CERRADA%2C%20EN_CURSO%2C%20FINALIZADA%2C%20LIQUIDADA%20y%20CANCELADA&descColor=E8B4B8&descAlignY=60"
       alt="Banner: CICLO DE VIDA DE UNA CARRERA (FSM)"/>
</p>

<p align="center">
  <img src="https://64.media.tumblr.com/3254f08405664a04d3c5a65f765eb8c9/61bf168659dda322-50/s2048x3072/36c765a65bc72096e27e85823017367c0b9b48b2.pnj" alt="Ilustración conceptual de estrategia y competición en la academia" width="520"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Formato-Mermaid-540B13?style=flat-square&logoColor=white" alt="Formato: Mermaid"/>
  <img src="https://img.shields.io/badge/Estados-7-6B0F1A?style=flat-square&logoColor=white" alt="Estados: 7"/>
  <img src="https://img.shields.io/badge/Universidad-EIA-8B1E2D?style=flat-square&logoColor=white" alt="Universidad: EIA"/>
</p>


<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=rect&height=6&color=6B0F1A"
       alt=""/>
</p>

<!-- BANNER:FIN -->

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
