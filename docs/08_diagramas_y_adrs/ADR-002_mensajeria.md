# ADR-002: Selección de la Tecnología de Mensajería y Event Streaming
**Proyecto:** La Gran Liga de Apuestas de Medianos EIA  
**Empresa:** Salchipapa Maker Racing S.A.S.  
**Estado:** `[x]` Aprobado por el usuario  
**Fecha:** 2026-10-27  

---

## 1. Contexto y Problema
La plataforma de apuestas sobre carreras de medianos requiere una infraestructura asíncrona para propagar eventos transaccionales desde el núcleo hacia múltiples subsistemas independientes: cálculo en vivo de cuotas dinámicas, notificación multicanal a apostadores, alimentación del almacén de analítica y auditoría/control de fraude. Asimismo, se debe coordinar la liquidación masiva de premios de más de 1.000.000 de apuestas en menos de 15 minutos sin bloquear el tráfico interactivo y respetando la directriz de costo y parsimonia técnica de la organización.

## 2. Opciones Consideradas
1. **RabbitMQ como Broker Único:** Sistema basado en colas AMQP, exchanges y enrutamiento flexible, complementable con colas tradicionales o streams.
2. **Apache Kafka como Broker Único:** Plataforma distribuida de streaming de eventos basada en log de confirmación particionado (*commit log* append-only) con persistencia configurable y grupos de consumidores independientes.
3. **Solución Dual (RabbitMQ + Kafka):** Kafka para la ingestión masiva de analítica y eventos de apuestas; RabbitMQ para la orquestación de tareas de liquidación y notificaciones.
4. **Ninguno (Comunicación Síncrona Directa):** Acoplamiento directo mediante llamadas REST/gRPC entre todos los componentes.

## 3. Decisión Tomada
Se adopta **Apache Kafka como tecnología única de mensajería y event streaming**. Los eventos transaccionales del núcleo (apuestas, inicios, finales y resultados) se publican en tópicos particionados mediante el patrón Transactional Outbox. Múltiples grupos de consumidores independientes (`Consumer Groups`) leen concurrentemente las particiones a su propio ritmo sin duplicación física de datos en el broker. La liquidación masiva de premios se resuelve mediante tareas en lotes particionados por identificador de lote (`batch_id`) sobre tópicos de trabajo en el mismo clúster.

## 4. Justificación del Descarte de Alternativas
- **Descarte de RabbitMQ como broker único:** Aunque cuenta con extensiones modernas como streams, el modelo nativo de Kafka de log distribuido particionado por clave de negocio (`race_id`, `user_id`) con consumidores desacoplados por offset resuelve de manera más homogénea y directa las necesidades de difusión masiva hacia múltiples subsistemas y la distribución concurrente de lotes de liquidación.
- **Descarte de la Solución Dual:** Para el diseño inicial del sistema no se ha demostrado una ventaja técnica suficiente que justifique la sobrecarga operativa, cognitiva y financiera de aprovisionar, asegurar y monitorear dos plataformas de mensajería dispares simultáneamente.
- **Descarte de Ninguno:** Descartado por el riesgo inminente de colapso en cascada bajo el pico de 10.000 apuestas/s.

## 5. Consecuencias

### Lo que se gana:
- **Consumo desacoplado y concurrente:** Notificaciones lentas, analítica pesada y auditoría consumen del mismo log sin saturar la memoria del broker ni interferir entre sí.
- **Distribución eficiente de liquidación:** Descomposición del millón de apuestas en lotes homogéneos particionados por identificador de lote (`batch_id`), procesados en paralelo por workers para cumplir el plazo de 15 minutos; el orden de bloqueo por `user_id` dentro de cada lote evita interbloqueos de saldo.
- **Persistencia y reprocesamiento operativo:** Retención temporal de eventos (ej. 7 días) que permite recuperar caídas de consumidores y reprocesar información reciente.

### Lo que se sacrifica y límites:
- **Complejidad de operación de Kafka:** Demanda gestión de particiones, replicación y balanceo de consumidores, recomendándose el uso de servicios administrados.
- **Semántica at-least-once:** Kafka puede reentregar eventos duplicados ante reintentos de red; **los consumidores deben ser estrictamente idempotentes** para impedir dobles cobros o acreditaciones repetidas.
- **Delimitación de retención:** Kafka no sustituye el almacenamiento de auditoría inalterable a 5 años; los eventos deben persistirse en un repositorio inmutable dedicado.
