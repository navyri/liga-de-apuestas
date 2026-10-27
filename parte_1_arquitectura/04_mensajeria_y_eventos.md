# ETAPA P1-4: MENSAJERÍA Y COMUNICACIÓN ASÍNCRONA
**Caso:** La Gran Liga de Apuestas de Medianos EIA  
**Organización:** Salchipapa Maker Racing S.A.S.  
**Artefacto:** `P1-ART-005`  
**Versión:** `v1.0`  
**Estado:** `[x]` Consolidado (Elección de Apache Kafka aprobada por el usuario en P1-DEC-002; diseño de eventos, topología y outbox verificado por revisión autónoma)  

---

## P1-4.1 Y P1-4.2: DECISIÓN 5 — ELECCIÓN DE LA TECNOLOGÍA DE MENSAJERÍA

### 1. Dirección Aprobada: Apache Kafka como Broker Único del Sistema
Se adopta formalmente **Apache Kafka** como plataforma exclusiva de mensajería y streaming de eventos para la Liga de Apuestas de Medianos.

### 2. Justificación Técnica y Comparativa Frente al Dominio

#### A. Ajuste al Patrón de Múltiples Consumidores Independientes y Eventos Retenidos
- **Naturaleza del Dominio:** En la plataforma, un único evento de negocio (por ejemplo, la admisión de una apuesta o la publicación del resultado oficial) interesa concurrentemente a múltiples subsistemas:
  - Motor de estimación de cuotas dinámicas en vivo.
  - Servicio de auditoría y control de anomalías.
  - Pipeline de estadísticas y analítica para reportes diarios y venta premium.
  - Servicio de notificaciones multicanal hacia los apostadores.
- **Ventaja de Diseño de Kafka:** En Kafka, el almacenamiento se estructura como un log distribuido de confirmación en disco (*commit log* append-only). Múltiples grupos de consumidores (`Consumer Groups`) leen concurrentemente la misma partición a su propio ritmo sin necesidad de duplicar el mensaje físicamente en almacenamiento ni generar colas aisladas por cada suscriptor. Cada grupo mantiene su propio cursor o puntero de lectura (`offset`).

#### B. Justificación del Descarte de Alternativas
1. **Descarte de RabbitMQ como broker principal del diseño:**
   - Si bien RabbitMQ soporta patrones avanzados de enrutamiento AMQP, colas tradicionales y extensiones como *RabbitMQ Streams* (que ofrecen semánticas de log secuencial), el diseño del sistema encaja de forma más directa y estándar en el modelo de tópicos particionados y grupos de consumidores de Kafka, donde los eventos retenidos por ventana temporal permiten desacoplar de forma nativa a consumidores con velocidades de procesamiento dispares (ej. notificaciones lentas vs. cálculo ágil de cuotas).
   - *(Aclaración de descarte):* No se descarta a RabbitMQ por una supuesta incapacidad técnica ni por limitaciones genéricas de throughput, sino porque la semántica de publicación basada en log distribuido con particionamiento explícito por clave de negocio (`race_id`, `user_id`) satisface de manera más compacta y uniforme todos los flujos asíncronos del caso de estudio sin requerir tecnologías heterogéneas.
2. **Descarte de la Solución Dual (RabbitMQ + Kafka combinados):**
   - El PDF señala taxativamente (pág. 11, 15): *"No existe obligación de utilizar ambos... Si utilizan ambos, deberán justificar por qué mantener dos tecnologías diferentes representa una ventaja suficiente para asumir la complejidad adicional"*.
   - Para el alcance de la Liga de Medianos, **no se ha demostrado una ventaja operativa suficiente que compense la complejidad de aprovisionar, monitorizar, asegurar y operar dos plataformas de mensajería distintas**. Una sola tecnología bien dimensionada cubre tanto el streaming de eventos como la distribución de tareas de liquidación.

#### C. Matización Rigurosa de Rendimiento y Rendimiento Asíncrono
- **Distinción entre Apuestas/s y Eventos/s:**
  - El pico del negocio es de **10.000 apuestas por segundo** en la capa transaccional HTTP/BD durante 30 segundos.
  - Cada apuesta aceptada produce un evento principal de dominio (`BetPlaced`). No obstante, si se emitieran eventos secundarios de auditoría o cuotas sin consolidación, la tasa de eventos podría multiplicarse. El diseño adopta **1 evento canónico por apuesta admitida**, resultando en una tasa asíncrona pico de ~10.000 eventos/s hacia Kafka.
- **Supuestos de Dimensionamiento:**
  - Tamaño promedio de evento `BetPlaced` serializado en JSON/Avro: $\sim 500\text{ bytes}$.
  - Tasa de datos en pico: $10.000\text{ ev/s} \times 500\text{ bytes} \approx 5\text{ MB/s}$ de rendimiento de escritura sostenido durante 30 segundos ($\approx 150\text{ MB}$ totales por ráfaga), lo cual es absorbible por un clúster moderado de Kafka con particiones adecuadas sin representar una carga insalvable.
- **Compromiso entre Paralelismo y Orden por Partición:**
  - En Kafka, el orden estricto de entrega solo se garantiza **dentro de una misma partición**.
  - Aumentar el número de particiones eleva el paralelismo de consumo, pero distribuye los eventos. Para preservar el orden causal donde es obligatorio (ej. ciclo de una carrera), se utiliza la clave de partición adecuada.

#### D. Delimitación Estricta entre Retención Operativa en Kafka y Auditoría Inalterable a 5 Años
- **Retención Operativa en Kafka:** Kafka se configura con una retención temporal acotada (ej. **7 días**). Su función es absorber ráfagas, tolerar caídas transitorias de consumidores y permitir reprocesamiento reciente (*replay* operativo). **Kafka no es el repositorio definitivo de auditoría inalterable a 5 años**.
- **Auditoría Legal y Forense a 5 Años:** Se garantiza mediante la ingesta continua de eventos desde Kafka hacia una base de datos o almacenamiento inmutable de auditoría (esquema append-only con controles de integridad criptográfica y permisos exclusivos de solo lectura para el auditor).
- **Protección contra Efectos Duplicados en Reprocesamiento (*Replay*):**
  - Si un consumidor retrocede su offset para reprocesar eventos, **jamás debe re-acreditar premios ni emitir reembolsos duplicados**.
  - Los consumidores de billetera y liquidación operan con **idempotencia estricta en la base de datos de destino** (ej. tablas contables con restricciones `UNIQUE (race_id, user_id, transaction_type)`), ignorando transacciones previamente ejecutadas.

---

## P1-4.3: DEFINICIÓN CANÓNICA DE EVENTOS EN UN ÚNICO IDIOMA

Para dar cumplimiento formal al requisito del PDF (pág. 10, 14: *"Usen un único idioma para nombrarlos"*), se adopta **Español formal en formato PascalCase** en toda la plataforma:

1. `ApuestaAceptada`: Emitido cuando una apuesta es validada, descontada de la billetera y confirmada en la base de datos.
2. `CarreraIniciada`: Emitido cuando la carrera arranca oficialmente en pista y cesa irrevocablemente el corte.
3. `CarreraFinalizada`: Emitido cuando el último mediano cruza la meta y la carrera concluye en pista.
4. `ResultadoOficialPublicado`: Emitido cuando el Operador de Carrera registra y sella la foto de llegada y el ganador oficial.
5. `LotePremiosCalculado`: Emitido por el worker de liquidación detallando las apuestas premiadas por bloque.
6. `PremioAcreditado`: Emitido cada vez que se abona exitosamente la recompensa en la billetera de un apostador ganador.
7. `CarreraCancelada`: Emitido si la carrera se suspende antes de finalizar, activando el proceso masivo de devoluciones.
8. `DevolucionAcreditada`: Emitido al reintegrarse el 100% de los fondos de una apuesta tras cancelación.

---

## P1-4.4: TABLA DE PRODUCTORES, CONSUMIDORES, TOPOLOGÍA Y CLAVES (PDF pág. 14)

Conforme a la estructura obligatoria de la Decisión 4 del PDF, se define el catálogo de eventos asíncronos:

| Evento | Productor | Tecnología | Consumidor(es) | Clave de Partición (`Partition Key`) | Propósito / Efecto del Consumo |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`ApuestaAceptada`** | Núcleo Modular (`core-api` vía Outbox) | Apache Kafka (Topic: `apuestas.aceptadas`) | 1. `CalculadorCuotas`<br>2. `ServicioAnalitica`<br>3. `ServicioAuditoria`<br>4. `ServicioNotificaciones` | `race_id` | Mantiene el orden estricto de llegada de apuestas por carrera para el cálculo progresivo de la cuota estimada, alimentación de métricas y alerta al apostador. |
| **`CarreraIniciada`** | Núcleo Modular (`RacesModule` vía Outbox) | Apache Kafka (Topic: `carreras.eventos`) | 1. `ServicioNotificaciones`<br>2. `ServicioAnalitica` | `race_id` | Notifica a usuarios en vivo y actualiza el estado de la transmisión en tiempo real. |
| **`CarreraFinalizada`** | Núcleo Modular (`RacesModule` vía Outbox) | Apache Kafka (Topic: `carreras.eventos`) | 1. `ServicioNotificaciones`<br>2. `ConsolaOperador` | `race_id` | Alerta al operador y usuarios del fin de la carrera en pista a la espera de resultados oficiales. |
| **`ResultadoOficialPublicado`**| Núcleo Modular (`RacesModule` vía Outbox) | Apache Kafka (Topic: `carreras.resultados`) | 1. `WorkerLiquidacion`<br>2. `ServicioNotificaciones`<br>3. `ServicioAuditoria` | `race_id` | **Disparador de liquidación:** El worker toma el resultado oficial y arranca el cálculo proporcional del 90% de la bolsa. |
| **`LoteLiquidacionGenerado`** | `WorkerLiquidacion` | Apache Kafka (Topic: `liquidacion.lotes`) | `WorkersDispersadoresSaldo` (Pool de hilos en `core-api` / worker) | `user_id` | **Distribución de carga:** Divide 1M de apuestas en lotes particionados por usuario para evitar contención de balance en BD. |
| **`PremioAcreditado`** | Worker / Módulo Billetera | Apache Kafka (Topic: `billetera.movimientos`) | 1. `ServicioNotificaciones`<br>2. `ServicioAuditoria`<br>3. `ServicioAnalitica` | `user_id` | Notifica al usuario ganador ("¡Ganaste X EIA Coins!") y registra el movimiento contable en auditoría. |
| **`CarreraCancelada`** | Núcleo Modular (`RacesModule` vía Outbox) | Apache Kafka (Topic: `carreras.eventos`) | 1. `WorkerLiquidacion` (Modo Reembolso)<br>2. `ServicioNotificaciones`<br>3. `ServicioAuditoria` | `race_id` | Dispara el proceso de reembolso del 100% de los montos a cada apostador participante. |
| **`DevolucionAcreditada`** | Worker / Módulo Billetera | Apache Kafka (Topic: `billetera.movimientos`) | 1. `ServicioNotificaciones`<br>2. `ServicioAuditoria` | `user_id` | Notifica al apostador el reintegro de sus EIA Coins por cancelación de carrera. |

---

## P1-4.5: ESQUEMA Y CONTENIDO MÍNIMO DE LOS EVENTOS

Todos los eventos de la plataforma comparten una estructura base canónica con versionado semántico para garantizar evolución compatible de esquemas:

```json
{
  "eventId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "eventType": "ApuestaAceptada",
  "schemaVersion": "1.0",
  "timestamp": "2026-10-27T18:30:00.125Z",
  "producer": "core-api/instance-03",
  "correlationId": "corr-89102-uuid",
  "data": {
    "betId": "bet-994821",
    "raceId": "race-copa-final-2026",
    "userId": "usr-48192",
    "racerId": "racer-frodito-turbo",
    "amount": 500,
    "userBalanceAfter": 1500,
    "idempotencyKey": "idem-client-8812739"
  }
}
```

### Campos Mínimos Obligatorios:
- `eventId`: Identificador único global (UUIDv4) del evento para deduplicación en consumidores.
- `eventType`: Nombre canónico del evento en PascalCase.
- `schemaVersion`: Versión del contrato de datos para soportar evolución.
- `timestamp`: Marca temporal en UTC generada por el servidor emisor.
- `producer`: Identificador del componente u origen del mensaje.
- `data`: Carga útil de negocio específica con identificadores de entidades, montos y claves de trazabilidad.

---

## P1-4.6: TOPOLOGÍA DE TÓPICOS Y GRUPOS DE CONSUMIDORES

```text
                                  APACHE KAFKA CLUSTER
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │                                                                                        │
 │  Topic: apuestas.aceptadas (Particionado por race_id)                                  │
 │  [ P0 ][ P1 ][ P2 ][ P3 ][ P4 ][ P5 ][ P6 ][ P7 ]                                      │
 │   │      │      │                                                                      │
 └───┼──────┼──────┼──────────────────────────────────────────────────────────────────────┘
     │      │      │
     ├──────┴──────┴───────► Consumer Group: "cuotas-dinamicas-workers" (Offset propio)
     ├─────────────────────► Consumer Group: "notificaciones-apuestas" (Offset propio)
     ├─────────────────────► Consumer Group: "analitica-ingesta-diaria" (Offset propio)
     └─────────────────────► Consumer Group: "auditoria-control-fraude" (Offset propio)

 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │  Topic: liquidacion.lotes (Particionado por user_id)                                   │
 │  [ P0 ][ P1 ][ P2 ][ P3 ][ P4 ][ P5 ][ P6 ][ P7 ]                                      │
 │   │                                                                                    │
 └───┼────────────────────────────────────────────────────────────────────────────────────┘
     └─────────────────────► Consumer Group: "dispersores-premios-billetera"
```

### Distribución del Trabajo de Liquidación Masiva sin RabbitMQ
Para procesar más de 1.000.000 de apuestas en menos de 15 minutos sin generar una única tarea gigantesca monolítica y sin introducir un segundo broker:
1. **Fase 1 (Cálculo Agregado en Worker):** Al recibir `ResultadoOficialPublicado`, el `WorkerLiquidacion` ejecuta una consulta agregada sobre la bolsa de la carrera en la BD operativa, determinando la masa ganadora $T_w$, la bolsa neta $B_{\text{neta}}$ y la cuota unitaria final $Q_w$. Esta fase toma menos de 10 segundos.
2. **Fase 2 (Generación de Lotes Particionados):** El worker segmenta las apuestas ganadoras en **lotes homogéneos de 1.000 apuestas** (`LoteLiquidacionGenerado`).
3. **Fase 3 (Dispersión Paralela por Tópico Particionado por `user_id`):** Los lotes se publican en el tópico `liquidacion.lotes` utilizando el identificador del usuario como clave de partición (`user_id`).
4. **Fase 4 (Consumo Concurrente):** Un grupo escalado de workers acreditadores consume los lotes en paralelo. Dado que los eventos están particionados por usuario, se evitan interbloqueos (*deadlocks*) en la tabla de billeteras, logrando acreditar las apuestas ganadoras de forma fluida a una tasa de $\sim 1.500\text{ a } 2.500\text{ acreditaciones/s}$, completando el millón de jugadas en un rango de 7 a 11 minutos (muy por debajo del límite de 15 minutos).

---

## P1-4.7: ESTRATEGIA DE REINTENTOS, CONFIRMACIONES, MENSAJES DUPLICADOS Y FALLIDOS

1. **Garantía de Entrega y Tolerancia a Duplicados:**  
   Kafka opera bajo la semántica de entrega **al menos una vez** (*at-least-once*). En consecuencia, **los consumidores deben ser estrictamente idempotentes**. Todo consumidor registra en su almacén local el `eventId` procesado; si un mensaje se reentrega por caída de red, el consumidor detecta el `eventId` y emite confirmación de offset sin reejecutar la lógica.
2. **Tópicos de Reintento y Carta Muerta (Dead Letter Topic - DLT):**  
   - Si un consumidor falla por error transitorio (ej. micro-corte hacia el proveedor push de notificaciones), el mensaje se remite a un tópico de reintento (`notificaciones.retry-5s`) con cabecera de contador de intentos.
   - Si tras 3 reintentos el fallo persiste (ej. dirección de correo corrupta), se desvía al tópico de descarte (`notificaciones.dlt`) para inspección operativa sin detener el consumo del flujo principal.

---

## P1-4.8: PUBLICACIÓN CONFIABLE: PATRÓN TRANSACTIONAL OUTBOX

Para erradicar la inconsistencia clásica de los sistemas distribuidos (donde se guarda en la base de datos pero se cae el broker antes de publicar, o viceversa), se implementa el patrón **Transactional Outbox**:

```text
 ┌─────────────────────────────────────────────────────────────┐
 │                TRANSACCIÓN LOCAL ACID EN BD                 │
 │                                                             │
 │  1. UPDATE wallets SET balance = balance - 500              │
 │  2. INSERT INTO bets (id, user_id, amount, ...)             │
 │  3. INSERT INTO outbox_events (id, topic, payload, status)  │
 │                                                             │
 │  COMMIT ATÓMICO (Garantiza persistencia conjunta)           │
 └──────────────────────────────┬──────────────────────────────┘
                                │
                                ▼ CDC / Polling Publisher
                 ┌─────────────────────────────┐
                 │    OUTBOX RELAY PROCESS     │
                 │ - Lee eventos 'PENDING'     │
                 │ - Publica en Apache Kafka   │
                 │ - Marca eventos 'PUBLISHED' │
                 └──────────────┬──────────────┘
                                │
                                ▼
                         [ APACHE KAFKA ]
```

- **Garantía de Persistencia:** El evento `ApuestaAceptada` se escribe en la tabla `outbox_events` dentro de la **misma transacción local** que debita el saldo y guarda la apuesta.
- **Relay Desacoplado:** Un proceso emisor (*Outbox Relay* mediante lectura de logs de transacción / CDC o polling de alta frecuencia) lee los registros pendientes y los despacha hacia Apache Kafka con confirmación del broker (`acks=all`).
- **Resiliencia:** Si Kafka experimenta una caída momentánea, las apuestas siguen siendo admitidas y cobradas normalmente en la base de datos; los eventos se acumulan de forma segura en la tabla outbox y se drenan automáticamente al recuperarse el broker.
