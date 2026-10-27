# ETAPA P1-6: ESCALABILIDAD, DIMENSIONAMIENTO Y MANEJO DE FALLOS
**Caso:** La Gran Liga de Apuestas de Medianos EIA  
**Organización:** Salchipapa Maker Racing S.A.S.  
**Artefacto:** `P1-ART-007`  
**Versión:** `v1.0`  
**Estado:** `[x]` Consolidado y verificado por revisión autónoma  

---

## P1-6.1 Y P1-6.2: ANÁLISIS DE CARGA MASIVA, CUELLOS DE BOTELLA Y ESCALAMIENTO

### 1. Perfil Cuantitativo de la Carga Extrema (PDF págs. 8, 15)
- **Carga Concurrente Máxima:** 100.000 usuarios conectados en la final de la Copa Intersemestral Dyllan Salchipapa Maker.
- **Ráfaga Transaccional de Apuestas:** **10.000 apuestas por segundo sostenidas durante los 30 segundos previos al cierre**.
- **Volumen Total del Pico:** $10.000\text{ apuestas/s} \times 30\text{ s} = 300.000\text{ apuestas}$ procesadas bajo máxima contención.

### 2. Identificación Precisa de Cuellos de Botella Físicos
Bajo esta ráfaga masiva, los puntos críticos de saturación no se ubican en la capa de cómputo stateless, sino en:
1. **Contención de Conexiones en Borde:** 100.000 conexiones concurrentes demandan terminación TLS eficiente y balanceo con *connection pooling* para no agotar los descriptores de archivo del sistema operativo.
2. **Contención de Base de Datos en Bloqueos de Fila:** 10.000 escrituras concurrentes por segundo sobre la tabla de billeteras. Aunque cada usuario tiene su propia fila (`wallets`), si múltiples apuestas concurrentes provienen del mismo usuario (o de bots), se genera contención por la cláusula `SELECT FOR UPDATE`.
3. **Escritura del Write-Ahead Log (WAL) e IOPS de Almacenamiento:** Confirmar 10.000 transacciones ACID locales por segundo en disco físico impone una demanda masiva de IOPS y rendimiento de sincronización de fsync.

### 3. Asimetría de Escalamiento: Componentes que Escalan vs. Componentes que No Escalan Igual

```text
 ┌─────────────────────────────────────────────────────────────────────────────────────────────┐
 │                     ESCALAMIENTO ASIMÉTRICO ANTE EL PICO DE APUESTAS                        │
 └──────────────────────────────────────────────┬──────────────────────────────────────────────┘
         ┌──────────────────────────────────────┴──────────────────────────────────────┐
         ▼                                                                             ▼
 [ESCALAN AGRESIVAMENTE EN EL PICO]                             [NO NECESITAN ESCALAR EN EL PICO]
 1. API Gateway / Reverse Proxy (HTTP/2, TLS)                   1. Worker de Liquidación de Premios
    - Absorbe conexiones de 100k usuarios                          - La carrera sigue abierta; no calcula premios
 2. Núcleo Modular (core-api en réplicas)                       2. Almacén Analítico OLAP / Reportes Premium
    - Escala horizontalmente (CPU/Memoria)                         - Tolera retraso; se pausa la analítica pesada
 3. Tópicos de Apache Kafka (apuestas.aceptadas)                3. Canales Externos de Notificaciones
    - Particiones dimensionadas para ingesta                       - Desacoplados por colas; drenan a su ritmo
 4. Base de Datos Transaccional OLTP (IOPS / CPU)               4. Consolas Administrativas / Operadores
    - Provisión de IOPS y réplicas de lectura                      - Volumen transaccional despreciable (< 1 op/s)
```

- **Componentes que deben escalar agresivamente:**
  - *API Gateway:* Escalamiento horizontal elástico para manejar los 100.000 sockets y aplicar rate limiting/anti-bot.
  - *Instancias del Núcleo Modular (`core-api`):* Pool de réplicas sin estado (*stateless*) para procesar validaciones de tokens, reglas de negocio e inserciones locales.
  - *Almacenamiento OLTP:* Aprovisionamiento elástico de IOPS en almacenamiento SSD/NVMe y réplicas de lectura para segregar consultas.
- **Componentes que NO escalan en el pico:**
  - *Liquidación de Premios:* Permanece inactiva durante la ráfaga (la carrera no ha finalizado).
  - *Servicio de Analítica:* Mantiene consumo a ritmo diferido sin demandar recursos durante el cierre.
  - *Módulos Administrativos:* El tráfico de operadores y auditores es mínimo y no requiere escalamiento elástico.

---

## P1-6.3: CUMPLIMIENTO DEL TIEMPO DE RESPUESTA EN MENOS DE UN SEGUNDO

Para asegurar que el usuario conozca deterministamente si su jugada fue aceptada o rechazada en $< 1\text{ segundo}$ bajo ráfaga:
1. **Presupuesto de Latencia (*Latency Budget*):**
   - Red de cliente a Gateway (Red externa 4G/WiFi): $\approx 150 - 300\text{ ms}$.
   - Procesamiento en Gateway (Rate limiting, auth token check): $\approx 5 - 10\text{ ms}$.
   - Red privada interna (Gateway a `core-api`): $\approx 2 - 5\text{ ms}$.
   - Transacción Local Atómica en BD (Bloqueo de fila por usuario + validación de hora + inserts): $\approx 15 - 40\text{ ms}$.
   - Serialización y respuesta HTTP 201: $\approx 5\text{ ms}$.
   - Retorno por red al cliente: $\approx 150 - 300\text{ ms}$.
   - **Latencia Total Estimada:** $\mathbf{330 - 660\text{ ms}}$ (holgadamente inferior al umbral de 1.000 ms).
2. **Estrategias para Proteger el Presupuesto de Latencia:**
   - Cero saltos de red distribuidos síncronos en el backend (se rechazaron microservicios con llamadas RPC intermedias).
   - Publicación asíncrona mediante Transactional Outbox: la escritura en Kafka no forma parte del ciclo de reloj de la petición HTTP del cliente.

---

## P1-6.4: MECANISMO TÉCNICO PARA IMPEDIR ACEPTACIONES POSTERIORES AL CIERRE

Conforme a la regla del PDF (pág. 3: *"Una apuesta que llegue después del cierre debe rechazarse, aunque el usuario la haya enviado antes"*):
1. **Autoridad Absoluta del Reloj:** Se implementa sincronización temporal mediante Network Time Protocol (NTP / PTP) en todos los nodos de cómputo y base de datos con deriva inferior a 5 ms.
2. **Filtro de Dos Fases:**
   - *Fase 1 (En memoria en `core-api`):* Si `local_server_time >= race.start_time`, la petición se rechaza de inmediato con `HTTP 409 Conflict` sin interactuar con la base de datos, aliviando la carga del motor en los segundos posteriores al corte.
   - *Fase 2 (Atómica en BD - Guardián Definitivo):* La sentencia de inserción condiciona su ejecución a la marca temporal local del motor:
     ```sql
     INSERT INTO bets (id, user_id, race_id, racer_id, amount, created_at)
     SELECT :betId, :userId, :raceId, :racerId, :amount, CLOCK_TIMESTAMP()
     FROM races
     WHERE races.id = :raceId 
       AND races.status = 'ABIERTA' 
       AND CLOCK_TIMESTAMP() < races.start_time;
     ```
     Si el reloj del motor alcanzó o superó `races.start_time`, la consulta afecta 0 filas, provocando el aborto transaccional determinista.

---

## P1-6.5: CUMPLIMIENTO DEL PLAZO DE LIQUIDACIÓN (< 15 MINUTOS PARA > 1.000.000 DE APUESTAS)

Para liquidar más de 1.000.000 de apuestas en menos de 15 minutos (900 segundos):
1. **Demanda Contable Mínima:**
   $$\text{Throughput Mínimo} = \frac{1.000.000\text{ apuestas}}{900\text{ segundos}} \approx 1.111\text{ acreditaciones por segundo}$$
2. **Dimensionamiento y Paralelismo:**
   - La fase global del algoritmo de mayores restos toma $< 10\text{ segundos}$ en memoria en el `WorkerLiquidacion`.
   - Se generan $\sim 1.000\text{ a } 2.000\text{ lotes}$ de 500 a 1.000 apuestas cada uno en el tópico `liquidacion.lotes`.
   - Un pool de **10 workers concurrentes** consumiendo particiones independientes ejecuta inserciones masivas agrupadas (`batch inserts` y `UPDATE wallets ... FROM (VALUES ...)`), logrando una capacidad agregada de $2.000\text{ a } 3.000\text{ acreditaciones/s}$.
   - **Tiempo Total Estimado:** $\mathbf{6\text{ a } 9\text{ minutos}}$ (satisfaciendo holgadamente la exigencia de 15 minutos).

---

## P1-6.6: DURABILIDAD ABSOLUTA Y RECUPERACIÓN ANTE DESASTRES

Para dar cumplimiento formal al requisito `P1-REQ-008` (pérdida cero de apuestas aceptadas y movimientos de billetera):
1. **Persistencia Síncrona en Motor OLTP:** Configuración de base de datos con `synchronous_commit = on` y replicación síncrona a nivel de *Write-Ahead Log* hacia al menos una réplica secundaria en zona de disponibilidad independiente.
2. **Puntos de Recuperación (*RPO* y *RTO*):**
   - **RPO (Recovery Point Objective):** **0 segundos** (cero pérdida de transacciones confirmadas).
   - **RTO (Recovery Time Objective):** **< 30 segundos** mediante conmutación por error automática (*failover*) del nodo primario de base de datos.
3. **Respaldo Físico y Continuo:** Copias de seguridad completas diarias más archivado continuo de segmentos WAL (*Point-in-Time Recovery* - PITR) hacia almacenamiento de objetos redundante.

---

## P1-6.7 Y P1-6.8: ANÁLISIS FORMAL DE ESCENARIOS DE FALLO (PDF pág. 16)

### Caso A: El sistema de notificaciones está caído
- **¿Los usuarios deberían poder seguir apostando?:** **SÍ, TOTALMENTE.**
- **Justificación Técnica:**  
  La aceptación de una apuesta es un hecho transaccional crítico que ocurre exclusivamente entre el cliente, el API Gateway, el Núcleo Modular y la base de datos OLTP. El subsistema de notificaciones está **completamente desacoplado de la ruta crítica** mediante Apache Kafka.
- **Comportamiento del Sistema:**  
  Los eventos `ApuestaAceptada` continúan acumulándose de forma segura en el tópico de Kafka. El usuario recibe su confirmación síncrona en pantalla (`HTTP 201 Created`). Cuando el servicio de notificaciones se recupera, reanuda la lectura desde su último offset confirmado y despacha los correos/push pendientes sin haber afectado en absoluto la disponibilidad operativa de las apuestas.

### Caso B: El servicio de billetera (o módulo de billetera) está caído
- **¿Los usuarios deberían poder seguir apostando?:** **NO, DEBEN RECHAZARSE / BLOQUEARSE.**
- **Justificación Técnica:**  
  La comprobación de saldo y el descuento de EIA Coins constituyen una **precondición obligatoria e indivisible** para admitir una apuesta (invariante de no saldo negativo y no doble gasto).
- **Explicación de por qué las respuestas son diametralmente distintas:**  
  Mientras que las notificaciones son una capacidad informativa de **consistencia eventual** (cuya demora o pérdida temporal no altera el estado financiero de los participantes), la billetera gobierna la **consistencia fuerte y la integridad de fondos** de la plataforma. Admitir apuestas con la billetera inhabilitada obligaría a operar a crédito o a ciegas, derivando en saldos negativos incontrolados y violando las reglas fundamentales del modelo pari-mutuel.

---

## P1-6.9: CASO C (OPCIONAL): CORRECCIÓN DE RESULTADOS TRAS FOTO DE LLEGADA MAL INTERPRETADA

Conforme al caso opcional del PDF (pág. 16): *Diez minutos después de publicado el resultado oficial, un operador descubre que la foto de llegada fue mal interpretada y el ganador era otro mediano, habiéndose pagado ya algunos premios*.

```text
 ┌─────────────────────────────────────────────────────────────────────────────────────────────┐
 │                         PROTOCOLO FORENSE DE CORRECCIÓN DE RESULTADO                        │
 └──────────────────────────────────────────────┬──────────────────────────────────────────────┘
         ┌──────────────────────────────────────┼──────────────────────────────────────┐
         ▼                                      ▼                                      ▼
 [1. DETECCIÓN Y CONGELAMIENTO]        [2. TRAZABILIDAD Y NO MUTACIÓN]        [3. COMPENSACIÓN CONTABLE]
 - Operador emite Rectificación        - NUNCA se borran los registros        - Se calculan premios correctos
 - Pausa inmediata de liquidación        erróneos anteriores                    para el mediano legítimo
 - Estado: RECTIFICACION_PENDIENTE     - Registro de auditoría del evento     - Movimiento compensatorio en saldo
                                         y del operador responsable           - Trazabilidad contable intacta
```

### Protocolo de Compensación sin Pérdida de Trazabilidad:
1. **Prohibición de Alteración Destructiva:**  
   Bajo ninguna circunstancia se ejecutan sentencias destructivas (`DELETE` o `UPDATE` sobre el historial contable ya aplicado). La auditoría forense exige preservar la evidencia del error humano original.
2. **Transición a Estado `RESULTADO_EN_RECTIFICACION`:**  
   El operador autorizado registra formalmente la corrección (`POST /api/v1/races/{id}/rectify`) adjuntando la nueva evidencia visual y el motivo. El sistema frena de inmediato cualquier lote de acreditación en curso para esa carrera.
3. **Cálculo de la Nueva Liquidación Oficial:**  
   El worker recalcula la bolsa mutua para el mediano legítimo $M_{\text{correcto}}$, generando los montos de premio correctos con una nueva versión de liquidación (`settlement_version = 2`).
4. **Política de Saldo y Ajuste Contable:**
   - **Invariante de Saldo Preservado:** Si el usuario que recibió el premio erróneo ya consumió sus EIA Coins, **su balance jamás se fuerza a negativo**, respetando la restricción física `CHECK (balance >= 0)`. No se inventa una recuperación mágica de fondos virtuales inexistentes.
   - **Diferenciación de Movimientos:**
     - *Premio Original:* Registrado con `transaction_type = 'PRIZE_PAYOUT'` y `settlement_version = 1`.
     - *Nuevo Premio Legítimo:* Se abona a los verdaderos ganadores con `transaction_type = 'PRIZE_PAYOUT'` y `settlement_version = 2`. La clave de idempotencia compuesta `UNIQUE(bet_id, transaction_type, settlement_version)` permite el pago legítimo sin colisionar con la liquidación errónea previa.
     - *Ajuste Compensatorio:* Al usuario beneficiado por error se le descuenta el balance disponible hasta un mínimo de 0 (`LEAST(balance, erroneous_amount)`) mediante un movimiento de tipo `ADJUSTMENT_ERRONEOUS_PAYOUT`. El importe insoluto no recuperable se registra en auditoría como pérdida operativa de Salchipapa Maker Racing asumida por rectificación deportiva.
5. **Sellado de Auditoría:**  
   Se emite un evento inmutable `ResultadoRectificado` que ingresa a la cadena criptográfica de auditoría, documentando la identidad del operador, la marca de tiempo de la corrección y el impacto financiero exacto.

---

## P1-6.10: PLAN CONCEPTUAL DE MÉTRICAS Y VALIDACIÓN ARQUITECTÓNICA

Para validar empíricamente que la arquitectura soporta las demandas cuantitativas antes de la Copa Intersemestral:

| Dimensión a Validar | Métrica Clave | Umbral Aceptable | Herramienta / Método Conceptual |
| :--- | :--- | :--- | :--- |
| **Capacidad de Ingesta** | Tasa de apuestas aceptadas/s | $\ge 10.000\text{ apuestas/s}$ sostenidas durante $30\text{ s}$ | Prueba de carga distribuida en ambiente de pruebas (Locust / k6). |
| **Latencia Percibida** | Percentil 95 y 99 ($p95, p99$) | $p99 < 800\text{ ms}$ en respuesta de confirmación | Trazabilidad distribuida y métricas de APM (Prometheus + Grafana). |
| **Integridad de Saldo** | Conteo de saldos negativos | **Exactamente 0** bajo ráfaga concurrente | Verificación contable automatizada tras prueba de estrés. |
| **Cierre Estricto** | Apuestas aceptadas con $t \ge T_{\text{cierre}}$ | **Exactamente 0** | Inyección de tráfico cruzando deliberadamente la marca de tiempo de corte. |
| **Plazo de Liquidación** | Duración de liquidación masiva | $< 15\text{ minutos}$ para $1.000.000$ de apuestas simuladas | Medición de reloj entre evento `ResultadoOficialPublicado` y `CarreraLiquidada`. |
