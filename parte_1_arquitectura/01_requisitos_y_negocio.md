# ETAPA P1-1: ANÁLISIS DE NEGOCIO Y REQUISITOS
**Caso:** La Gran Liga de Apuestas de Medianos EIA  
**Organización:** Salchipapa Maker Racing S.A.S.  
**Artefacto:** `P1-ART-002`  
**Versión:** `v1.0`  
**Estado:** `[x]` Completado y aprobado por el usuario  

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
  El cierre de apuestas está fijado exactamente a la hora de inicio de la carrera según el **reloj del servidor** (PDF pág. 3). **No depende de una orden manual ni de un botón accionado por el Operador de Carrera**. Cualquier solicitud recibida tras la marca de tiempo de cierre del servidor es rechazada irrevocablemente, independientemente de la latencia del cliente o de cuándo fue despachada por el usuario. El mecanismo técnico exacto (programador interno, flags en memoria, checks atómicos en motor de base de datos) se definirá y justificará formalmente en las etapas de diseño.
