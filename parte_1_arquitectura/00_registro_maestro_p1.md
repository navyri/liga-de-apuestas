# REGISTRO MAESTRO P1 — LIGA DE CARRERAS DE MEDIANOS EIA
**Empresa:** Salchipapa Maker Racing S.A.S.  
**Caso Académico:** La Gran Liga de Apuestas de Medianos EIA  
**Fuente principal:** `Trabajo de Arquitectura de Software.pdf` (Universidad EIA)  
**Alcance de esta parte:** Exclusivamente PARTE 1 (Diseño y justificación arquitectónica. Prohibida la implementación).

---

## 1. POLÍTICA DE AUTONOMÍA Y CONTROL DE PROGRESO

### Mecánica de Aprobaciones y Autonomía
- **Tareas documentales rutinarias:** Pueden transicionar a `[x]` mediante verificación autónoma cuando estén elaboradas, revisadas exhaustivamente contra el PDF y mantengan coherencia con las decisiones vigentes.
- **Decisiones arquitectónicas críticas:** Requieren consulta y aprobación explícita del usuario antes de cerrarse (estilo arquitectónico, división principal de servicios, elección de brokers RabbitMQ/Kafka, políticas contables de redondeo/sin ganadores, estrategias críticas de consistencia y resolución de contradicciones reales).
- **Distinción de estados:**
  - `[ ]` Pendiente.
  - `[~]` En progreso o pendiente de una decisión/verificación necesaria.
  - `[x]` Completado y verificado dentro del alcance (se registra si el cierre fue por *revisión autónoma* o por *aprobación del usuario*).
  - `[!]` Bloqueado o requiere revisión.
- **Separación de planos:** Se mantiene estricta diferenciación entre contenido elaborado, contenido verificado, decisión aprobada, archivo guardado en disco, commit creado en Git y push completado al remoto.

---

## 2. CHECKLIST MAESTRO DE CONTROL DE PROGRESO

### ETAPA P1-0 — Lectura y organización
- [x] **P1-0.1** Leer el PDF completo. *(Leído y verificado; completado y aprobado)*.
- [x] **P1-0.2** Extraer entregables, restricciones y rúbrica. *(Elaborado con correcciones; completado y aprobado)*.
- [x] **P1-0.3** Inicializar registro maestro y matriz de trazabilidad. *(Elaborado con correcciones; completado y aprobado)*.
- [x] **P1-0.4** Aprobar plan y organización documental. *(Elaborado con correcciones; completado y aprobado)*.

### ETAPA P1-1 — Negocio y requisitos
- [x] **P1-1.1** Actores, roles y capacidades. *(Completado y aprobado por el usuario)*.
- [x] **P1-1.2** Reglas del negocio y ciclo de carrera. *(Completado y verificado por revisión autónoma)*.
- [x] **P1-1.3** Carga, latencia, durabilidad, liquidación y retención. *(Completado y verificado por revisión autónoma)*.
- [x] **P1-1.4** Invariantes de saldo, duplicación, cierre y auditoría. *(Completado y verificado por revisión autónoma)*.
- [x] **P1-1.5** Ambigüedades y supuestos. *(Completado y verificado por revisión autónoma)*.

### ETAPA P1-2 — Arquitectura y componentes
- [x] **P1-2.1** Comparar estilos arquitectónicos. *(Completado y consolidado)*.
- [x] **P1-2.2** Elegir estilo y descartar justificadamente al menos dos alternativas. *(Aprobado formalmente por el usuario: P1-DEC-001)*.
- [x] **P1-2.3** Definir responsabilidades y límites. *(Completado y verificado por revisión autónoma)*.
- [x] **P1-2.4** Distinguir módulos, despliegues y propiedad de datos. *(Completado y verificado por revisión autónoma)*.
- [x] **P1-2.5** Definir escalamiento independiente. *(Completado y verificado por revisión autónoma)*.

### ETAPA P1-3 — Flujo crítico y comunicación síncrona
- [x] **P1-3.1** Flujo completo de aceptación/rechazo de apuesta. *(Completado y verificado por revisión autónoma)*.
- [x] **P1-3.2** Coherencia entre apuesta y descuento. *(Completado y verificado por revisión autónoma)*.
- [x] **P1-3.3** Validaciones y cierre. *(Completado y verificado por revisión autónoma)*.
- [x] **P1-3.4** Tabla síncrona exigida. *(Completado y verificado por revisión autónoma)*.
- [x] **P1-3.5** Timeouts, reintentos y respuestas inciertas. *(Completado y verificado por revisión autónoma)*.

### ETAPA P1-4 — Mensajería
- [x] **P1-4.1** Comparar RabbitMQ, Kafka, ambos o ninguno. *(Completado y consolidado)*.
- [x] **P1-4.2** Aprobar elección. *(Aprobado formalmente por el usuario: P1-DEC-002)*.
- [x] **P1-4.3** Definir eventos en un único idioma. *(Completado en español formal PascalCase)*.
- [x] **P1-4.4** Tabla de productores, consumidores, tecnología y claves. *(Completado y consolidado)*.
- [x] **P1-4.5** Contenido mínimo y versiones. *(Completado y consolidado)*.
- [x] **P1-4.6** Topología de mensajería. *(Completado y consolidado con particionamiento de liquidación)*.
- [x] **P1-4.7** Reintentos, confirmaciones, duplicados y fallidos. *(Completado y consolidado con DLT e idempotencia)*.
- [x] **P1-4.8** Publicación confiable entre persistencia y mensajería. *(Completado con Transactional Outbox)*.

### ETAPA P1-5 — Datos e idempotencia
- [~] **P1-5.1** Almacenamiento y propiedad. *(Elaborado en P1-ART-006)*.
- [~] **P1-5.2** Consistencia fuerte y eventual. *(Elaborado en P1-ART-006)*.
- [~] **P1-5.3** Concurrencia y prevención de saldo negativo. *(Elaborado en P1-ART-006)*.
- [~] **P1-5.4** Idempotencia en al menos tres operaciones. *(Elaborado en P1-ART-006)*.
- [~] **P1-5.5** Reintentos frente a apuestas legítimas nuevas. *(Elaborado en P1-ART-006)*.
- [~] **P1-5.6** Premios, comisión y devoluciones. *(Elaborado en P1-ART-006)*.
- [~] **P1-5.7** Supuestos de redondeo y ausencia de ganadores. *(Pendiente de decisión del usuario: P1-PA-001 y P1-PA-002)*.
- [~] **P1-5.8** Histórico, analítica y auditoría de cinco años. *(Elaborado en P1-ART-006)*.
- [~] **P1-5.9** Justificar transacciones, outbox o sagas donde se necesiten. *(Elaborado en P1-ART-006)*.

### ETAPA P1-6 — Escalabilidad y fallos
- [ ] **P1-6.1** Analizar 100.000 usuarios y 10.000 apuestas/s durante 30 segundos.
- [ ] **P1-6.2** Cuellos de botella y escalamiento.
- [ ] **P1-6.3** Respuesta en menos de un segundo.
- [ ] **P1-6.4** Impedir aceptaciones fuera del cierre.
- [ ] **P1-6.5** Premios en menos de 15 minutos.
- [ ] **P1-6.6** Durabilidad y recuperación.
- [ ] **P1-6.7** Caída de notificaciones.
- [ ] **P1-6.8** Caída de billetera o equivalente.
- [ ] **P1-6.9** Decidir si abordaremos la corrección opcional de resultados.
- [ ] **P1-6.10** Plan conceptual de métricas y validación.

### ETAPA P1-7 — Seguridad y costos
- [ ] **P1-7.1** Autenticación, autorización y roles.
- [ ] **P1-7.2** APIs, bots y límites de tasa.
- [ ] **P1-7.3** Cifrado y credenciales.
- [ ] **P1-7.4** Operaciones administrativas y auditoría.
- [ ] **P1-7.5** Componentes públicos y privados.
- [ ] **P1-7.6** Infraestructura y servicios administrados.
- [ ] **P1-7.7** Justificación de costos y complejidad.

### ETAPA P1-8 — Diagramas y ADR
- [ ] **P1-8.1** Diagrama general.
- [ ] **P1-8.2** Diferenciación síncrona/asíncrona.
- [ ] **P1-8.3** Secuencia completa de apuesta y descuento.
- [ ] **P1-8.4** Diagrama de mensajería.
- [ ] **P1-8.5** ADR 1.
- [ ] **P1-8.6** ADR 2.
- [ ] **P1-8.7** ADR 3.
- [ ] **P1-8.8** Revisión cruzada de artefactos.

### ETAPA P1-9 — Entrega
- [ ] **P1-9.1** Arquitectura que implementaríamos hoy.
- [ ] **P1-9.2** Evolución ante crecimiento de 100 veces.
- [ ] **P1-9.3** Conclusiones.
- [ ] **P1-9.4** Presentación completa de máximo 20 diapositivas.
- [ ] **P1-9.5** Notas de sustentación.
- [ ] **P1-9.6** Verificar los 16 puntos del entregable.
- [ ] **P1-9.7** Revisar rúbrica.

### ETAPA P1-10 — Sustentación
- [ ] **P1-10.1** Preguntas y respuestas.
- [ ] **P1-10.2** Defensa de decisiones y compromisos.
- [ ] **P1-10.3** Cambio de requisitos: apuestas en vivo.
- [ ] **P1-10.4** Revisión de comprensión conmigo.

---

## 2. REGISTRO DE DECISIONES ARQUITECTÓNICAS (ADR) Y DECISIONES TÉCNICAS
- **P1-DEC-001 (Aprobada por el usuario):** Adopción de la **Arquitectura Híbrida** (Núcleo Modular Transaccional para usuarios, medianos, carreras, apuestas y billetera, con servicios/workers desacoplados para notificaciones, analítica y liquidación masiva). Descarte formal de Microservicios Puros y Monolito Tradicional. Formalizada en `P1-ADR-001`.
- **P1-DEC-002 (Aprobada por el usuario):** Selección de **Apache Kafka como Broker Único** de mensajería y streaming de eventos. Descarte de RabbitMQ como broker único y de la solución dual (ambos). Adopción del patrón Transactional Outbox para publicación confiable y particionamiento por `race_id` y `user_id`. Formalizada en `P1-ADR-002`.

---

## 3. HECHOS EXPLÍCITOS, SUPUESTOS, PREGUNTAS ABIERTAS Y RIESGOS TÉCNICOS

### Hechos y Condiciones Explícitas (Antes listados preliminarmente como supuestos)
- **P1-HEC-001 (Explícito, antes P1-SUP-001):** *Naturaleza de la moneda virtual:* Los *EIA Coins* son créditos ficticios del enunciado, no tienen valor monetario, no se compran ni se canjean por dinero real (Fuente: PDF, pág. 1).
- **P1-HEC-002 (Explícito, antes P1-SUP-002):** *Condición temporal de exposición:* La fecha de exposición está fijada para el 4 y 5 de noviembre, sin año explícito en el documento (Fuente: PDF, pág. 19).

### Supuestos Propuestos (Pendientes de aprobación)
- *Ningún supuesto metodológico adicional propuesto en esta etapa.*

### Preguntas Abiertas de Negocio (Pendientes de definición en etapas correspondientes)
- **P1-PA-001 (Pregunta abierta, antes P1-SUP-003):** *Política de redondeo y remanentes:* El PDF no define decimales ni el manejo de fracciones sobrantes al repartir el 90% de la bolsa; se formulará una propuesta técnica/contable concreta en P1-5.
- **P1-PA-002 (Pregunta abierta, antes P1-SUP-004):** *Ausencia de ganadores:* El PDF no especifica el destino de la bolsa si ningún usuario apostó al mediano ganador; se planteará una política explícita en P1-5 (ej. reembolso del 90% a apostadores o acumulación).

### Riesgos y Desafíos Técnicos Identificados
- **P1-RIE-001 (Desafío de rendimiento y concurrencia, antes clasificado preliminarmente como P1-CON-001):** *Tensión entre latencia estricta (< 1 s) y pico masivo (10.000 apuestas/s en 30 s previos al cierre).* Representa un desafío central de dimensionamiento, particionamiento y consistencia transaccional sin colapsar el almacenamiento ni violar el límite temporal; no constituye una contradicción lógica demostrada del enunciado.

---

## 4. ÍNDICE DE ARTEFACTOS Y VERSIONES

| ID Artefacto | Nombre del Artefacto | Versión | Estado | Descripción / Contenido |
| :--- | :--- | :--- | :--- | :--- |
| **P1-ART-001** | Registro Maestro P1 | v1.7 | `[x]` Aprobado | Checklist maestro, política de autonomía, decisiones aprobadas (P1-DEC-001/002), trazabilidad y bitácora. |
| **P1-ART-002** | Negocio, Actores, Roles y Capacidades | v1.1 | `[x]` Aprobado | Análisis de roles (explícito vs propuesto) y 9 capacidades funcionales de negocio consolidadas. |
| **P1-ART-003** | Arquitectura y Componentes | v1.0 | `[x]` Consolidado | Comparación de estilos, justificación de descartes, desglose de boundaries, módulos vs despliegues y modelo de escalamiento. |
| **P1-ART-004** | Flujo Crítico y Comunicación Síncrona | v1.1 | `[x]` Consolidado | Secuencia integral de apuesta-descuento, consistencia local ACID, tabla síncrona formal y protocolo de incertidumbre de red. |
| **P1-ART-005** | Mensajería y Comunicación Asíncrona | v1.0 | `[x]` Consolidado | Comparativa de brokers, catálogo canónico en español, tabla de eventos, topología de tópicos, particionamiento de liquidación y Transactional Outbox. |
| **P1-ART-006** | Datos, Persistencia e Idempotencia | v0.1 | `[~]` Elaborado | Esquema OLTP vs OLAP, consistencia fuerte vs eventual, bloqueo de billetera, 3 casos de idempotencia y propuestas de redondeo/sin ganadores. |
| **P1-ADR-001** | ADR-001: Estilo Arquitectónico | v1.0 | `[x]` Aprobado | Registro formal de decisión arquitectónica para la adopción de la Arquitectura Híbrida y descarte de alternativas. |
| **P1-ADR-002** | ADR-002: Broker de Mensajería | v1.0 | `[x]` Aprobado | Registro formal de decisión arquitectónica para la selección de Apache Kafka como broker único y patrón Transactional Outbox. |

---

## 5. MATRIZ DE TRAZABILIDAD (Requisito → Decisión/Mecanismo → Artefacto → Diapositiva prevista → Estado)

| ID Requisito | Descripción del Requisito | Fuente | Decisión / Mecanismo Técnico | Artefacto Vinculado | Diapositiva Prevista | Estado |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **P1-REQ-001** | **Modelo Pari-Mutuel y Fases:** Bolsa común, comisión del 10% para la casa, cuotas dinámicas estimadas en ventana abierta. La bolsa total y cuota definitiva se fijan estrictamente al cierre. Tras la carrera, al recibir el resultado oficial, se identifican ganadores, se calculan premios proporcionales al monto y se acreditan en billeteras. | PDF pág. 3, 6 | Por definir en P1-2 y P1-5 | `P1-ART-002` (Negocio y Requisitos) | Sección Negocio / Modelo Pari-Mutuel | `[x]` Formalizado en P1-1.2 |
| **P1-REQ-002** | **Cierre Estricto de Apuestas:** Las apuestas se cierran exactamente a la hora de inicio de la carrera según reloj del servidor. Toda apuesta que llegue después del cierre debe rechazarse, aunque el usuario la haya enviado antes. | PDF pág. 3, 5, 8, 9, 15 | Por definir en P1-3 y P1-6 | `P1-ART-002` | Sección Reglas de Negocio / Cierre | `[x]` Formalizado en P1-1.2 y P1-1.4 |
| **P1-REQ-003** | **Ciclo de Vida de Carrera y Reembolsos:** `PROGRAMADA -> ABIERTA -> CERRADA -> EN_CURSO -> FINALIZADA -> LIQUIDADA`. Cancelable antes de `FINALIZADA` con devolución íntegra (100%) a los usuarios. | PDF pág. 3, 6 | Por definir en P1-2 y P1-4 | `P1-ART-002` | Sección Ciclo de Vida | `[x]` Formalizado en P1-1.2 |
| **P1-REQ-004** | **Validaciones Previas de Apuesta:** Comprobar existencia del usuario, carrera abierta, participación del mediano, saldo suficiente de EIA Coins y ausencia de duplicados. | PDF pág. 5 | Por definir en P1-3 | `P1-ART-002` | Sección Flujo de Apuesta | `[x]` Formalizado en P1-1.1 y P1-1.4 |
| **P1-REQ-005** | **Invariante de Billetera y Concurrencia:** Prohibición absoluta de doble gasto de los mismos EIA Coins y de saldo negativo, incluso si el usuario envía múltiples apuestas simultáneas. | PDF pág. 6, 15 | Por definir en P1-5 y P1-6 | `P1-ART-002` | Sección Invariantes / Billetera | `[x]` Formalizado en P1-1.4 |
| **P1-REQ-006** | **Carga Masiva:** Soportar 500 usuarios normales; 100.000 concurrentes en la final; ráfaga de 10.000 apuestas/s en los 30 s previos al cierre. | PDF pág. 8, 15 | Por definir en P1-6 | `P1-ART-002` | Sección Cargas y Concurrencia | `[x]` Formalizado en P1-1.3 |
| **P1-REQ-007** | **Latencia de Respuesta al Apostar:** El usuario debe saber en menos de 1 segundo si su apuesta fue aceptada o rechazada. El mecanismo técnico (síncrono/asíncrono) se justificará en el diseño. | PDF pág. 9, 15 | Por definir en P1-3 y P1-6 | `P1-ART-002` | Sección Atributos de Calidad | `[x]` Formalizado en P1-1.3 |
| **P1-REQ-008** | **Durabilidad Absoluta:** Pérdida cero de apuestas aceptadas y de movimientos de billetera ante cualquier falla. | PDF pág. 9, 15 | Por definir en P1-5 y P1-6 | `P1-ART-002` | Sección Atributos de Calidad | `[x]` Formalizado en P1-1.3 |
| **P1-REQ-009** | **Plazo de Liquidación de Premios:** Todos los premios pagados en menos de 15 minutos tras el resultado oficial, incluso acumulando más de un millón de apuestas (sin procesarlas en una sola petición HTTP). | PDF pág. 6, 9 | Por definir en P1-4, P1-5 y P1-6 | `P1-ART-002` | Sección Liquidación Masiva | `[x]` Formalizado en P1-1.3 |
| **P1-REQ-010** | **Retención y Auditoría:** Conservar registro inalterable de apuestas, billetera, premios y resultados por al menos 5 años. Rol auditor con permisos exclusivos de solo lectura. Reconstrucción exacta de cálculo de premios. | PDF pág. 7, 8, 9 | Por definir en P1-5 y P1-7 | `P1-ART-002` | Sección Auditoría / Invariantes | `[x]` Formalizado en P1-1.1, P1-1.3 y P1-1.4 |
| **P1-REQ-011** | **Tolerancia y Desacoplamiento de Notificaciones:** Una falla en el sistema de notificaciones no debe impedir el registro ni aceptación de una apuesta. | PDF pág. 7, 16 | Por definir en P1-4 y P1-6 | `P1-ART-002` | Sección Desacoplamiento / Fallos | `[x]` Formalizado en P1-1.1 |
| **P1-REQ-012** | **Seguridad y Control de Acceso:** 4 roles explícitos (apostador, operador de carrera, administrador, auditor). Protección de credenciales/datos sensibles, rate limiting y anti-bot. Separación estricta entre componentes públicos y privados. | PDF pág. 4, 7, 12 | Por definir en P1-7 | `P1-ART-002` | Sección Seguridad y Roles | `[x]` Formalizado en P1-1.1 |
| **P1-REQ-013** | **Múltiples Apuestas Legítimas vs. Idempotencia:** Un usuario puede apostar varias veces en la misma carrera (incluso por medianos distintos). Los mecanismos de idempotencia deben distinguir reintentos por fallos de red de nuevas apuestas legítimas. | PDF pág. 3, 9, 15 | Por definir en P1-3 y P1-5 | `P1-ART-002` | Sección Reglas de Apuestas | `[x]` Formalizado en P1-1.2 y P1-1.4 |
| **P1-REQ-014** | **Restricción de Complejidad y Costo:** Regla directiva de Dyllan ("no pagar infraestructura de Netflix para una carrera de cinco medianos"). Justificar servicios mínimos, infraestructura compartida y servicios administrados. | PDF pág. 12, 13, 19, 20 | Por definir en P1-2 y P1-7 | `P1-ART-001` / `P1-ART-002` | Sección Costos y Gobernanza | `[x]` Formalizado en P1-1.1 |
| **P1-REQ-015** | **Condiciones Académicas de Entrega y Evaluación:** Grupos de máximo 3 estudiantes; exposición el 4 y 5 de noviembre; presentación de máximo 20 diapositivas; uso de IA generativa permitido bajo estricta comprensión y defensa individual de cada decisión; sustentación con cambio de requisitos en vivo. | PDF pág. 19 | Por definir en P1-9 y P1-10 | `P1-ART-001` | Introducción / Metodología | `[x]` Formalizado en P1-0 |

---

## 6. BITÁCORA DE TRABAJO
- **2026-10-27 (Sesión Inicial - Paso 1):** Lectura del PDF oficial (20 páginas). Extracción inicial de rúbrica, entregables y requisitos.
- **2026-10-27 (Sesión Inicial - Paso 2):** Ajustes a partir de la revisión del usuario:
  1. Corrección de `P1-REQ-001` para separar cierre de bolsa, llegada de resultado oficial y posterior liquidación.
  2. Desclasificación de la comunicación síncrona como imposición en `P1-REQ-007` (se definirá en diseño).
  3. Incorporación formal de `P1-REQ-013` (múltiples apuestas legítimas vs idempotencia) y `P1-REQ-015` (condiciones académicas completas).
  4. Delimitación de fuentes de restricciones: aclarado origen metodológico del usuario (separación P1/P2 y Git opcional) vs exigencias del PDF.
  5. Creación del archivo físico real del registro maestro en disco.
- **2026-10-27 (Sesión Inicial - Paso 4):** Reclasificación en el Registro Maestro: `P1-SUP-001/002` a hechos explícitos (`P1-HEC-001/002`), `P1-SUP-003/004` a preguntas abiertas (`P1-PA-001/002`), y `P1-CON-001` a desafío técnico (`P1-RIE-001`). Corrección y verificación formal del recuento exacto de tareas (72 totales: 4 aprobadas, 1 en progreso, 67 pendientes).
- **2026-10-27 (Sesión Inicial - Paso 5):** Aprobación del usuario para P1-1.1 y cambio a política de autonomía con versionado real en GitHub. Inicialización del repositorio local en `main`, configuración del remoto oficial `https://github.com/navyri/liga-de-apuestas.git`, creación de `README.md` y `.gitignore`. Commit inicial `3b58a4b` publicado exitosamente.
- **2026-10-27 (Sesión Inicial - Paso 6):** Desarrollo y revisión autónoma de los subpasos P1-1.2, P1-1.3, P1-1.4 y P1-1.5 en `P1-ART-002 v1.1`. Cierre formal de la Etapa P1-1 (5/5 tareas en `[x]`). Actualización de matriz de trazabilidad y conteos de progreso.
- **2026-10-27 (Sesión Inicial - Paso 7):** Elaboración de `P1-2.1` en `P1-ART-003 v0.1` (`02_arquitectura_y_componentes.md`): comparación de 4 estilos frente a coherencia, cierre, latencia, ráfaga de 10k ops/s, liquidación y costos. Actualización del README principal con identidad visual adaptada, badges reales e índice completo.
- **2026-10-27 (Sesión Inicial - Paso 8):** Aprobación del usuario para la Arquitectura Híbrida (`P1-DEC-001`). Incorporación de precisiones: apuesta-descuento en transacción local, matización de garantías de rendimiento, reajuste de motivos de descarte de microservicios, e inclusión explícita de Resultados, Liquidación, Devoluciones y Auditoría. Elaboración y verificación de `P1-2.3`, `P1-2.4` y `P1-2.5`. Redacción de `P1-ADR-001`. Cierre formal de la Etapa P1-2 (5/5 tareas en `[x]`).
- **2026-10-27 (Sesión Inicial - Paso 9):** Elaboración y consolidación autónoma de la Etapa P1-3 en `P1-ART-004 v1.0` (`03_flujo_critico_y_comunicacion.md`): secuencia atómica de apuesta y débito, tabla síncrona formal (Decisión 3), validación atómica de hora de cierre y protocolo de incertidumbre de red / timeouts con idempotency keys. Cierre de P1-3 (5/5 tareas en `[x]`).
- **2026-10-27 (Sesión Inicial - Paso 10):** Elaboración de `P1-4.1` en `P1-ART-005 v0.1` (`04_mensajeria_y_eventos.md`): comparación técnica de RabbitMQ, Kafka, Ambos y Ninguno frente al pico de 10k eventos/s, múltiples consumidores independientes y reproducción para auditoría. Preparación para la consulta de la Decisión 5 (`P1-4.2`).
- **2026-10-27 (Sesión Inicial - Paso 11):** Aprobación del usuario para Apache Kafka (`P1-DEC-002`) con precisiones de descarte proporcional, matización de tasas de eventos vs apuestas, delimitación de Kafka frente a auditoría a 5 años e idempotencia en replay. Ajuste en `P1-ART-004 v1.1` sobre estados de incertidumbre vs garantías de latencia. Consolidación de `P1-4.3` a `P1-4.8` en `P1-ART-005 v1.0` (eventos canónicos en español, tabla formal, topología con particionamiento de liquidación y Transactional Outbox). Redacción de `P1-ADR-002`. Cierre formal de la Etapa P1-4 (8/8 tareas en `[x]`).
- **2026-10-27 (Sesión Inicial - Paso 12):** Elaboración técnica integral de la Etapa P1-5 en `P1-ART-006 v0.1` (`05_datos_e_idempotencia.md`): esquema de almacenamiento (OLTP en núcleo, OLAP analítico, WORM auditoría), consistencia fuerte vs eventual, prevención de saldo negativo con bloqueo de fila `FOR UPDATE`, idempotencia en 3 operaciones críticas, deduplicación de eventos y formulación de opciones para redondeo (`P1-PA-001`) y ausencia de ganadores (`P1-PA-002`).

---

## 7. ESTADO DOCUMENTAL Y DE CONTROL DE VERSIONES (GIT)

### Distinción de Archivos y Artefactos

#### Archivos Reales Creados en el Workspace:
- `parte_1_arquitectura/00_registro_maestro_p1.md` (Contiene `P1-ART-001` v0.2).

#### Archivos Previstos (Estructura proyectada a crear según se apruebe cada etapa):
```text
parte_1_arquitectura/
├── 00_registro_maestro_p1.md              # [CREADO] Registro Maestro y Matriz de Trazabilidad
├── 01_requisitos_y_negocio.md             # [PREVISTO] Etapa P1-1: Análisis detallado de negocio
├── 02_arquitectura_y_componentes.md       # [PREVISTO] Etapa P1-2: Estilo y división de servicios
├── 03_flujo_critico_y_comunicacion.md     # [PREVISTO] Etapa P1-3: Flujo de apuesta y tabla síncrona
├── 04_mensajeria_y_eventos.md             # [PREVISTO] Etapa P1-4: Broker, tabla de eventos y topología
├── 05_datos_e_idempotencia.md             # [PREVISTO] Etapa P1-5: Persistencia, consistencia y transacciones
├── 06_escalabilidad_y_fallos.md           # [PREVISTO] Etapa P1-6: Cargas masivas y casos de falla
├── 07_seguridad_y_costos.md               # [PREVISTO] Etapa P1-7: RBAC, zonas de red y costos
├── 08_diagramas_y_adrs/                   # [PREVISTO] Etapa P1-8: Diagramas Mermaid y ADRs
│   ├── diagrama_general.md
│   ├── diagrama_secuencia_apuesta.md
│   ├── topologia_mensajeria.md
│   ├── ADR-001_tema_tentativo_estilo.md
│   ├── ADR-002_tema_tentativo_mensajeria.md
│   └── ADR-003_tema_tentativo_consistencia.md
├── 09_presentacion_diapositivas.md        # [PREVISTO] Etapa P1-9: Presentación (máx. 20 diapositivas)
└── 10_guia_sustentacion.md                # [PREVISTO] Etapa P1-10: Banco de preguntas y cambio en vivo
```
*(Nota: Los títulos de los 3 ADR se mantienen como temas tentativos; el archivo de diapositivas se denomina `09_presentacion_diapositivas.md` para cumplir la restricción de "máximo 20 diapositivas" sin forzar un número exacto).*

#### Estado de Git:
- **Naturaleza:** Git es una herramienta metodológica opcional para versionar documentación de P1, según instrucciones del usuario (no es exigido por el PDF).
- **Estado actual:** No se han realizado commits ni inicializaciones en este turno. El archivo creado permanece en el sistema de archivos listo para ser versionado cuando el usuario lo determine.
