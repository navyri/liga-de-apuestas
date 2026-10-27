# ETAPA P1-2: ARQUITECTURA Y COMPONENTES
**Caso:** La Gran Liga de Apuestas de Medianos EIA  
**Organización:** Salchipapa Maker Racing S.A.S.  
**Artefacto:** `P1-ART-003`  
**Versión:** `v0.1` (Borrador técnico para decisión)  
**Estado:** `[~]` Elaborado pendiente de decisión del usuario para P1-2.2  

---

## P1-2.1: COMPARACIÓN TÉCNICA DE ESTILOS ARQUITECTÓNICOS

### 1. Marco Metodológico de Comparación
Para responder a la **Decisión 1** del PDF (pág. 13), se evalúan cuatro estilos arquitectónicos fundamentales:
1. **Monolito Tradicional (Monolito no modular / acoplado):** Todo el sistema se compila, empaqueta y ejecuta como un único artefacto desplegable con acoplamiento interno en código y base de datos compartida.
2. **Monolito Modular:** Sistema estructurado internamente en módulos funcionales con límites estrictos, interfaces públicas bien definidas y bajo acoplamiento en código. Puede desplegarse como un único proceso o replicarse horizontalmente en múltiples instancias idénticas, compartiendo esquemas lógicos o una base de datos centralizada.
3. **Microservicios Puros:** Descomposición total de las 9 capacidades del negocio en servicios autónomos e independientes, cada uno como una unidad de despliegue aislada y con su propia base de datos privada (*database-per-service*).
4. **Arquitectura Híbrida (Monolito Modular Central + Servicios Especializados Desacoplados):** Núcleo transaccional de alta cohesión (carreras, apuestas, billetera) organizado como módulos con boundaries estrictos, complementado con componentes o servicios autónomos extraídos específicamente para cargas con ciclos de vida y perfiles de escalamiento asimétricos (ej. analítica/estadísticas y procesamiento de notificaciones).

> [!IMPORTANT]
> **Distinción Conceptual Clave:**
> - **Módulo Lógico:** Límite de encapsulamiento a nivel de código y lógica de dominio (ej. módulo de billetera, módulo de carreras).
> - **Unidad Desplegable:** Proceso en ejecución independiente en el sistema operativo o contenedor (un monolito modular puede desplegarse en $N$ instancias idénticas detrás de un balanceador de carga; no equivale a "una sola instancia").
> - **Base de Datos:** Almacén de persistencia físico o lógico (instancia de BD, esquema, o réplica). El rendimiento depende del modelo de concurrencia y de datos, no del estilo arquitectónico por sí solo.

---

### 2. Evaluación de los Estilos frente a los Desafíos del Caso

#### A. Coherencia entre Apuesta y Descuento
- **Monolito Tradicional / Monolito Modular:** Permite ejecutar la comprobación de saldo, la deducción de EIA Coins y la inserción de la apuesta dentro de una **transacción ACID local** en la base de datos relacional. Garantiza consistencia fuerte sin necesidad de protocolos de coordinación distribuida (evita fallos de red intermedios entre apuesta y billetera).
- **Microservicios Puros:** Al separar "Apuestas" y "Billetera" en servicios y bases de datos independientes, la operación requiere coordinación distribuida (patrón Saga con compensación o 2PC). Una falla en el servicio de billetera tras registrar la apuesta exige transacciones compensatorias complejas, aumentando el riesgo de inconsistencia temporal o saldo negativo si no se aísla adecuadamente bajo alta concurrencia.
- **Arquitectura Híbrida:** Si las capacidades transaccionales críticas (apuestas y billetera) residen dentro del mismo límite o comparten un mecanismo transaccional atómico local, se preserva la consistencia fuerte ACID para el débito y registro, eliminando la complejidad de sagas en la ruta crítica de 1 segundo.

#### B. Cierre Estricto de Apuestas (según reloj del servidor)
- **Monolito / Monolito Modular:** La validación de tiempo se ejecuta directamente contra la marca temporal del servidor de aplicaciones o el motor de base de datos local en el instante de la transacción: `IF server_time >= race.start_time THEN REJECT`. Cero desfase de red entre servicios para verificar el corte.
- **Microservicios Puros:** Requiere sincronización precisa de relojes (NTP) entre múltiples instancias de servicios distintos o consultas remotas de estado entre el servicio de apuestas y el servicio de carreras, introduciendo latencia de red y riesgo de admitir apuestas desfasadas por retraso en la propagación de eventos de cierre.
- **Arquitectura Híbrida:** El núcleo transaccional valida la regla de corte en memoria o en el registro de carrera local en microsegundos, asegurando el rechazo irrevocable e independiente de intervención humana.

#### C. Pico de 10.000 Apuestas por Segundo durante 30 Segundos (300.000 apuestas)
- **Monolito Tradicional:** Puede escalar horizontalmente sus instancias web/API, pero la base de datos centralizada sufre contención extrema en bloqueos de fila de saldo si muchos usuarios apuestan en paralelo. El acoplamiento interno de código dificulta optimizar la ruta crítica sin afectar el resto del sistema.
- **Monolito Modular:** Puede desplegarse en un grupo escalado de instancias idénticas optimizadas. Los límites de módulos permiten implementar particionamiento lógico o buffers específicos para apuestas. Sin embargo, si todas las capacidades (incluida analítica pesada) comparten el mismo pool de recursos de BD, las consultas complejas pueden canibalizar la capacidad transaccional del pico de apuestas.
- **Microservicios Puros:** Permite escalar masivamente solo el servicio de apuestas. No obstante, si el servicio de apuestas debe consultar síncronamente al servicio de billetera y al de usuarios 10.000 veces por segundo por HTTP/gRPC, se produce una cascada de llamadas de red (10k req/s $\times$ saltos de red = alta latencia y saturación de conexiones distribuidas).
- **Arquitectura Híbrida:** Aísla el pico permitiendo que las unidades que reciben la carga escalen horizontalmente, manteniendo la validación de apuesta y saldo con mínima latencia de red (comunicación in-process o mensajería de alta velocidad) y aislando completamente las cargas pesadas de estadísticas y notificaciones para que no consuman recursos del flujo transaccional.

#### D. Respuesta en Menos de 1 Segundo al Usuario
- **Monolito / Monolito Modular:** Al no requerir saltos de red adicionales entre módulos de negocio para validar usuario, carrera, saldo y apuesta, el tiempo de procesamiento interno es típicamente del orden de decenas de milisegundos ($< 50\text{ ms}$), dejando un amplio margen para la latencia de red del cliente ($< 1\text{ s}$).
- **Microservicios Puros:** Cada salto de red (API Gateway $\to$ Servicio Apuestas $\to$ Servicio Billetera $\to$ Servicio Carreras) agrega serialización, deserialización, latencia de red y riesgo de cola en cada salto. Bajo 10.000 req/s, la amplificación de colas en servicios aguas abajo puede degradar rápidamente la latencia por encima de 1 segundo (problema del eslabón más lento / *tail latency*).
- **Arquitectura Híbrida:** Minimiza los saltos de red en la ruta crítica del usuario a lo estrictamente necesario (API Gateway $\to$ Núcleo de Apuestas/Billetera), resolviendo la aceptación/rechazo en milisegundos y difiriendo el resto (notificaciones, analítica) a procesos asíncronos.

#### E. Liquidación Masiva (< 15 minutos para > 1.000.000 de apuestas)
- **Monolito Tradicional:** Ejecutar el cálculo y actualización de 1 millón de registros dentro del hilo principal del monolito puede bloquear las transacciones operativas y degradar la base de datos.
- **Monolito Modular:** Puede ejecutar un worker en un proceso separado pero reutilizando la lógica del módulo de premios y billetera. Requiere diseñar la liquidación en lotes paralelos (*chunking*).
- **Microservicios Puros:** El servicio de premios debe emitir 1 millón de llamadas HTTP o mensajes individuales al servicio de billetera. Si se hace mediante peticiones HTTP síncronas una por una (desaconsejado explícitamente en el PDF pág. 6), se saturaría la red y se excedería el límite de 15 minutos ($1.000.000 / 900\text{ s} \approx 1.111\text{ ops/s}$ sostenidas de acreditación). Exige mensajería asíncrona particionada.
- **Arquitectura Híbrida:** Permite desacoplar la liquidación mediante un proceso/worker especializado que consume el evento de carrera finalizada, calcula los premios y despacha la acreditación en lotes concurrentes particionados por usuario, cumpliendo holgadamente el plazo de 15 minutos sin impactar las lecturas de los apostadores.

#### F. Fallos, Operación y Costos (Regla de Dyllan: "No infraestructura de Netflix")
- **Monolito Tradicional:** Operación muy económica y simple, pero frágil: una fuga de memoria en analítica o un colapso en el procesamiento de notificaciones puede tumbar todo el sitio.
- **Monolito Modular:** Excelente balance de costos. Infraestructura compartida eficiente (servidores o contenedores estándar, una o dos instancias de BD administradas con réplicas de lectura). Alta mantenibilidad gracias a los límites de código claros.
- **Microservicios Puros:** Costo operativo y financiero desmedido para este caso. 9 microservicios con sus propias bases de datos, service discovery, distributed tracing, API gateways complejos, mTLS y balanceadores violan directamente la restricción de Dyllan (PDF pág. 12, 19, 20: *"crear 42 microservicios, 17 bases de datos... es una excelente manera de conseguir que Dyllan despida al equipo"*).
- **Arquitectura Híbrida:** Cumple estrictamente la regla de costos: consolida la mayoría de las capacidades en un servicio modular desplegable (evitando sobrecostos de múltiples clústeres y bases de datos aisladas), y solo segrega en componentes autónomos lo que estrictamente lo justifica por asimetría de carga o desacoplamiento de fallos (notificaciones y analítica).

---

### 3. Matriz Comparativa Justificada (Sin puntuaciones arbitrarias)

| Criterio de Decisión | Monolito Tradicional | Monolito Modular | Microservicios Puros | Arquitectura Híbrida (Recomendada) |
| :--- | :--- | :--- | :--- | :--- |
| **Coherencia Apuesta-Descuento** | Muy alta (ACID local directa). | Muy alta (ACID local modular). | Baja (requiere transacciones distribuidas o Sagas complejas). | Alta / Muy alta (transacción local en núcleo o mensajería atómica). |
| **Latencia en Ruta Crítica (< 1 s)** | Óptima (cero saltos de red internos). | Óptima (cero saltos de red internos). | Riesgo alto (múltiples saltos de red HTTP/gRPC bajo carga). | Óptima (salto único en borde, procesamiento atómico). |
| **Resiliencia ante Fallos de Notificaciones** | Pobre (falla de notificaciones puede bloquear la petición si no se aísla). | Media/Alta (requiere aislamiento estricto de hilos/colas internas). | Muy alta (aislamiento físico total de procesos y fallas). | Muy alta (componente de notificaciones físicamente desacoplado). |
| **Aislamiento de Analítica (Millones de regs.)** | Muy bajo (consultas pesadas saturan la BD transaccional). | Medio (requiere réplicas de lectura dedicadas). | Total (almacén analítico completamente segregado). | Total (ingesta de eventos hacia almacén analítico especializado). |
| **Costo y Complejidad Operativa (Regla Dyllan)** | Mínimo costo, pero alto riesgo de deuda técnica y bloqueo. | Mínimo a moderado (excelente ratio costo/eficiencia). | Máximo (infraestructura desproporcionada para el problema). | Moderado y controlado (máximo rendimiento sin sobrecosto). |

---

### 4. Propuesta de Decisión y Alternativas Descartadas (Para consulta de aprobación)

#### A. Estilo Recomendado: Arquitectura Híbrida (Monolito Modular Transaccional + Servicios Asíncronos Desacoplados)
- **Núcleo Transaccional Modular (Core Monolith):** Agrupa las capacidades fuertemente cohesivas: *Usuarios/Auth*, *Medianos*, *Carreras*, *Apuestas* y *Billetera*. Se organiza internamente mediante módulos desacoplados con límites estrictos. Maneja la validación y el descuento atómico de EIA Coins sin latencias de red distribuidas, garantizando respuesta en menos de 1 segundo y prevención de saldo negativo.
- **Servicio de Notificaciones Autónomo:** Desacoplado físicamente del flujo de apuestas (PDF pág. 7: *"Una falla en el sistema de notificaciones no debería impedir que una apuesta sea registrada"*). Consume eventos asíncronos y gestiona sus propios reintentos y canales externos (push, correo).
- **Servicio / Pipeline de Analítica y Estadísticas:** Desacoplado físicamente del motor transaccional. Consume eventos de plataforma y alimenta un almacén optimizado para consultas agregadas y reportes premium sin degradar la base de datos de apuestas.
- **Worker de Liquidación Masiva:** Proceso especializado que ejecuta el cálculo y dispersión masiva de premios sin bloquear el tráfico interactivo de los usuarios.

#### B. Alternativas Descartadas Obligatorias (PDF pág. 13)
1. **Descarte de Microservicios Puros (Microservicios de grano fino para cada capacidad):**
   - *Razón técnica:* Introducir 9 microservicios con bases de datos segregadas para un sistema de medianos generaría una sobrecarga innecesaria de red (latencia acumulada de llamadas gRPC/REST) que pondría en grave riesgo la respuesta en menos de 1 segundo bajo 10.000 apuestas/s. Además, exigiría implementar transacciones distribuidas (Sagas) para el débito de saldo y registro de apuesta, elevando el riesgo de condiciones de carrera y saldo negativo. Viola directamente la directriz de costo y sobredimensionamiento de Dyllan (PDF pág. 12, 19, 20).
2. **Descarte del Monolito Tradicional (No modular / monolito clásico enredado):**
   - *Razón técnica:* Carece de límites arquitectónicos formales. La ingesta masiva de analítica diaria (millones de registros) y la generación de reportes competirían por los mismos bloqueos de recursos y memoria que el pico de 10.000 apuestas/s. Asimismo, una falla o lentitud en los proveedores externos de notificaciones (correo/push) podría saturar el pool de conexiones de la aplicación y bloquear la aceptación de apuestas, violando el requisito explícito de desacoplamiento de fallos (PDF pág. 7).
