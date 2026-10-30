<!-- BANNER:INICIO (bloque estetico; omitido en el PDF consolidado) -->
<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&height=170&color=6B0F1A&text=DATOS%20E%20IDEMPOTENCIA&fontColor=F4ECE4&fontSize=44&fontAlignY=34&desc=Documento%2005%20%C2%B7%20Esquema%20OLTP%2FOLAP%2C%20mayores%20restos%20y%20auditor%C3%ADa%20WORM&descColor=E8B4B8&descAlignY=60"
       alt="Banner: DATOS E IDEMPOTENCIA"/>
</p>

<p align="center">
  <img src="https://64.media.tumblr.com/3254f08405664a04d3c5a65f765eb8c9/61bf168659dda322-50/s2048x3072/36c765a65bc72096e27e85823017367c0b9b48b2.pnj" alt="Ilustración conceptual de estrategia y competición en la academia" width="520"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/ACID-SELECT%20FOR%20UPDATE-540B13?style=flat-square&logoColor=white" alt="ACID: SELECT FOR UPDATE"/>
  <img src="https://img.shields.io/badge/Garantia-Cero%20doble%20gasto-6B0F1A?style=flat-square&logoColor=white" alt="Garantia: Cero doble gasto"/>
  <img src="https://img.shields.io/badge/Universidad-EIA-8B1E2D?style=flat-square&logoColor=white" alt="Universidad: EIA"/>
</p>


<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=rect&height=6&color=6B0F1A"
       alt=""/>
</p>

<!-- BANNER:FIN -->

# ETAPA P1-5: DATOS, PERSISTENCIA E IDEMPOTENCIA
**Caso:** La Gran Liga de Apuestas de Medianos EIA  
**Organización:** Salchipapa Maker Racing S.A.S.  
**Artefacto:** `P1-ART-006`  
**Versión:** `v1.0`  
**Estado:** `[x]` Consolidado (Políticas de negocio y correcciones técnicas incorporadas)  

---

## P1-5.1: ALMACENAMIENTO Y PROPIEDAD DE DATOS

Para cumplir con la Decisión 9 del PDF (pág. 16), se definen los tipos de bases de datos, su propiedad y sus fronteras de acceso:

1. **Base de Datos Operativa Transaccional (OLTP):**
   - **Tecnología recomendada:** Motor Relacional SQL (ej. PostgreSQL administrado).
   - **Propiedad:** Exclusiva del **Núcleo Modular Transaccional (`core-api`)**.
   - **Justificación:** Maneja el libro contable de billeteras, el catálogo de competidores, las carreras y las apuestas. Requiere soporte estricto de transacciones ACID, aislamiento *read committed* con bloqueos pesimistas a nivel de fila (`SELECT FOR UPDATE`), restricciones de clave foránea y claves únicas para garantizar que ningún saldo sea negativo.
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
   - **Tecnología recomendada:** Base de datos con tablas append-only dedicadas y almacenamiento de archivos con retención de solo lectura mediante políticas de inmutabilidad (WORM / Object Lock).
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
 - Header: Idempotency-Key           - Clave natural basada en          - Deduplicación por eventId
 - Restricción UNIQUE en BD:           la apuesta:                      - Tabla processed_events:
   UNIQUE(user_id, idemp_key)          UNIQUE(bet_id, trans_type)        INSERT ... ON CONFLICT DO NOTHING
 - Retorna respuesta cacheada        - Permite múltiples apuestas del   - Evita duplicar efectos
   sin cobrar dos veces                mismo usuario en la carrera        al retroceder offsets
```

1. **Operación 1: Creación y Cobro de una Apuesta (`POST /api/v1/bets`):**
   - *Riesgo:* El usuario pulsa cuatro veces consecutivas el botón de apostar ante lentitud de red.
   - *Mecanismo:* El cliente genera una cabecera HTTP obligatoria `Idempotency-Key: <UUIDv4>`. En la base de datos existe la restricción `UNIQUE (user_id, idempotency_key)` en la tabla `bets_idempotency`. Si entra la segunda, tercera o cuarta petición con la misma clave, la inserción colisiona atómicamente; el servidor intercepta la colisión, lee la respuesta almacenada de la primera transacción confirmada y la retorna de inmediato (`HTTP 200 OK`) sin tocar el balance ni registrar una nueva apuesta.
2. **Operación 2: Acreditación de Premios por Liquidación:**
   - *Riesgo:* El worker de liquidación sufre un fallo transitorio tras pagar un premio y Kafka le reentrega el mensaje de lote, o un operador ejecuta un reintento manual de liquidación.
   - *Mecanismo y Granularidad de la Clave:* Dado que un usuario puede realizar **múltiples apuestas ganadoras legítimas en la misma carrera** (por ejemplo, dos jugadas distintas de 500 EIA Coins cada una), la clave no puede agregarse a nivel de `(race_id, user_id)`. Se define una **clave de unicidad vinculada directamente a la apuesta premiada**:
     $$\text{UNIQUE}(\text{bet\_id}, \text{transaction\_type})$$
     donde `transaction_type = 'PRIZE_PAYOUT'`. Cada apuesta ganadora recibe su pago individual de forma exacta. Si un lote se reintenta, la base de datos detecta que la apuesta ya fue acreditada (`ON CONFLICT DO NOTHING`), impidiendo abonos duplicados sin bloquear el pago de otras apuestas válidas del mismo apostador.
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
- **Nueva Apuesta Legítima:** Cuando el usuario decide voluntariamente apostar 200 EIA Coins a *Frodito Turbo* y posteriormente 300 EIA Coins a *Bilbo Rápido*, la aplicación cliente genera un **nuevo y diferente `Idempotency-Key`** para cada transacción. El sistema las procesa como operaciones independientes, debitando ambas sumas y registrando dos apuestas distintas con identificadores únicos (`bet_id_1`, `bet_id_2`).
- **Reintento Duplicado:** Si la red falla y la aplicación cliente reenvía la petición con la **misma `Idempotency-Key`**, el sistema la trata como un reintento idempotente, retornando la confirmación de la primera sin descontar nuevamente los fondos.

---

## P1-5.6: POLÍTICA DETERMINISTA DE REDONDEO MEDIANTE MAYORES RESTOS (`P1-DEC-003`)

> **Aclaración institucional y contable:**  
> La adopción de una **precisión contable de dos decimales** para los EIA Coins es una **decisión técnica del proyecto** para garantizar exactitud financiera, no un requisito impuesto por el PDF. Para erradicar la imprecisión de coma flotante binaria, todos los cálculos de distribución se realizan utilizando **unidades mínimas enteras (centavos de EIA Coin / centi-coins)**:
> $$1\text{ EIA Coin} = 100\text{ unidades mínimas (centavos)}$$

### Reglas Formales del Algoritmo de Mayores Restos:
1. **Bolsa Total Recaudada en Centavos ($B$):** Sumatoria entera exacta de los montos apostados:
   $$B = \sum_{i=1}^{N} \text{monto\_centavos}_i$$
2. **Determinación de la Comisión Contabilizada ($R$):**
   - Se calcula el 10% teórico: $R_{\text{teorico}} = 0.10 \times B$.
   - Como $0.10 \times B$ puede no ser un entero exacto de centavos, se define la **regla determinista de redondeo bancario estándar al centavo más cercano** (`ROUND_HALF_EVEN`):
     $$R = \text{round}(0.10 \times B)$$
   - *(Aclaración de rigor):* Con precisión contable finita, **no es matemáticamente posible mantener exactamente el 10.000...% en todas las sumas impares de centavos**; la comisión contabilizada absorbe la regla de redondeo determinista.
3. **Bolsa Neta Distribuible Exacta ($B_{\text{neta}}$):**
   - La masa total a repartir entre ganadores se define estrictamente por sustracción:
     $$B_{\text{neta}} = B - R$$
   - Esto garantiza por construcción que:
     $$B_{\text{neta}} + R = B \quad \text{(Conservación absoluta de la bolsa)}$$
4. **Cálculo de Cuotas y Cuotas Teóricas por Apuesta Ganadora:**  
   Sea $T_w$ la masa total apostada (en centavos) al mediano ganador, y sea $a_k$ una apuesta ganadora con monto $m_k$. El premio teórico continuo es:
   $$P_{\text{teorico}}(a_k) = \frac{B_{\text{neta}} \times m_k}{T_w}$$
5. **Asignación de Unidades Enteras Inferiores:**  
   Cada apuesta recibe inicialmente la parte entera inferior truncada de centavos:
   $$P_{\text{base}}(a_k) = \lfloor P_{\text{teorico}}(a_k) \rfloor$$
   El residuo fraccionario de cada apuesta es:
   $$\text{resto}_k = P_{\text{teorico}}(a_k) - P_{\text{base}}(a_k)$$
6. **Cálculo de Centavos Restantes a Distribuir:**
   $$C_{\text{remanente}} = B_{\text{neta}} - \sum_{k=1}^{|G|} P_{\text{base}}(a_k)$$
   Donde $0 \le C_{\text{remanente}} < |G|$.
7. **Distribución Determinista de Mayores Restos:**
   - Se ordenan las apuestas ganadoras de mayor a menor valor de $\text{resto}_k$.
   - **Criterio de Desempate Determinista:** Si dos o más apuestas presentan exactamente el mismo resto fraccionario, el desempate se resuelve ordenando de forma determinista por el **identificador único de apuesta en orden lexicográfico ascendente (`bet_id`)**. Jamás se utiliza el orden de llegada de red ni la secuencia aleatoria de ejecución de workers.
   - A las primeras $C_{\text{remanente}}$ apuestas de la lista ordenada se les adiciona exactamente $+1\text{ centavo}$ ($+0.01\text{ EIA Coin}$).
8. **Determinación Global Previa a la Dispersión en Lotes:**  
   El reparto completo se calcula en **una única fase analítica global** en el `WorkerLiquidacion` tras sellar el resultado. Una vez calculados los importes finales exactos de cada apuesta ganadora, se generan los lotes de acreditación. Los workers dispersores jamás recalculan residuos de forma aislada, garantizando que la sumatoria de pagos coincida al centavo con $B_{\text{neta}}$.
9. **Trazabilidad y Versión de la Política:**  
   La liquidación almacena en la tabla de resultados de la carrera la versión del algoritmo (`settlement_policy_version = 'HAMILTON_LARGEST_REMAINDER_V1'`), los parámetros globales ($B$, $R$, $B_{\text{neta}}$, $T_w$) y el desglose de cada apuesta para reproducción exacta por el rol Auditor.

---

### Ejemplo Numérico Demostrativo de Conservación de la Bolsa

- **Supuesto del ejemplo:**
  - Carrera con 3 apuestas ganadoras ($A_1$, $A_2$, $A_3$).
  - Montos apostados: $A_1 = 33.33\text{ EIA Coins}$ (3.333 centavos), $A_2 = 33.33\text{ EIA Coins}$ (3.333 centavos), $A_3 = 33.34\text{ EIA Coins}$ (3.334 centavos).
  - Masa total ganadora: $T_w = 100.00\text{ EIA Coins}$ (10.000 centavos).
  - Bolsa bruta total recaudada en la carrera: $B = 100.05\text{ EIA Coins}$ (10.005 centavos).
- **Paso 1: Comisión de la casa:**
  - $R_{\text{teorico}} = 0.10 \times 10.005 = 1.000,5\text{ centavos}$.
  - Con redondeo bancario: $R = 1.000\text{ centavos}$ ($10.00\text{ EIA Coins}$).
- **Paso 2: Bolsa Neta Distribuible:**
  - $B_{\text{neta}} = 10.005 - 1.000 = 9.005\text{ centavos}$ ($90.05\text{ EIA Coins}$).
- **Paso 3: Cálculo teórico proporcional por apuesta:**
  - $P_{\text{teorico}}(A_1) = \frac{9.005 \times 3.333}{10.000} = 3.001,3665\text{ centavos} \to \text{Base} = 3.001$, $\text{Resto} = 0,3665$.
  - $P_{\text{teorico}}(A_2) = \frac{9.005 \times 3.333}{10.000} = 3.001,3665\text{ centavos} \to \text{Base} = 3.001$, $\text{Resto} = 0,3665$.
  - $P_{\text{teorico}}(A_3) = \frac{9.005 \times 3.334}{10.000} = 3.002,2670\text{ centavos} \to \text{Base} = 3.002$, $\text{Resto} = 0,2670$.
- **Paso 4: Suma base y residuo:**
  - $\text{Suma Bases} = 3.001 + 3.001 + 3.002 = 9.004\text{ centavos}$.
  - $C_{\text{remanente}} = 9.005 - 9.004 = 1\text{ centavo}$ a repartir.
- **Paso 5: Asignación por mayor resto y desempate determinista:**
  - Comparación de restos: $A_1 (0,3665)$ empata con $A_2 (0,3665)$, y ambos superan a $A_3 (0,2670)$.
  - Desempate determinista por `bet_id`: Suponiendo que $A_1.\text{bet\_id} = \text{'BET-001'}$ y $A_2.\text{bet\_id} = \text{'BET-002'}$, el identificador `'BET-001'` antecede lexicográficamente.
  - El centavo remanente se asigna a $A_1$.
- **Resultado Final:**
  - $A_1 = 3.001 + 1 = 3.002\text{ centavos}$ ($30.02\text{ EIA Coins}$).
  - $A_2 = 3.001\text{ centavos}$ ($30.01\text{ EIA Coins}$).
  - $A_3 = 3.002\text{ centavos}$ ($30.02\text{ EIA Coins}$).
- **Comprobación de Conservación Absoluta:**
  $$\sum \text{Premios} = 30.02 + 30.01 + 30.02 = 90.05\text{ EIA Coins}$$
  $$\text{Bolsa Total} = \text{Comisión Contabilizada} (10.00) + \text{Suma Premios} (90.05) = 100.05\text{ EIA Coins} \equiv B$$
  *(Verificado: Cero fuga o ganancia artificial de fondos).*

---

## P1-5.7: POLÍTICA ANTE AUSENCIA DE GANADORES (`P1-DEC-004`)

> **Aclaración institucional:**  
> El PDF no estipula el destino de la bolsa si ningún usuario apostó por el mediano ganador. Esta política constituye una **decisión formal del proyecto** para resolver dicho vacío normativo.

### Reglas Formales ante Ausencia de Ganadores:
1. **Condición de Disparo:** Se publica el resultado oficial de la carrera y la masa de apuestas sobre el mediano ganador es nula ($T_w = 0$).
2. **Reembolso Íntegro del 100%:** Se reintegra el 100% de lo apostado a cada usuario que haya participado con apuestas aceptadas en esa carrera.
3. **No Retención de Comisión:** Salchipapa Maker Racing S.A.S. renuncia a la retención del 10% en este escenario excepcional; los apostadores reciben la totalidad de su dinero virtual.
4. **No Generación de Pozo Acumulado:** No se acumula bolsa para carreras futuras (*no rollover*), garantizando el cierre contable limpio e inmediato del evento.
5. **Preservación del Ciclo de Vida y del Historial:**
   - **La carrera NO pasa a estado `CANCELADA`:** La carrera sí se corrió deportivamente, el mediano ganador sí cruzó la meta y las estadísticas de rendimiento de los competidores permanecen válidas en el catálogo.
   - El estado de la carrera transiciona a `FINALIZADA` y posteriormente a `LIQUIDADA`.
   - Se registra un motivo de liquidación explícito en el registro oficial:
     $$\text{settlement\_reason} = \text{'SIN\_APUESTAS\_GANADORAS'}$$
6. **Diferenciación Conceptual de Devoluciones:**  
   Se distingue formalmente la devolución por carrera suspendida/anulada (`REFUND_RACE_CANCELLED`) de la devolución por ausencia de aciertos (`REFUND_NO_WINNERS`), permitiendo al auditor distinguir incidentes operativos de desenlaces deportivos sin ganadores.
7. **Idempotencia en Devoluciones:** Cada devolución individual está indexada por la clave de unicidad `UNIQUE (bet_id, 'REFUND_NO_WINNERS')`, evitando duplicaciones contables ante reintentos de workers.
8. **Tratamiento de Bolsa Vacía:** Si una carrera no acumuló ninguna apuesta ($B = 0$), el proceso transiciona directamente a `LIQUIDADA` con motivo `BOLSA_VACIA`, sin invocar divisiones por cero ni crear registros contables artificiales.

---

## P1-5.8: HISTÓRICO, ANALÍTICA Y AUDITORÍA INALTERABLE DE CINCO AÑOS

1. **Separación de Ciclos de Vida:**  
   - Los datos operativos de apuestas en la base de datos OLTP se conservan activos durante la temporada.
   - Mediante un proceso de archivado periódico (ETL / streaming desde Kafka), las apuestas y transacciones se consolidan en el almacén de auditoría inmutable de largo plazo.
2. **Mecanismos de Protección Efectiva contra Alteraciones:**  
   - *(Aclaración conceptual crítica):* **La replicación de bases de datos no equivale a inmutabilidad**. Si un atacante o error muta un dato en el nodo primario, la replicación propagaría la mutación a las réplicas.
   - La inmutabilidad real de los 5 años se fundamenta en tres barreras:
     1. *Permisos de Motor:* Conexiones de auditoría configuradas con privilegios exclusivos `SELECT` a nivel de RBAC de base de datos.
     2. *Almacenamiento Físico WORM / Object Lock:* Los registros históricos consolidados se exportan en formato inmutable (ej. Parquet/ORC) a un almacenamiento de objetos con política WORM (*Write Once, Read Many*) con bloqueo de retención de cumplimiento legal por 5 años, que impide físicamente la eliminación o modificación incluso por administradores de sistema.
     3. *Sellado Criptográfico:* Cadenas de hashes criptográficos (SHA-256) generadas al cierre de cada carrera, permitiendo verificar matemáticamente que las tablas de auditoría no han sufrido adulteración física.
3. **Reconstrucción Forense de Premios:**  
   - Para cualquier carrera histórica, el rol Auditor puede consultar el registro congelado: monto de la bolsa $B$, mediano ganador oficial certificado, masa $T_w$, cuota final $Q_w$, versión de política utilizada y lista exhaustiva de apuestas premiadas, reproduciendo exactamente el algoritmo de mayores restos para verificar la exactitud de cada EIA Coin distribuido.

---

## P1-5.9: JUSTIFICACIÓN DE TRANSACCIONES LOCALES, OUTBOX Y SAGAS

- **Transacciones Locales (ACID):** Se utilizan en la ruta crítica del Núcleo Modular para asegurar la atomicidad entre el débito de saldo, la validación de cierre y el registro de la apuesta.
- **Transactional Outbox:** Se utiliza para la publicación confiable de eventos hacia Apache Kafka, garantizando que no existan eventos "fantasma" si la base de datos aborta la transacción, ni eventos perdidos si el broker sufre una interrupción transitoria.
- **Descarte de Sagas en la Ruta Crítica:** Se justifica explícitamente no utilizar el patrón Saga para la aceptación de apuestas, dado que requeriría llamadas remotas asíncronas entre apuestas y billetera con transacciones de compensación que harían extremadamente complejo asegurar el límite de 1 segundo e impedir saldos negativos concurrentes.
- **Saga Coreografiada para Liquidación de Premios:** La liquidación masiva adopta un flujo desacoplado por etapas fuera de la ruta crítica: `ResultadoPublicado` $\to$ `CalcularPremiosGlobal` $\to$ `DispersarLotes` $\to$ `ConfirmarLiquidacion`, con reintentos idempotentes y trazabilidad individualizada por apuesta.
