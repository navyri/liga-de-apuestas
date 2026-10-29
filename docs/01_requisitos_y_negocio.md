# ETAPA P1-1: ANÁLISIS DE NEGOCIO Y REQUISITOS
**Caso:** La Gran Liga de Apuestas de Medianos EIA  
**Organización:** Salchipapa Maker Racing S.A.S.  
**Artefacto:** `P1-ART-002`  
**Versión:** `v1.1`  
**Estado:** `[x]` Verificado y consolidado (P1-1.1 aprobado por usuario; P1-1.2 a P1-1.5 completados por revisión autónoma)  

---

## P1-1.1: ACTORES, ROLES Y CAPACIDADES DEL SISTEMA

### 1. Actores y Roles del Sistema

#### Distinción entre Requisitos Explícitos del PDF y Propuesta de Asignación de Responsabilidades:

| Rol | Elementos Explícitos en el PDF (Fuente: PDF págs. 3, 4, 7, 8, 12) | Propuesta de Asignación / Alcance Técnico (Propuesto a aprobación) |
| :--- | :--- | :--- |
| **Apostador** | • Nombre de rol explícito (pág. 4).<br>• Puede registrarse, iniciar sesión y consultar perfiles (pág. 4).<br>• Puede consultar carreras disponibles y realizar apuestas usando EIA Coins (pág. 2, 3).<br>• Puede realizar varias apuestas en la misma carrera, incluso sobre medianos distintos (pág. 3).<br>• Dispone de billetera virtual para consultar saldo y movimientos (pág. 6).<br>• Recibe notificaciones de eventos (pág. 6-7).<br>• Una apuesta enviada después del cierre es rechazada según reloj del servidor (pág. 3). | • Sujeto a rate limiting perimetral y mecanismos de mitigación de bots automatizados.<br>• Consulta de cuotas dinámicas y ficha de competidores con tolerancia a lecturas eventuales.<br>• Clientes móviles y web operan contra interfaces de consumo público. |
| **Operador de Carrera** | • Nombre de rol explícito (pág. 4).<br>• No tiene detalle de funciones taxativas en la pág. 4. Se deduce de la capacidad "Carreras" (pág. 5) y "Resultados y premios" (pág. 6) que registra/interviene en programación, inicio, fin y resultados oficiales. | • **Propuesta:** Interfaz interna autenticada para parametrizar eventos (pistas, distancias, medianos participantes y horarios).<br>• **Propuesta:** Ingreso o confirmación de inicio, fin y captura de foto de llegada/resultado oficial.<br>• **Regla estricta:** El cierre de apuestas NO depende de que el operador presione un botón; se rige estrictamente por la hora programada y el reloj del servidor.<br>• No posee facultades para alterar saldos de billeteras arbitrariamente. |
| **Administrador** | • Nombre de rol explícito (pág. 4).<br>• Administrar roles, bloquear usuarios y validar permisos (pág. 4).<br>• Todas las acciones administrativas deben registrarse (pág. 12). | • **Propuesta:** Gestión de usuarios (bloqueo/desbloqueo de cuentas sospechosas identificadas por auditoría).<br>• **Propuesta:** Asignación y revocación de privilegios RBAC.<br>• Principio de mínimo privilegio: sin acceso directo de mutación a balances contables históricos ni mutación de resultados oficiales sellados. |
| **Auditor** | • Nombre de rol explícito (pág. 4).<br>• **Permisos exclusivos de solo lectura** (explícito pág. 7).<br>• Consulta registro inalterable de apuestas, movimientos de billetera, premios y cambios de resultados (pág. 7).<br>• Detección de comportamientos sospechosos (múltiples cuentas por dispositivo, apuestas masivas al cierre) (pág. 8).<br>• Reconstrucción histórica de cálculo de premios de cualquier carrera (pág. 8). | • Consola de supervisión analítica y forense conectada a réplicas o almacenes inmutables de auditoría.<br>• Incapacidad total de mutación, inserción o borrado en el plano transaccional. |

---

### 2. Las Nueve Capacidades Principales del Sistema (Fuente: PDF págs. 3-8)
El PDF establece de forma numerada y taxativa exactamente **nueve capacidades principales** (secciones 1 a 9, págs. 4 a 8):

1. **Usuarios y autenticación (PDF pág. 4):** Registrar usuarios, iniciar sesión, consultar perfiles, administrar roles, bloquear usuarios y validar permisos. Protección estricta de contraseñas y datos personales.
2. **Medianos (PDF pág. 4-5):** Almacenar información de cada competidor: nombre, edad, peso, historial de carreras, victorias, derrotas, velocidad promedio y estado actual.
3. **Carreras (PDF pág. 5):** Administrar creación de carreras, programación, participantes, horarios, pistas, inicio de carrera, finalización y resultados oficiales. Comunicación inmediata de cambios de estado a la plataforma.
4. **Apuestas (PDF pág. 5):** Permitir realizar apuestas sobre carreras disponibles. Validaciones previas obligatorias: existencia de usuario, carrera abierta (antes del cierre según servidor), mediano participante, saldo suficiente y ausencia de duplicados. Soporte de miles de apuestas por segundo.
5. **Billetera de EIA Coins (PDF pág. 6):** Billetera virtual por usuario para consultar saldo, descontar EIA Coins al apostar, acreditar premios, consultar movimientos y realizar devoluciones ante carreras canceladas. Invariante: nunca permitir doble gasto de monedas ni saldos negativos.
6. **Resultados y premios (PDF pág. 6):** Recepción del resultado oficial al terminar la carrera: identificar ganador, ubicar apuestas ganadoras, calcular premios (bolsa mutua con 10% retenido por la casa), acreditar EIA Coins, registrar movimientos y generar auditoría. Soporte de más de un millón de apuestas sin procesarlas en una sola petición HTTP.
7. **Notificaciones (PDF pág. 6-7):** Envío de mensajes a usuarios por correo, app móvil y push ante hitos: apuesta aceptada, inicio de carrera, término de carrera, apuesta ganada, acreditación de monedas y carrera cancelada. Aislamiento: su caída no debe impedir registrar apuestas.
8. **Estadísticas y analítica (PDF pág. 7):** Almacenamiento masivo diario (millones de registros) de apuestas, montos, comportamiento, carreras, rendimiento histórico de medianos, probabilidades, tendencias y eventos. No requiere tiempo real estricto (retraso de minutos permitido; reportes premium hasta un día).
9. **Auditoría y control de fraude (PDF pág. 7-8):** Registro inalterable y conservado al menos 5 años de toda operación que afecte saldos, apuestas o resultados; consulta de solo lectura para auditor; detección de fraudes y reconstrucción exacta del reparto de premios.

---

### 3. Aclaración Metodológica y Aspectos Transversales
- **Diferenciación entre Capacidades Principales y Lista de Referencia para División de Servicios:**  
  En la pág. 13 (Decisión 2), el PDF presenta una lista de capacidades como referencia para evaluar qué separar o agrupar en servicios: *(usuarios, medianos, carreras, apuestas, billetera, resultados, premios, notificaciones, estadísticas, auditoría)*. En dicha lista de trabajo se mencionan "resultados" y "premios" como conceptos separados, pero en el cuerpo principal del enunciado funcional (pág. 6) ambas forman una única capacidad denominada **"6. Resultados y premios"**. El diseño arquitectónico respetará las 9 capacidades del dominio de negocio y analizará su división técnica en P1-2.
- **Aspectos Transversales de Arquitectura (No capacidades de negocio aisladas):**  
  - **Seguridad (PDF pág. 12):** Autenticación, autorización RBAC, protección de APIs, cifrado en tránsito/reposo, credenciales, rate limiting, anti-bot y segmentación de red pública vs. privada.
  - **Costos y Simplicidad (PDF pág. 12-13, 19, 20):** La directriz de Dyllan ("no pagar infraestructura de Netflix para una carrera de cinco medianos") es un criterio rector de gobernanza y economía técnica que restringe la sobreingeniería en todo el diseño.

---

### 4. Regla Estricta del Cierre de Apuestas
- **Independencia de Intervención Humana:**  
  El cierre de apuestas está fijado exactamente a la hora de inicio de la carrera según el **reloj del servidor** (PDF pág. 3). **No depende de una orden manual ni de un botón accionado por el Operador de Carrera**. Cualquier solicitud recibida tras la marca de tiempo de cierre del servidor es rechazada irrevocablemente, independientemente de la latencia del cliente o de cuándo fue despachada por el usuario.

---

## P1-1.2: REGLAS DEL NEGOCIO Y CICLO DE CARRERA

### 1. Modelo de Premios: Apuesta Mutua (Pari-Mutuel) (PDF pág. 3)
El sistema opera bajo un esquema estricto de bolsa común (*Pari-Mutuel*):
- **Bolsa Bruta ($B$):** Sumatoria total de los montos apostados por todos los usuarios en la carrera $c$:
  $$B = \sum_{i=1}^{N} \text{monto}_i$$
- **Retención de la Casa ($R$):** La casa (Salchipapa Maker Racing S.A.S.) retiene exactamente el **10%** de la bolsa total:
  $$R = 0.10 \times B$$
- **Bolsa Neta Distribuible ($B_{\text{neta}}$):** Fondo total destinado a premiar a los apostadores ganadores (**90%** de la bolsa):
  $$B_{\text{neta}} = 0.90 \times B$$
- **Reparto Proporcional a Ganadores:** Si el mediano ganador es $M_w$, el conjunto de apuestas ganadoras es $G = \{a \mid a.\text{mediano} = M_w\}$. La masa total apostada al ganador es:
  $$T_w = \sum_{a \in G} a.\text{monto}$$
  El premio asignado a una apuesta individual ganadora $a_k \in G$ se calcula en estricta proporción a su contribución individual:
  $$\text{Premio}(a_k) = B_{\text{neta}} \times \left( \frac{a_k.\text{monto}}{T_w} \right) = \frac{0.90 \times B}{T_w} \times a_k.\text{monto}$$
- **Fijación de la Cuota Definitiva:** La cuota final oficial por unidad apostada ($Q_w$) queda sellada matemáticamente en el instante en que cesan las apuestas:
  $$Q_w = \frac{B_{\text{neta}}}{T_w} = \frac{0.90 \times B}{T_w}$$
  Por esta razón, **el premio final solo se conoce cuando se cierran las apuestas** y se certifica el ganador oficial (PDF pág. 3).

### 2. Cuotas Estimadas en Vivo (PDF pág. 3)
- Mientras la carrera permanece en estado `ABIERTA`, la plataforma calcula y expone a los apostadores una **cuota estimada** para cada mediano $m$:
  $$Q_{\text{estimada}}(m) = \frac{0.90 \times B_{\text{actual}}}{T_m}$$
  donde $T_m$ es el total acumulado sobre el mediano $m$ hasta ese instante.
- Estas cuotas varían dinámicamente con cada nueva apuesta que ingresa.
- **Naturaleza informativa:** La cuota mostrada es estrictamente una estimación proyectada; no constituye una cuota fija garantizada al momento de apostar.

### 3. Ciclo de Vida Formal de una Carrera (PDF pág. 3)
El PDF define formalmente una máquina de estados determinista para cada carrera:

```text
  [PROGRAMADA] ──► [ABIERTA] ──► [CERRADA] ──► [EN_CURSO] ──► [FINALIZADA] ──► [LIQUIDADA]
        │              │             │              │
        └──────────────┴─────────────┴──────────────┴──────────────► [CANCELADA]
                                                                        (Devolución 100%)
```

#### Transiciones y Efectos de Estado:
1. `PROGRAMADA`: Carrera configurada con fecha, hora, pista, distancia y participantes. No admite apuestas.
2. `ABIERTA`: Ventana formal de admisión de apuestas. Se calculan cuotas estimadas.
3. `CERRADA`: Cese estricto e irrevocable de recepción de apuestas al llegar la hora de inicio (reloj del servidor). Bolsa común fijada.
4. `EN_CURSO`: Competencia deportiva en desarrollo. Las apuestas permanecen congeladas y selladas.
5. `FINALIZADA`: Conclusión de la carrera en pista. El sistema queda a la espera de la recepción del resultado oficial verificado.
6. `LIQUIDADA`: Resultado oficial procesado, ganadores identificados, premios calculados y acreditados en las billeteras de los usuarios.
7. `CANCELADA`: Transición de excepción posible **desde cualquier estado anterior a `FINALIZADA`**. Provoca la devolución íntegra (100%) de los montos apostados a todos los usuarios participantes.

### 4. Regla de Múltiples Apuestas por Usuario (PDF pág. 3)
- Un usuario tiene autorización expresa de emitir múltiples apuestas en la misma carrera.
- Puede apostar varias veces por el mismo mediano (ej. dos apuestas de 100 EIA Coins separadas) o diversificar apostando a distintos medianos.
- **Distinción arquitectónica fundamental:** Un nuevo envío de apuesta con un nuevo identificador de intención constituye una operación de negocio legítima y debe ser procesada. La deduplicación debe actuar estrictamente sobre reintentos de una misma transacción (`idempotency_key` u `operation_id`).

---

## P1-1.3: PARÁMETROS CRÍTICOS DE CARGA, LATENCIA, DURABILIDAD, LIQUIDACIÓN Y RETENCIÓN

Con base en la sección *"El problema de las cargas masivas"* (PDF pág. 8) y la tabla de *"Supuestos de diseño"* (PDF págs. 8-9), se consolidan los parámetros cuantitativos obligatorios del sistema:

| Parámetro / Dimensión | Criterio Cuantitativo Explícito | Requisito Fuente | Implicación de Diseño Arquitectónico |
| :--- | :--- | :--- | :--- |
| **Usuarios Concurrentes (Normal)** | 500 usuarios conectados simultáneamente | PDF pág. 8 | Carga base manejable con recursos mínimos y configuración liviana. |
| **Usuarios Concurrentes (Pico Máximo)** | 100.000 usuarios conectados en la final de la Copa Intersemestral | PDF pág. 8 | Requiere escalamiento horizontal elástico en capa de entrada y lectura eficiente. |
| **Pico de Transacciones de Apuesta** | **10.000 apuestas por segundo** sostenidas durante los 30 segundos previos al cierre | PDF pág. 8 | Carga transaccional crítica: 300.000 apuestas en 30 segundos. Demanda bufferizado, procesamiento eficiente y particionamiento. |
| **Latencia de Respuesta al Apostar** | **< 1 segundo** para notificar al usuario si la apuesta fue aceptada o rechazada | PDF pág. 9 | Límite estricto de latencia percibida por el usuario. Prohíbe arquitecturas de espera indefinida. |
| **Durabilidad y Pérdida de Datos** | **Cero tolerancia a pérdida:** ninguna apuesta aceptada ni movimiento de billetera puede perderse | PDF pág. 9 | Persistencia con confirmación atómica y write-ahead log o almacenamiento con réplicas durables. |
| **Tiempo Máximo de Liquidación** | **< 15 minutos** para pagar todos los premios tras la publicación del resultado oficial | PDF pág. 9 | Liquidación de más de 1.000.000 de apuestas (PDF pág. 6) distribuida mediante procesamiento por lotes/paralelo; prohíbe peticiones síncronas HTTP masivas monolíticas. |
| **Frescura de Estadísticas** | Métricas operativas con tolerancia de minutos de retraso; reportes premium hasta un día | PDF pág. 9 | Desacoplamiento analítico: permite procesamiento en streaming/batch fuera de la ruta crítica transaccional. |
| **Retención de Auditoría** | Conservación inalterable durante **al menos 5 años** | PDF pág. 9 | Almacenamiento histórico inmutable, optimizado para consulta de solo lectura por auditores. |

---

## P1-1.4: INVARIANTES DEL SISTEMA (SALDO, DUPLICACIÓN, CIERRE Y AUDITORÍA)

Los invariantes son condiciones formales de corrección que el sistema jamás puede violar bajo ninguna circunstancia de carga, concurrencia o fallo:

1. **Invariante de Moneda y No Doble Gasto (PDF pág. 6, 15):**
   - *Regla:* Un EIA Coin no puede ser gastado dos veces.
   - *Invariante:* $\text{Saldo}(u) \ge 0 \quad \forall u \in \text{Usuarios}$. El saldo contable de un usuario nunca puede ser negativo, aun cuando envíe múltiples apuestas en paralelo desde pestañas o conexiones simultáneas.
2. **Invariante de Cierre Temporal Estricto (PDF pág. 3, 5, 8, 9, 15):**
   - *Regla:* Cierre según reloj del servidor a la hora programada $T_{\text{inicio}}$.
   - *Invariante:* Si $t_{\text{recepción}}(\text{apuesta}) \ge T_{\text{inicio}}$, entonces $\text{Estado}(\text{apuesta}) = \text{RECHAZADA}$. Ninguna apuesta puede ser admitida en la bolsa mutua después del corte del servidor, sin importar cuándo la despachó el cliente.
3. **Invariante de Integridad Pari-Mutuel (PDF pág. 3):**
   - *Regla:* Conservación matemática estricta de la bolsa.
   - *Invariante:* $\sum \text{Premios Acreditados} + \text{Comisión Casa (10%)} = B_{\text{total}}$. El sistema no puede emitir premios que superen el fondo recaudado ni retener más del porcentaje establecido.
4. **Invariante de No Duplicación por Idempotencia (PDF pág. 9, 15):**
   - *Regla:* Pulsaciones múltiples ("APOSTAR" repetido 4 veces) no multiplican el débito ni la apuesta.
   - *Invariante:* $\forall \text{operación } op$, el efecto sobre la billetera y sobre las apuestas aceptadas debe ocurrir exactamente una vez para una misma clave lógica de idempotencia:
     $$f(f(op)) = f(op)$$
5. **Invariante de Registro Inmutable y Solo Lectura en Auditoría (PDF pág. 7, 8):**
   - *Regla:* Trazabilidad absoluta de eventos contables y de resultados.
   - *Invariante:* Toda mutación sobre saldos, creación de apuestas, cambios de estado de carreras o resultados genera un registro inmutable.
   - *Aclaración conceptual:*
     - **Append-only:** Propiedad estructural del modelo de datos donde se permite insertar nuevos registros cronológicos de eventos sin modificar ni sobrescribir los registros preexistentes.
     - **Solo lectura:** Política de permisos y control de acceso asignada al rol Auditor en el plano de autorización.
     - La protección física y lógica efectiva contra alteraciones (como firmas criptográficas, inmutabilidad a nivel de almacenamiento o políticas WORM) se diseñará y justificará formalmente en las etapas de persistencia y seguridad.

---

## P1-1.5: IDENTIFICACIÓN DE AMBIGÜEDADES, PREGUNTAS ABIERTAS Y RIESGOS TÉCNICOS

Para preservar la pureza metodológica, se formaliza la clasificación de elementos no definidos en el PDF:

| Código | Categoría | Descripción | Impacto en el Diseño | Propuesta o Estrategia de Resolución |
| :--- | :--- | :--- | :--- | :--- |
| **P1-PA-001** | Pregunta Abierta | **Política de Redondeo y Remanentes de la Bolsa:** Al dividir $0.90 \times B$ entre las apuestas ganadoras, pueden generarse fracciones indivisibles de EIA Coins. | Posible descuadre contable si no se especifica el manejo de decimales. | **Propuesta técnica para P1-5:** Redondeo al entero inferior (*floor*) de cada premio individual y acumulación del residuo fraccionario en la cuenta de la casa o fondo de reserva del torneo. |
| **P1-PA-002** | Pregunta Abierta | **Escenario sin Ganadores:** El PDF no estipula el destino del 90% de la bolsa si ningún apostador eligió al mediano que cruzó la meta en primer lugar. | Vacío de negocio sobre retención o devolución. | **Propuesta técnica para P1-5:** Devolución íntegra (100%) a los apostadores participantes en esa carrera o acumulación (*rollover*) para la siguiente carrera. Se presentará a elección del usuario en P1-5. |
| **P1-RIE-001** | Riesgo / Desafío Técnico | **Tensión Latencia vs Concurrencia Extrema:** Responder en menos de 1 segundo mientras ingresan 10.000 apuestas/s en 30 segundos. | Riesgo de contención en base de datos al validar saldo y debitar bajo concurrencia. | Mitigación en P1-3, P1-5 y P1-6 mediante particionamiento por usuario, estructuras en memoria para validación rápida y aislamiento de colas. |
| **P1-RIE-002** | Riesgo de Conectividad | **Incertidumbre de Red en el Cliente:** Un timeout de red no significa que la apuesta no fue procesada. | Riesgo de que el usuario reintente creyendo que falló. | Mitigación mediante `idempotency-key` obligatoria generada por el cliente antes de despachar la solicitud. |
