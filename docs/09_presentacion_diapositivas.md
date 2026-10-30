<!-- BANNER:INICIO (bloque estetico; omitido en el PDF consolidado) -->
<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&height=170&color=6B0F1A&text=PRESENTACION%20Y%20PREGUNTA%20FINAL&fontColor=F4ECE4&fontSize=44&fontAlignY=34&desc=Documento%2009%20%C2%B7%20Guion%20de%2020%20diapositivas%20y%20respuesta%20ante%20un%20crecimiento%20100x&descColor=E8B4B8&descAlignY=60"
       alt="Banner: PRESENTACION Y PREGUNTA FINAL"/>
</p>

<p align="center">
  <img src="https://64.media.tumblr.com/3254f08405664a04d3c5a65f765eb8c9/61bf168659dda322-50/s2048x3072/36c765a65bc72096e27e85823017367c0b9b48b2.pnj" alt="Ilustración conceptual de estrategia y competición en la academia" width="520"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Diapositivas-20%20%28maximo%29-540B13?style=flat-square&logoColor=white" alt="Diapositivas: 20 (maximo)"/>
  <img src="https://img.shields.io/badge/Evolucion-Hoy%20vs%20100x-6B0F1A?style=flat-square&logoColor=white" alt="Evolucion: Hoy vs 100x"/>
  <img src="https://img.shields.io/badge/Universidad-EIA-8B1E2D?style=flat-square&logoColor=white" alt="Universidad: EIA"/>
</p>


<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=rect&height=6&color=6B0F1A"
       alt=""/>
</p>

<!-- BANNER:FIN -->

# ETAPA P1-9: ENTREGA, CONCLUSIONES Y PRESENTACIÓN EJECUTIVA
**Caso:** La Gran Liga de Apuestas de Medianos EIA  
**Organización:** Salchipapa Maker Racing S.A.S.  
**Artefacto:** `P1-ART-010`  
**Versión:** `v1.0`  
**Estado:** `[x]` Consolidado y verificado por revisión autónoma  

---

## P1-9.1 Y P1-9.2: RESPUESTA A LA PREGUNTA FINAL DEL ENUNCIADO (PDF pág. 20)

> **Pregunta Oficial del PDF:**  
> *"Si ustedes fueran los responsables técnicos de Salchipapa Maker Racing S.A.S., ¿qué arquitectura implementarían hoy y cómo permitirían que evolucionara si la plataforma creciera 100 veces?"*

### 1. La Arquitectura que Implementaríamos Hoy (Fase Actual: 100k usuarios / 10k apuestas/s)
- **Implementación Inmediata:** **Arquitectura Híbrida** con Núcleo Modular Transaccional (`core-api` desplegado en contenedor o instancias elásticas) complementado con Apache Kafka administrado y workers especializados para Notificaciones, Analítica y Liquidación masiva.
- **Sustentación Dimensional de la Elección Inicial:**
  - **Complejidad:** Mínima viable. Agrupar apuestas y billetera en un monolito modular permite resolver la consistencia mediante transacciones locales ACID, suprimiendo la necesidad de patrones de coordinación distribuida (Sagas o 2PC) en la ruta crítica.
  - **Escalabilidad:** Escalamiento horizontal del núcleo mediante réplicas *stateless* detrás de un balanceador de carga, con particionamiento lógico de billeteras por usuario (`FOR UPDATE`) y réplicas de lectura para cuotas y catálogo.
  - **Resiliencia:** Desacoplamiento total de fallos: la caída de notificaciones no afecta las apuestas; las fallas en Kafka se absorben mediante Transactional Outbox en base de datos.
  - **Consistencia:** Consistencia fuerte inmediata para saldo y corte de carreras; consistencia eventual para streaming analítico y notificaciones.
  - **Seguridad:** Perímetro DMZ con rate limiting y WAF, autenticación JWT stateless, matriz RBAC estricta y aislamiento de red privada (VPC).
  - **Costo:** Estricto apego a la directriz de Dyllan: una base de datos relacional operativa con réplica, un clúster Kafka moderado y cómputo elástico que se reduce al mínimo en periodos intersemestrales.
  - **Mantenibilidad:** Código modular fuertemente tipado con interfaces explícitas que impiden acoplamientos espurios.

### 2. Ruta de Evolución ante un Crecimiento Hipotético de 100 Veces
Si Salchipapa Maker Racing experimentara un crecimiento masivo de 100 veces, la arquitectura no debe reescribirse a ciegas. Cada evolución debe responder a **señales y cuellos de botella empíricos claramente identificados**:

1. **Evolución 1: Sharding Transaccional de la Base de Datos:**
   - *Señal disparadora:* La contención en el Write-Ahead Log (WAL) y el límite físico de IOPS del nodo primario relacional impiden superar las 15.000 escrituras sostenidas/s.
   - *Mecanismo:* Se divide la base de datos de billeteras y apuestas en *shards* particionados por `user_id`. Como la apuesta solo involucra al usuario y la metadata de carrera (replicable en caché local), se preserva la atomicidad local sin transacciones distribuidas.
2. **Evolución 2: Segregación Física del Servicio Contable (Billetera):**
   - *Señal disparadora:* Necesidad de equipos de desarrollo independientes para el libro mayor o requisitos regulatorios contables externos.
   - *Problemas de consistencia que introduce:* Separar físicamente Billetera y Apuestas **destruye la transacción local ACID**, obligando a introducir coordinación distribuida (patrón Saga con compensaciones o reserva de créditos anticipados) y aumentando la latencia de red en la ruta crítica de 1 segundo. Por tanto, esta segregación **no es obligatoria ni recomendada inicialmente** salvo que la escala organizativa lo imponga.
3. **Evolución 3: Kafka Tiered Storage:**
   - *Señal disparadora:* El volumen de eventos acumulados satura los discos NVMe locales del clúster de Kafka.
   - *Mecanismo:* Se habilita almacenamiento escalonado para descargar segmentos fríos a almacenamiento de objetos sin degradar la memoria del broker.
4. **Evolución 4: Borde Distribuido (Edge Computing):**
   - *Señal disparadora:* Tráfico internacional con latencia de red geográfica superior a 400 ms desde clientes distantes.
   - *Mecanismo:* Despliegue de puntos de presencia (PoPs) para terminación TLS y rate limiting cercano al usuario.

---

## P1-9.3: CONCLUSIONES TÉCNICAS Y FILOSOFÍA DEL PROYECTO

1. **La Complejidad debe Justificarse por Requisitos, no por Moda:**  
   Tal como postula el enunciado oficial: *"Una buena arquitectura no es aquella que utiliza más tecnologías. Una buena arquitectura es aquella que utiliza la complejidad necesaria para resolver el problema sin agregar complejidad innecesaria"*. La tentación de adoptar 20 microservicios y dos motores de mensajería para gestionar carreras de medianos habría resultado en un diseño costoso, frágil y de difícil operación.
2. **La Coherencia Contable es Innegociable:**  
   En plataformas transaccionales, ningún mediano debe recibir premios dobles ni un usuario quedar con saldo negativo porque alguien presionó cuatro veces un botón. La combinación de consistencia local atómica, bloqueos por fila, claves idempotentes únicas y el algoritmo de mayores restos garantiza integridad matemática al centavo.
3. **El Desacoplamiento es la Llave de la Resiliencia:**  
   Separar físicamente los canales de notificación y el procesamiento analítico pesado de la ruta crítica de admisión de apuestas blinda la plataforma contra caídas de proveedores externos o lentitud en consultas agregadas.

---

## P1-9.4: PRESENTACIÓN EJECUTIVA COMPLETA (ESTRUCTURA DE 20 DIAPOSITIVAS)

Conforme a la restricción obligatoria del PDF (pág. 19: *"Extensión: presentación de máximo 20 diapositivas"*), se estructura el guion integral:

```text
 ┌─────────────────────────────────────────────────────────────────────────────────────────────┐
 │                    ESTRUCTURA DE PRESENTACIÓN EJECUTIVA (20 DIAPOSITIVAS)                   │
 └──────────────────────────────────────────────┬──────────────────────────────────────────────┘
  SLIDE 01: Portada Institucional y Título del Proyecto (Salchipapa Maker Racing & EIA)
  SLIDE 02: Contexto del Negocio y Desafío de Dyllan (De hoja de cálculo a sistema profesional)
  SLIDE 03: Requisitos Clave y Parámetros Cuantitativos (100k usuarios, 10k ops/s, < 1s, < 15 min)
  SLIDE 04: Modelo de Negocio: Apuesta Mutua (Pari-Mutuel) y Ciclo de Carrera FSM
  SLIDE 05: Los Cinco Invariantes del Sistema (Saldo positivo, cierre estricto, no duplicación)
  SLIDE 06: Decisión 1: Estilo Arquitectónico (Comparación de los 4 estilos y justificación)
  SLIDE 07: Descarte Justificado de Alternativas (Por qué no microservicios puros ni monolito clásico)
  SLIDE 08: Diagrama General de Arquitectura (Clientes, DMZ, Núcleo Modular, BDs y Kafka)
  SLIDE 09: Diferenciación Síncrona vs. Asíncrona (Ruta crítica < 1s vs. streaming)
  SLIDE 10: Flujo Secuencial de una Apuesta (Rate limiting, bloqueo de fila, ACID local y outbox)
  SLIDE 11: Decisión 2: Mensajería — Apache Kafka como Broker Único (Justificación técnica)
  SLIDE 12: Topología de Eventos y Catálogo Canónico (Topics, partition keys y consumer groups)
  SLIDE 13: Estrategia de Idempotencia en 3 Operaciones (Apuestas, premios y replay de eventos)
  SLIDE 14: Modelo de Liquidación Masiva y Algoritmo de Mayores Restos (Conservación exacta de la bolsa)
  SLIDE 15: Política ante Ausencia de Ganadores y Gestión de Devoluciones (100% reembolso, motivo explícito)
  SLIDE 16: Manejo de Cargas Masivas (10.000 apuestas/s: componentes que escalan vs. que no)
  SLIDE 17: Análisis de Fallos: Casos A (Notificaciones) y B (Billetera)
  SLIDE 18: Seguridad, RBAC y Segmentación de Red (DMZ pública vs. VPC privada)
  SLIDE 19: Gobernanza de Costos y Respuesta a la Pregunta Final (Diseño hoy vs. evolución 100x)
  SLIDE 20: Conclusiones Finales y Apertura de Preguntas
```

---

## P1-9.5: NOTAS Y GUÍA DE SUSTENTACIÓN PARA LOS ORADORES

### Recomendaciones Tácticas para la Exposición (4 y 5 de Noviembre):
1. **Defensa del Estilo Híbrido:**  
   *Pregunta del Jurado:* "¿Por qué no hicieron microservicios si es el estándar actual?"  
   *Respuesta Clave:* "Porque microservicios puros para este caso introducen el problema de transacciones distribuidas (Sagas) entre apuesta y billetera en una ventana de 1 segundo con 10.000 apuestas/s. La arquitectura híbrida mantiene la consistencia local ACID en el núcleo y utiliza el desacoplamiento de Kafka para lo que verdaderamente lo requiere (notificaciones y analítica), cumpliendo la directriz de simplicidad y costos de Salchipapa Maker Racing".
2. **Defensa de Kafka sobre RabbitMQ:**  
   *Pregunta del Jurado:* "¿Por qué no RabbitMQ que es más liviano?"  
   *Respuesta Clave:* "RabbitMQ es excelente para tareas en colas, pero aquí tenemos múltiples consumidores independientes leyendo concurrentemente el mismo flujo de apuestas a velocidades muy distintas sin duplicar el almacenamiento físico. Además, el log particionado de Kafka nos permite paralelizar la liquidación masiva por lotes y habilitar reproducción para auditoría sin requerir un segundo broker".
3. **Defensa del Reparto de Mayores Restos:**  
   *Pregunta del Jurado:* "¿Cómo evitan perder o ganar centavos en el reparto?"  
   *Respuesta Clave:* "Operamos en centavos enteros mínimos evitando coma flotante. Truncamos la base y asignamos los centavos residuales a las apuestas con mayor resto fraccionario, usando el `bet_id` como desempate determinista. Esto garantiza por construcción matemática que comisión + premios sea idéntico al centavo a la bolsa recaudada".

---

## P1-9.6: VERIFICACIÓN CRUZADA DE LOS 16 PUNTOS DEL ENTREGABLE OFICIAL (PDF pág. 18)

| Punto Oficial del PDF | Sección en la Documentación del Proyecto | Estado |
| :--- | :--- | :---: |
| **1. Arquitectura seleccionada y justificación (con descartes)** | `02_arquitectura_y_componentes.md` y `ADR-001` | **Completado** |
| **2. Identificación de servicios/módulos y responsabilidades** | `02_arquitectura_y_componentes.md` | **Completado** |
| **3. Diagrama general de arquitectura** | `08_diagramas_y_adrs/diagrama_general.md` | **Completado** |
| **4. Diagrama de secuencia del flujo de una apuesta** | `08_diagramas_y_adrs/diagrama_secuencia_apuesta.md` | **Completado** |
| **5. Comunicaciones síncronas (Tabla Decisión 3)** | `03_flujo_critico_y_comunicacion.md` | **Completado** |
| **6. Eventos y comunicaciones asíncronas (Tabla Decisión 4)** | `04_mensajeria_y_eventos.md` | **Completado** |
| **7. Diseño de RabbitMQ y/o Kafka** | `04_mensajeria_y_eventos.md`, `diagramas` y `ADR-002` | **Completado** |
| **8. Estrategia de idempotencia** | `05_datos_e_idempotencia.md` y `ADR-003` | **Completado** |
| **9. Datos y consistencia** | `05_datos_e_idempotencia.md` | **Completado** |
| **10. Manejo de cargas masivas** | `06_escalabilidad_y_fallos.md` | **Completado** |
| **11. Estrategia básica de seguridad (públicos vs. privados)** | `07_seguridad_y_costos.md` | **Completado** |
| **12. Consideraciones de costo** | `07_seguridad_y_costos.md` | **Completado** |
| **13. Manejo de fallos (Casos A, B y C opcional)** | `06_escalabilidad_y_fallos.md` | **Completado** |
| **14. Tres registros ADR (máximo 1 página c/u)** | `ADR-001`, `ADR-002`, `ADR-003` en `08_diagramas_y_adrs/` | **Completado** |
| **15. Respuesta a la pregunta final (Hoy vs. 100x)** | `09_presentacion_diapositivas.md` (P1-9.1 y P1-9.2) | **Completado** |
| **16. Conclusiones** | `09_presentacion_diapositivas.md` (P1-9.3) | **Completado** |

---

## P1-9.7: REVISIÓN DE CUMPLIMIENTO FRENTE A LA RÚBRICA OFICIAL (PDF pág. 19)

- **Justificación de estilo y servicios (15%):** Cubierto con análisis riguroso de trade-offs y descarte formal de microservicios y monolito tradicional (`ADR-001`).
- **Comunicación síncrona/asíncrona y mensajería (20%):** Cubierto con tabla síncrona formal, topología de Kafka, outbox y tabla canónica en español (`ADR-002`).
- **Idempotencia, datos y consistencia (20%):** Cubierto con consistencia fuerte ACID local, bloqueo `FOR UPDATE`, 3 niveles de idempotencia, mayores restos y política de sin ganadores (`ADR-003`).
- **Escalabilidad y fallos (15%):** Cubierto con análisis del pico de 10k ops/s, presupuesto de latencia, Casos A, B y C resueltos forensemente.
- **Seguridad y costos (10%):** Cubierto con matriz RBAC, rate limiting, aislamiento DMZ vs VPC y optimización de infraestructura.
- **Calidad de diagramas, ADR y documentos (10%):** Cubierto con 3 diagramas Mermaid profesionales y 3 ADRs en formato formal de 1 página.
- **Sustentación (10%):** Cubierto con guion de 20 diapositivas y preparación para la defensa en vivo.
