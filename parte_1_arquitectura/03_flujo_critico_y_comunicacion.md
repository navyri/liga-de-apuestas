# ETAPA P1-3: FLUJO CRÍTICO Y COMUNICACIÓN SÍNCRONA
**Caso:** La Gran Liga de Apuestas de Medianos EIA  
**Organización:** Salchipapa Maker Racing S.A.S.  
**Artefacto:** `P1-ART-004`  
**Versión:** `v1.0`  
**Estado:** `[x]` Consolidado y verificado por revisión autónoma  

---

## P1-3.1: FLUJO COMPLETO DE ACEPTACIÓN / RECHAZO DE UNA APUESTA

El flujo de procesamiento de una apuesta representa la ruta transaccional más crítica del sistema, sujeta a la restricción de respuesta en menos de 1 segundo (PDF pág. 9, 15).

```text
Apostador                API Gateway / Edge          Núcleo Modular (Core)          Base de Datos OLTP
   │                             │                            │                             │
   │ 1. POST /api/v1/bets        │                            │                             │
   │    (idempotency_key, raceId,│                            │                             │
   │     racerId, amount)        │                            │                             │
   ├────────────────────────────►│ 2. Rate limit + Anti-bot   │                             │
   │                             │    Validar JWT y claims    │                             │
   │                             ├───────────────────────────►│ 3. Iniciar Transacción Local│
   │                             │                            │    BEGIN TRANSACTION        │
   │                             │                            ├────────────────────────────►│
   │                             │                            │                             │
   │                             │                            │ 4. Validar Idempotencia     │
   │                             │                            │    SELECT FROM bets_idemp   │
   │                             │                            ├────────────────────────────►│
   │                             │                            │                             │
   │                             │                            │ 5. Validar Carrera          │
   │                             │                            │    Estado == 'ABIERTA' &&   │
   │                             │                            │    server_time < start_time │
   │                             │                            ├────────────────────────────►│
   │                             │                            │                             │
   │                             │                            │ 6. Validar Saldo y Bloqueo  │
   │                             │                            │    SELECT balance FROM      │
   │                             │                            │    wallets FOR UPDATE       │
   │                             │                            ├────────────────────────────►│
   │                             │                            │                             │
   │                             │                            │ 7. Débito + Registro + Outbox
   │                             │                            │    UPDATE wallets (balance) │
   │                             │                            │    INSERT INTO bets (...)   │
   │                             │                            │    INSERT INTO outbox (...) │
   │                             │                            ├────────────────────────────►│
   │                             │                            │                             │
   │                             │                            │ 8. COMMIT                   │
   │                             │                            ├────────────────────────────►│
   │                             │ 9. HTTP 201 Created        │                             │
   │                             │    { status: 'ACCEPTED',   │                             │
   │                             │      betId, newBalance }   │                             │
   │◄────────────────────────────┴────────────────────────────┤                             │
   │                                                          │                             │
```

### Detalle Secuencial Paso a Paso:
1. **Despacho del Cliente:** El apostador envía una petición HTTP `POST /api/v1/bets` transportando en el cuerpo: identificador de carrera (`race_id`), mediano seleccionado (`racer_id`), monto a apostar (`amount`) y en la cabecera HTTP un identificador único de intención (`Idempotency-Key` generado por el cliente).
2. **Filtrado en Borde (API Gateway):** Aplica *rate limiting* por IP/usuario y validación de firma criptográfica del token JWT. Si la tasa es excedida, rechaza inmediatamente con `HTTP 429 Too Many Requests` sin tocar el núcleo transaccional.
3. **Apertura de Transacción Local (ACID):** La instancia de `core-api` abre una transacción atómica local en la base de datos relacional operativa.
4. **Verificación de Idempotencia:** Se comprueba si la `idempotency_key` ya fue procesada previamente para este usuario. Si ya existe, se retorna el resultado previamente registrado (`HTTP 200 OK`) sin duplicar débitos.
5. **Comprobación de Reglas de Admisión y Cierre:**
   - Comprueba existencia y habilitación del usuario.
   - Comprueba que el mediano participe efectivamente en dicha carrera.
   - **Regla estricta de cierre:** Se evalúa de forma atómica: `server_current_timestamp < race.start_time` y `race.status == 'ABIERTA'`. Si la hora del servidor alcanzó o superó el inicio de la carrera, la transacción se aborta y se responde `HTTP 409 Conflict / REJECTED_RACE_CLOSED`.
6. **Bloqueo Pesimista de Billetera:** Se ejecuta `SELECT balance FROM wallets WHERE user_id = :uid FOR UPDATE`. Este bloqueo a nivel de fila garantiza que si el usuario emite dos apuestas simultáneas desde dos dispositivos distintos, se procesen de forma estrictamente secuencial.
7. **Validación de Saldo y Ejecución Atómica:**
   - Si `balance < amount`, la transacción se revierte (`ROLLBACK`) y se responde `HTTP 422 Unprocessable Entity / INSUFFICIENT_FUNDS`.
   - Si `balance >= amount`, se actualiza el saldo contable (`balance = balance - amount`), se inserta el registro de la apuesta en la tabla `bets`, y se inserta un registro en la tabla transaccional `outbox` con el evento `BetPlaced` para su posterior difusión asíncrona.
8. **Commit Local:** Se confirma la transacción atómica en la base de datos (`COMMIT`).
9. **Confirmación Determinista al Apostador:** El servidor retorna `HTTP 201 Created` con el detalle de la apuesta aceptada y el saldo restante actualizado, completando el ciclo en decenas de milisegundos (holgadamente dentro del límite de 1 segundo).

---

## P1-3.2: COHERENCIA ESTRICTA ENTRE APUESTA Y DESCUENTO EN BILLETERA

Al haber adoptado la Arquitectura Híbrida (`P1-DEC-001`), la coherencia entre la apuesta y el descuento se resuelve mediante **atomicidad transaccional local** en lugar de transacciones distribuidas:
- **Todo o Nada (All-or-Nothing):** No existe ninguna ventana de vulnerabilidad donde la apuesta quede registrada pero el dinero no se descuente, ni donde el saldo se reduzca pero la apuesta falle.
- **Invariante Preservado:** La integridad contable queda garantizada por las propiedades ACID del motor de base de datos relacional. La propagación hacia componentes externos (analítica, notificaciones, cálculo de cuotas dinámicas) se realiza de forma asíncrona a través del patrón **Transactional Outbox**, garantizando que un evento hacia el broker solo se despache si la transacción local de BD hizo `COMMIT` exitoso.

---

## P1-3.3: VALIDACIONES Y MECANISMO DE CIERRE ESTRICTO

### 1. Definición Formal del Momento de Aceptación
Una apuesta **solo se considera aceptada por el sistema** en el instante exacto en que la transacción local de base de datos ejecuta un `COMMIT` exitoso. Si en cualquier punto previo al commit la transacción falla, se revierte o supera la hora de corte, la apuesta se considera **rechazada de forma determinista**, sin que se registre la jugada ni se debite el saldo.

### 2. Tratamiento de Esperas por Bloqueos y Concurrencia al Cierre
- **El Escenario Crítico:** Un usuario despacha una solicitud de apuesta a las `11:59:59.950` para una carrera que inicia a las `12:00:00.000`. Al ingresar a la base de datos, la solicitud queda en espera (*lock wait*) debido a que otra transacción concurrente sobre el mismo usuario está ejecutándose. Para cuando la transacción adquiere el bloqueo de fila, el reloj del servidor marca las `12:00:00.050`.
- **Regla Inflexible de Rechazo:** Aunque la petición HTTP haya llegado a la infraestructura antes del corte, **si al momento de evaluar la sentencia atómica en el motor la hora del servidor alcanzó o superó `start_time`, la apuesta es irrevocablemente rechazada**.
- **Mecanismo Atómico Conjunto (Hora + Estado + Saldo):**
  La validación no se delega a una lectura aislada previa de `CLOCK_TIMESTAMP()`. Se ejecuta como condición de inserción y bloqueo dentro de la misma sentencia:
  ```sql
  -- Inserción atómica condicionada al reloj exacto y estado de carrera
  INSERT INTO bets (id, user_id, race_id, racer_id, amount, created_at)
  SELECT :bet_id, :user_id, :race_id, :racer_id, :amount, CLOCK_TIMESTAMP()
  FROM races
  WHERE races.id = :race_id 
    AND races.status = 'ABIERTA' 
    AND CLOCK_TIMESTAMP() < races.start_time;
  ```
  Si la carrera transicionó a `CANCELADA` o `CERRADA`, o si la espera por bloqueos hizo que `CLOCK_TIMESTAMP() >= start_time`, la sentencia afecta exactamente **0 filas**. El backend detecta `rows_affected == 0`, ejecuta `ROLLBACK` de la transacción y retorna de inmediato `HTTP 409 Conflict (RACE_CLOSED_OR_NOT_OPEN)` al cliente. Esto garantiza que ninguna espera por contención degrade la regla del corte del servidor.

---

## P1-3.4: TABLA DE COMUNICACIONES SÍNCRONAS EXIGIDA (PDF pág. 14)

Conforme a la estructura obligatoria requerida en la Decisión 3 del PDF, se identifican las comunicaciones que operan de forma estrictamente síncrona:

| Servicio Origen | Servicio Destino | Protocolo | Información Solicitada | ¿Por qué debe ser síncrona? | Estrategia ante Fallo / Timeout |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Cliente Apostador (Web/App)** | **API Gateway / Edge** | HTTPS / REST (JSON) | Solicitud de autenticación, consulta de carreras y emisión de apuesta (`POST /bets`). | El usuario requiere retroalimentación interactiva inmediata en pantalla (< 1 s) para saber si su apuesta fue aceptada. | Timeout de cliente a los 800 ms. Si no hay respuesta, el cliente puede reintentar de forma segura utilizando la misma `Idempotency-Key`. |
| **API Gateway** | **Núcleo Modular (`core-api`)** | HTTP/2 o gRPC interno | Enrutamiento de peticiones de validación y emisión de apuestas con token JWT validado. | Tráfico en la ruta crítica del usuario; requiere latencia sub-milisegunda entre capas de red privada. | Circuit breaker con timeout de 600 ms. En caso de timeout, el gateway responde `HTTP 504 Gateway Timeout` informando que el estado es incierto e invitando a reintentar con la misma clave. |
| **Núcleo Modular (`core-api`)** | **Base de Datos Operativa (OLTP)** | Protocolo nativo de BD (TCP/Pool de conexiones) | Transacción ACID: `SELECT FOR UPDATE` de billetera, validación de corte de carrera e `INSERT` de apuesta. | Garantía obligatoria de no doble gasto, verificación estricta de saldo e integridad contable sin condiciones de carrera. | Timeout transaccional de 500 ms. Si la BD no responde, se ejecuta rollback automático y se retorna error temporal `HTTP 503 Service Unavailable`. |
| **Cliente Operador** | **Núcleo Modular (`core-api`)** | HTTPS / REST | Publicación del resultado oficial verificado de una carrera (`POST /races/{id}/results`). | El operador debe recibir confirmación inmediata del sellado del resultado para dar paso al proceso de liquidación. | Timeout de 2 s. Reintentos manuales idempotentes basados en el identificador único de la carrera. |
| **Cliente Auditor** | **Núcleo Modular / Réplica de Auditoría** | HTTPS / REST | Consulta de registros inalterables de apuestas, saldos y reconstrucción matemática de premios. | Operación de consulta interactiva para tareas de fiscalización y auditoría forense. | Timeout de 5 s. Lectura dirigida a réplica de lectura para no sobrecargar el nodo transaccional primario. |

---

## P1-3.5: GESTIÓN DE TIMEOUTS, REINTENTOS Y RESPUESTAS INCIERTAS

En sistemas transaccionales distribuidos de apuestas bajo alta concurrencia, es imperativo distinguir tres estados lógicos de una operación desde la perspectiva del cliente:
1. **`ACEPTADA` (Determinista):** Transacción local confirmada (`COMMIT`), apuesta persistida en la bolsa y saldo descontado. El cliente recibe `HTTP 201 Created`.
2. **`RECHAZADA` (Determinista):** Regla de negocio no satisfecha (saldo insuficiente, mediano no participante o llegada posterior a la hora de cierre según el reloj del servidor). El cliente recibe `HTTP 422 Unprocessable Entity` o `HTTP 409 Conflict`.
3. **`DESCONOCIDA / INCIERTA` (Por incertidumbre de red o timeout técnico):** La petición no completó su ciclo de respuesta antes del límite de espera técnico del cliente o del gateway (configurado preventivamente en ~800 ms para no retener conexiones bloqueadas). 

> **Aclaración crítica sobre latencia:**  
> El timeout de cliente de 800 ms **no constituye una garantía de que la operación de negocio se resolvió con éxito en menos de un segundo**. Es un mecanismo defensivo para liberar el socket ante fallos de conectividad. Cuando ocurre un timeout, el estado de la apuesta permanece estrictamente en condición de incertidumbre.

### Protocolo de Resolución de Incertidumbre y Reintentos:
1. **Incertidumbre de Red en el Cliente:**  
   Si el cliente web/móvil experimenta timeout o pérdida de paquete antes de recibir confirmación, **la aplicación no debe asumir que la apuesta falló ni que fue cobrada**.
2. **Reintentos Idempotentes Seguros:**  
   La aplicación cliente retiene en memoria la misma `Idempotency-Key` (UUIDv4) generada originalmente. Al ejecutar un reintento automático o tras la acción del usuario, reenvía la misma clave. El servidor detectará si la transacción ya fue confirmada (retornando el estado final sin duplicar cobros) o si se encuentra en procesamiento.
3. **Consulta de Estado Alternativa:**  
   Si persiste la incertidumbre, el cliente puede invocar el endpoint de lectura liviana `GET /api/v1/bets/by-key/{idempotency_key}` para inspeccionar el estado definitivo registrado en el servidor antes de permitir al usuario formular una nueva intención de apuesta.
