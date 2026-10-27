# ETAPA P1-5: DATOS, PERSISTENCIA E IDEMPOTENCIA
**Caso:** La Gran Liga de Apuestas de Medianos EIA  
**Organización:** Salchipapa Maker Racing S.A.S.  
**Artefacto:** `P1-ART-006`  
**Versión:** `v0.1` (Borrador técnico para decisión)  
**Estado:** `[~]` Elaborado pendiente de consulta sobre políticas de negocio (redondeo y sin ganadores)  

---

## P1-5.1: ALMACENAMIENTO Y PROPIEDAD DE DATOS

Para cumplir con la Decisión 9 del PDF (pág. 16), se definen los tipos de bases de datos, su propiedad y sus fronteras de acceso:

1. **Base de Datos Operativa Transaccional (OLTP):**
   - **Tecnología recomendada:** Motor Relacional SQL (ej. PostgreSQL administrado).
   - **Propiedad:** Exclusiva del **Núcleo Modular Transaccional (`core-api`)**.
   - **Justificación:** Maneja el libro contable de billeteras, el catálogo de competidores, las carreras y las apuestas. Requiere soporte estricto de transacciones ACID, aislamiento serializable o *read committed* con bloqueos pesimistas a nivel de fila (`SELECT FOR UPDATE`), restricciones de clave foránea y claves únicas para garantizar que ningún saldo sea negativo.
   - **Esquema Interno:**
     - `schema_users`: Usuarios, credenciales cifradas y roles RBAC.
     - `schema_races`: Catálogo de medianos y carreras con estados y marcas temporales.
     - `schema_bets`: Apuestas admitidas con índices únicos de idempotencia.
     - `schema_wallets`: Saldos de EIA Coins y libro de movimientos contables (*ledger* append-only).
     - `schema_outbox`: Tabla transaccional de eventos pendientes de publicación en Kafka.
2. **Almacén Analítico e Histórico (OLAP):**
   - **Tecnología recomendada:** Almacén columnar / motor de analítica distribuida (ej. ClickHouse o servicio administrado tipo BigQuery/Snowflake).
   - **Propiedad:** Exclusiva del **Servicio de Analítica y Estadísticas (`analytics-service`)**.
   - **Justificación:** Optimizado para la ingesta masiva de millones de eventos diarios y agregaciones analíticas complejas (cálculo de tendencias, rendimiento histórico de medianos y reportes premium) sin consumir los IOPS ni el pool de conexiones de la base de datos transaccional.
3. **Almacén de Auditoría Inmutable:**
   - **Tecnología recomendada:** Esquema append-only en réplica aislada con políticas WORM (*Write Once, Read Many*) o almacenamiento en frío con sellado criptográfico.
   - **Propiedad:** Consumo exclusivo de solo lectura para el rol Auditor (`audit-service`).
   - **Retención:** Mínimo **5 años** conforme al requisito del PDF (pág. 9).

---

## P1-5.2: CONSISTENCIA FUERTE VS. CONSISTENCIA EVENTUAL

Se clasifican formalmente los datos de la plataforma según su exigencia de consistencia:

| Dominio de Datos | Modelo de Consistencia | Justificación Técnica | Mecanismo de Aplicación |
| :--- | :--- | :--- | :--- |
| **Saldo y Movimientos de Billetera** | **Consistencia Fuerte (ACID)** | Invariante de negocio: prohibición absoluta de doble gasto de EIA Coins y de saldo negativo. | Transacción local en BD con bloqueo pesimista a nivel de fila (`FOR UPDATE`). |
| **Admisión y Cierre de Apuestas** | **Consistencia Fuerte (ACID)** | Una apuesta no puede aceptarse después de la hora exacta de corte del servidor ni registrarse sin descontar el saldo. | Verificación atómica en la misma sentencia `INSERT ... WHERE NOW() < start_time`. |
| **Cuotas Estimadas en Vivo** | **Consistencia Eventual** | La cuota dinámica es una aproximación progresiva para informar al usuario mientras la carrera está abierta (PDF pág. 3). | Cálculo en streaming desacoplado mediante consumo asíncrono de eventos `ApuestaAceptada`. |
| **Notificaciones al Apostador** | **Consistencia Eventual** | El envío de correos o push puede demorarse segundos sin invalidar la confirmación transaccional ya emitida. | Consumo asíncrono desde Kafka con reintentos y tolerancia a caídas. |
| **Estadísticas y Analítica** | **Consistencia Eventual** | El PDF autoriza explícitamente retrasos de minutos para estadísticas generales y hasta un día para reportes premium (pág. 9). | Ingesta en micro-lotes hacia el almacén columnar OLAP. |

---

## P1-5.3: CONCURRENCIA Y PREVENCIÓN ABSOLUTA DE SALDO NEGATIVO

Bajo el escenario crítico en que un estudiante presiona cuatro veces "APOSTAR" o emite múltiples apuestas en paralelo desde varias pestañas, se previene el saldo negativo mediante tres niveles de defensa:

```sql
-- 1. Bloqueo exclusivo a nivel de fila sobre la billetera del usuario
SELECT balance FROM wallets WHERE user_id = :user_id FOR UPDATE;

-- 2. Validación en memoria de la transacción
-- IF balance < :amount THEN ROLLBACK AND RETURN 422_INSUFFICIENT_FUNDS;

-- 3. Actualización segura y restricción CHECK a nivel de motor de base de datos
UPDATE wallets 
SET balance = balance - :amount, 
    updated_at = NOW() 
WHERE user_id = :user_id;

-- Constraint de seguridad física en la definición de tabla:
-- ALTER TABLE wallets ADD CONSTRAINT chk_positive_balance CHECK (balance >= 0);
```

- **Explicación del Mecanismo:** La cláusula `FOR UPDATE` serializa el acceso a la fila de saldo de ese usuario específico. Las solicitudes concurrentes del mismo usuario se encolan a nivel de base de datos y se evalúan secuencialmente. Si la primera apuesta agota el saldo, las tres siguientes leen el balance actualizado y son rechazadas atómicamente con error de saldo insuficiente, disparando `ROLLBACK`. La restricción física `CHECK (balance >= 0)` garantiza a nivel de motor que jamás se confirme un valor negativo.

---

## P1-5.4: ESTRATEGIA DE IDEMPOTENCIA EN AL MENOS TRES OPERACIONES CRÍTICAS (PDF pág. 15)

Conforme a la Decisión 6 del PDF, se diseñan los mecanismos para garantizar idempotencia ($f(f(x)) = f(x)$):

```text
 ┌─────────────────────────────────────────────────────────────────────────────────────────┐
 │                   MECANISMOS DE IDEMPOTENCIA EN TRES OPERACIONES CRÍTICAS                │
 └────────────────────────────────────────────┬────────────────────────────────────────────┘
         ┌────────────────────────────────────┼────────────────────────────────────┐
         ▼                                    ▼                                    ▼
 [1. CREACIÓN DE APUESTA]            [2. PAGO DE PREMIO]               [3. EVENTO KAFKA REPROCESADO]
 - Header: Idempotency-Key           - Clave natural compuesta:        - Deduplicación por eventId
 - Restricción UNIQUE en BD:           UNIQUE(race_id, user_id,          - Tabla processed_events:
   UNIQUE(user_id, idemp_key)          transaction_type)                 INSERT ... ON CONFLICT DO NOTHING
 - Retorna respuesta cacheada        - Reintentos no generan           - Evita duplicar efectos
   sin cobrar dos veces                segundo abono contable            al retroceder offsets
```

1. **Operación 1: Creación y Cobro de una Apuesta (`POST /api/v1/bets`):**
   - *Riesgo:* El usuario pulsa cuatro veces consecutivas el botón de apostar ante lentitud de red.
   - *Mecanismo:* El cliente genera una cabecera HTTP obligatoria `Idempotency-Key: <UUIDv4>`. En la base de datos existe la restricción `UNIQUE (user_id, idempotency_key)` en la tabla `bets_idempotency`. Si entra la segunda, tercera o cuarta petición con la misma clave, la inserción colisiona atómicamente por clave duplicada; el servidor intercepta la colisión, lee la respuesta almacenada de la primera transacción confirmada y la retorna de inmediato (`HTTP 200 OK`) sin tocar el balance ni registrar una nueva apuesta.
2. **Operación 2: Acreditación de Premios por Liquidación:**
   - *Riesgo:* El worker de liquidación sufre un fallo transitorio tras pagar un premio y Kafka le reentrega el mensaje de lote, o un operador ejecuta un reintento manual de liquidación.
   - *Mecanismo:* El abono contable utiliza una clave de unicidad natural: `UNIQUE (race_id, user_id, 'PRIZE_PAYOUT')` en la tabla de transacciones de billetera (`wallet_transactions`). Si se intenta re-acreditar el premio de la misma carrera al mismo usuario, la base de datos rechaza la inserción por violación de unicidad (`ON CONFLICT DO NOTHING`), evitando que un mediano reciba o distribuya premios duplicados.
3. **Operación 3: Consumo de Eventos de Mensajería (Replay / At-Least-Once):**
   - *Riesgo:* Kafka reentrega el evento `ApuestaAceptada` tras un rebalanceo del grupo de consumidores, o un auditor retrocede el offset del tópico para inspección.
   - *Mecanismo:* Cada consumidor mantiene una tabla local `processed_events (event_id VARCHAR PRIMARY KEY, processed_at TIMESTAMP)`. Antes de procesar cualquier mensaje, se ejecuta:
     ```sql
     INSERT INTO processed_events (event_id, processed_at) 
     VALUES (:eventId, NOW()) 
     ON CONFLICT (event_id) DO NOTHING;
     ```
     Si la fila ya existía (afecta 0 filas), el consumidor confirma el offset en Kafka y descarta el procesamiento del mensaje duplicado de forma transparente.

---

## P1-5.5: DISTINCIÓN ENTRE REINTENTOS E INTENCIONES LEGÍTIMAS DE NUEVAS APUESTAS

Para dar cumplimiento formal al requisito `P1-REQ-013` (un usuario puede apostar varias veces en la misma carrera, incluso por medianos distintos):
- **Nueva Apuesta Legítima:** Cuando el usuario decide voluntariamente apostar 200 EIA Coins a *Frodito Turbo* y posteriormente 300 EIA Coins a *Bilbo Rápido*, la aplicación cliente genera un **nuevo y diferente `Idempotency-Key`** para cada transacción. El sistema las procesa como operaciones independientes, debitando ambas sumas y registrando dos apuestas distintas.
- **Reintento Duplicado:** Si la red falla y la aplicación cliente reenvía la petición con la **misma `Idempotency-Key`**, el sistema la trata como un reintento idempotente, retornando la confirmación de la primera sin descontar nuevamente los fondos.

---

## P1-5.6, P1-5.7: PREMIOS, COMISIÓN, DEVOLUCIONES Y POLÍTICAS DE NEGOCIO

### 1. Liquidación Estricta de la Bolsa Mutua
- **Bolsa Total Recaudada ($B$):** Suma atómica de todas las apuestas aceptadas en la carrera.
- **Comisión de la Casa ($10\%$):** Retención exacta calculada al liquidar: $R = 0.10 \times B$.
- **Bolsa Neta para Ganadores ($90\%$):** Fondo total distribuible: $B_{\text{neta}} = 0.90 \times B$.
- **Reparto Proporcional:** Para cada apuesta ganadora $a_k$ con monto $m_k$ sobre el mediano ganador con masa total apostada $T_w$:
  $$\text{Premio Bruto}(a_k) = \frac{B_{\text{neta}}}{T_w} \times m_k$$

---

### 2. Políticas de Negocio Propuestas para Definición del Usuario

#### A. Política de Redondeo y Fracciones de la Bolsa (`P1-PA-001`)
- **Problema:** En el cálculo de $\frac{B_{\text{neta}}}{T_w} \times m_k$ pueden generarse fracciones decimales de EIA Coins. Como los saldos se contabilizan en unidades enteras o con precisión fija de 2 decimales, la sumatoria de premios redondeados puede diferir ligeramente del $90\%$ exacto de la bolsa.
- **Propuesta A.1 (Recomendada): Redondeo al entero inferior (*Floor*) y remanente a Fondo de Reserva.**  
  Cada premio individual se trunca al entero inferior (`FLOOR`). La suma de las fracciones indivisibles sobrantes no se pierde: se acumula contablemente en una cuenta del sistema denominada *Fondo de Reserva de Salchipapa Maker Racing*, utilizada para respaldar redondeos futuros o premios especiales.
- **Propuesta A.2: Acreditación con 2 decimales exactos.**  
  Se define el modelo contable de EIA Coins con precisión de tipo `NUMERIC(12, 2)` y el residuo fraccionario menor a $0.01$ se abona a la comisión de la casa.

#### B. Política ante Ausencia de Ganadores (`P1-PA-002`)
- **Problema:** Ningún usuario apostó por el mediano que cruzó la meta en primer lugar ($T_w = 0$). ¿Qué ocurre con la bolsa común?
- **Propuesta B.1 (Recomendada): Reembolso de la Bolsa Neta (90%) a los Apostadores.**  
  La casa retiene su comisión operativa del $10\%$ por organización del evento, y el $90\%$ restante se devuelve íntegramente a todos los usuarios que apostaron en esa carrera, en proporción exacta a lo que apostó cada uno.
- **Propuesta B.2: Reembolso Total del 100%.**  
  Se declara la carrera sin efecto para premios y se devuelve el 100% de los montos apostados a todos los usuarios (tratamiento análogo a una carrera cancelada).
- **Propuesta B.3: Acumulación de la Bolsa (*Rollover* / Pozo Acumulado).**  
  El $90\%$ de la bolsa se traslada como fondo inicial acumulado para la siguiente carrera programada en la Liga.

---

## P1-5.8: HISTÓRICO, ANALÍTICA Y AUDITORÍA INALTERABLE DE CINCO AÑOS

1. **Separación de Ciclos de Vida:**  
   - Los datos operativos de apuestas en la base de datos OLTP se conservan activos durante la temporada.
   - Mediante un proceso de archivado periódico (ETL / streaming desde Kafka), las apuestas y transacciones se consolidan en el almacén de auditoría inmutable de largo plazo.
2. **Garantía de Inmutabilidad:**  
   - La base de datos de auditoría se despliega en una réplica física o servicio de almacenamiento con privilegios estrictos de **solo lectura** para los usuarios humanos (incluido el rol Auditor).
   - Se generan cadenas de resúmenes criptográficos (hashes SHA-256 periódicos por carrera) sobre las tablas de apuestas y premios. Cualquier intento de alteración física en el disco invalidaría la firma del bloque de auditoría.
3. **Reconstrucción Forense de Premios:**  
   - Para cualquier carrera de los últimos 5 años, el rol Auditor puede consultar el registro congelado: monto de la bolsa $B$, mediano ganador oficial certificado, masa $T_w$, cuota final $Q_w$ y lista exhaustiva de apuestas premiadas, reproduciendo exactamente la fórmula de liquidación para validar que no hubo fraude.

---

## P1-5.9: JUSTIFICACIÓN DE TRANSACCIONES LOCALES, OUTBOX Y SAGAS

- **Transacciones Locales (ACID):** Se utilizan en la ruta crítica del Núcleo Modular para asegurar la atomicidad entre el débito de saldo, la validación de cierre y el registro de la apuesta.
- **Transactional Outbox:** Se utiliza para la publicación confiable de eventos hacia Apache Kafka, garantizando que no existan eventos "fantasma" si la base de datos aborta la transacción, ni eventos perdidos si el broker sufre una interrupción transitoria.
- **Descarte de Sagas en la Ruta Crítica:** Se justifica explícitamente no utilizar el patrón Saga para la aceptación de apuestas, dado que requeriría llamadas remotas asíncronas entre apuestas y billetera con transacciones de compensación que harían extremadamente complejo asegurar el límite de 1 segundo e impedir saldos negativos concurrentes.
- **Saga Coreografiada para Liquidación de Premios:** La liquidación masiva sí adopta un patrón por etapas fuera de la ruta crítica: `ResultadoPublicado` $\to$ `CalcularPremios` $\to$ `DispersarAcreditacionesPorLote` $\to$ `ConfirmarLiquidada`, con reintentos idempotentes ante fallos de worker.
