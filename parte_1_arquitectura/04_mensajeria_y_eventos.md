# ETAPA P1-4: MENSAJERÍA Y COMUNICACIÓN ASÍNCRONA
**Caso:** La Gran Liga de Apuestas de Medianos EIA  
**Organización:** Salchipapa Maker Racing S.A.S.  
**Artefacto:** `P1-ART-005`  
**Versión:** `v0.1` (Borrador técnico para decisión)  
**Estado:** `[~]` Elaborado pendiente de decisión del usuario para P1-4.2 (Decisión 5: RabbitMQ vs. Kafka)  

---

## P1-4.1: COMPARACIÓN TÉCNICA: RABBITMQ, KAFKA, AMBOS O NINGUNO

Para resolver la **Decisión 5** del PDF (págs. 11-12, 14-15), se evalúan las cuatro alternativas de infraestructura de mensajería frente a las características del dominio:

### 1. Perfil del Tráfico Asíncrono del Negocio
- **Eventos Transaccionales de Alto Volumen:** Emisión de eventos de apuestas (`ApuestaRealizada` / `BetPlaced`) a una tasa pico de 10.000 eventos/s durante 30 segundos (300.000 eventos acumulados) y generación masiva de registros diarios para analítica (millones al día).
- **Consumo Múltiple e Independiente:** Un mismo evento de apuesta interesa simultáneamente a:
  - Motor de cálculo de cuotas dinámicas estimadas (en tiempo casi real).
  - Servicio de auditoría y detección de fraudes (detección de anomalías al cierre).
  - Pipeline de analítica y estadísticas (almacén histórico).
  - Servicio de notificaciones al apostador (confirmación push/correo).
- **Procesamiento de Tareas / Tareas en Lotes:** Distribución de trabajos pesados de liquidación masiva de premios (> 1.000.000 apuestas) y dispersión de devoluciones por carreras canceladas.

---

### 2. Análisis Comparativo de las Alternativas

#### A. RabbitMQ Únicamente (Message Broker Basado en Colas y AMQP)
- **Fortalezas:** Excelente para enrutamiento flexible mediante exchanges (direct, topic, fanout), distribución de tareas a workers en competencia (*competing consumers*), gestión de reintentos con colas de cartas muertas (DLQ) y baja sobrecarga operativa base.
- **Limitaciones frente al caso:**
  - En RabbitMQ, una vez que un mensaje es consumido y confirmado (*acknowledged*), se elimina de la cola. No permite retención histórica ni reproducción posterior de eventos (*replay*) para reconstrucción forense o reentrenamiento analítico.
  - El modelo *fan-out* hacia 4 consumidores distintos (notificaciones, analítica, fraude, cuotas) multiplica físicamente las colas y copias de mensajes en disco/RAM. Sostener 10.000 eventos/s multiplicados por 4 consumidores genera 40.000 mensajes/s en el broker, saturando la memoria y provocando contención severa por contrapresión (*backpressure*).

#### B. Apache Kafka Únicamente (Distributed Event Streaming Platform / Commit Log)
- **Fortalezas:**
  - Diseñado como un registro distribuido append-only en disco optimizado para escrituras secuenciales masivas y alto *throughput* (cientos de miles de eventos/s).
  - **Múltiples consumidores independientes sin duplicación física:** Cada consumidor (Analítica, Fraude, Notificaciones, Cuotas) mantiene su propio cursor (*offset*) y lee el mismo log a su propio ritmo sin interferir con los demás.
  - **Retención y reproducción:** Los eventos se conservan según política temporal (ej. 7 días o semanas), permitiendo al servicio de auditoría o analítica retroceder el cursor y reprocesar el histórico ante fallos o recalibración de modelos.
  - **Particionamiento por clave:** Garantiza orden estricto por carrera (`race_id`) o por usuario (`user_id`).
- **Limitaciones frente al caso:**
  - No cuenta nativamente con colas de trabajo con visibilidad temporal individualizada ni reintentos selectivos por mensaje (el reintento requiere tópicos de reintento dedicados tipo *retry-topics* o DLQ topics).
  - Sobrecarga operativa superior si se despliega clúster auto-gestionado completo, aunque mitigable mediante servicios administrados.

#### C. Ambos Brokers (RabbitMQ + Kafka)
- **Enfoque:** Utilizar Kafka como columna vertebral para el flujo de eventos de alta velocidad (apuestas, analítica, auditoría) y RabbitMQ para la orquestación de tareas puntuales de liquidación masiva y reintentos de notificación.
- **Evaluación frente a la Regla de Dyllan:** Exige operar, monitorizar y aprovisionar dos plataformas de mensajería completamente diferentes con curvas de aprendizaje y costos dispares. El PDF advierte expresamente (pág. 15): *"Si utilizan ambos, deberán justificar por qué mantener dos tecnologías diferentes representa una ventaja suficiente para asumir la complejidad adicional"*. Para una liga de medianos, mantener dos clústeres viola el principio de parsimonia arquitectónica.

#### D. Ninguno (Comunicación Directa HTTP/gRPC)
- **Evaluación:** Obligaría al núcleo transaccional a notificar síncronamente por HTTP a analítica, notificaciones y auditoría en cada apuesta. Bajo 10.000 req/s, provocaría el colapso inmediato del sistema por agotamiento de puertos y cascada de fallos. El desacoplamiento asíncrono es estrictamente indispensable.

---

### 3. Matriz Comparativa de Mensajería

| Criterio Técnico | RabbitMQ | Apache Kafka | Ambos (RabbitMQ + Kafka) |
| :--- | :--- | :--- | :--- |
| **Soporte de Pico (10k eventos/s)** | Exigido al límite en ráfaga; riesgo de degradación por consumo de RAM. | Óptimo (escritura secuencial en log en disco con cero copia). | Óptimo en Kafka, pero sobrecargado en RabbitMQ. |
| **Múltiples Consumidores del Mismo Evento** | Requiere duplicar colas (fan-out); multiplica el uso de almacenamiento. | Nativo por diseño (grupos de consumidores sobre el mismo log). | Duplicado innecesariamente. |
| **Reproducción y Reprocesamiento Histórico** | No soportado (los mensajes se eliminan tras el ACK). | Nativo (reproducibilidad por desplazamiento de *offset*). | Disponible solo en el segmento de Kafka. |
| **Complejidad y Costo Operativo (Dyllan)** | Bajo a moderado. | Moderado (óptimo como servicio administrado). | Máximo (injustificado para el tamaño del problema). |

---

### 4. Propuesta de Decisión (P1-4.2)
- **Recomendación técnica:** **Seleccionar Apache Kafka como tecnología única de mensajería y event streaming.**
  - *Justificación:* Resuelve de manera natural el requerimiento explícito del PDF (pág. 11): *"múltiples consumidores interesados en la misma información (Analítica, Fraude, Estadísticas, Auditoría) donde cada consumidor lee el mismo evento de forma independiente y a su propio ritmo"*. Además, permite absorber con holgura los 10.000 eventos/s de la ráfaga mediante particionamiento sin multiplicar el almacenamiento, y habilita la reproducción histórica exigida por la auditoría forense.
  - *Descarte de RabbitMQ y de la solución dual:* Se descarta RabbitMQ como broker principal por su ineficiencia al replicar colas para múltiples consumidores bajo ráfaga y por la imposibilidad de reproducir eventos. Se descarta la solución dual (ambos) para no duplicar costos ni infraestructura operativa, cumpliendo la directriz de Dyllan.
