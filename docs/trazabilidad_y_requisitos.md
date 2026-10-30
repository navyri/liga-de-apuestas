<!-- BANNER:INICIO (bloque estetico; omitido en el PDF consolidado) -->
<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&height=170&color=6B0F1A&text=TRAZABILIDAD%20Y%20REQUISITOS&fontColor=F4ECE4&fontSize=44&fontAlignY=34&desc=Documento%2000%20%C2%B7%20Cobertura%20verificada%20de%20los%2016%20puntos%20del%20enunciado&descColor=E8B4B8&descAlignY=60"
       alt="Banner: TRAZABILIDAD Y REQUISITOS"/>
</p>

<p align="center">
  <img src="https://64.media.tumblr.com/3254f08405664a04d3c5a65f765eb8c9/61bf168659dda322-50/s2048x3072/36c765a65bc72096e27e85823017367c0b9b48b2.pnj" alt="Ilustración conceptual de estrategia y competición en la academia" width="520"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Alcance-16%20puntos%20del%20PDF-540B13?style=flat-square&logoColor=white" alt="Alcance: 16 puntos del PDF"/>
  <img src="https://img.shields.io/badge/Mapeo-Requisito%20-%3E%20Documento-6B0F1A?style=flat-square&logoColor=white" alt="Mapeo: Requisito -> Documento"/>
</p>


<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=rect&height=6&color=6B0F1A"
       alt=""/>
</p>

<!-- BANNER:FIN -->

# MATRIZ DE TRAZABILIDAD Y COBERTURA DE REQUISITOS
**Caso:** La Gran Liga de Apuestas de Medianos EIA  
**Organización:** Salchipapa Maker Racing S.A.S.  
**Entregable:** Trazabilidad de Requisitos, Decisiones y Evidencias Documentales  
**Estado:** Documento de Entrega Técnico (Consolidado para Evaluación)  

---

<!-- DIVISOR:INICIO (bloque estetico; omitido en el PDF consolidado) -->
<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=rect&height=6&color=6B0F1A" alt=""/>
</p>
<!-- DIVISOR:FIN -->


## 1. Matriz Integral de Trazabilidad

Esta matriz documenta la correspondencia biunívoca entre las exigencias oficiales del enunciado (`Trabajo de Arquitectura de Software.pdf`), las decisiones arquitectónicas adoptadas, su ubicación documental y las limitaciones o evidencias pendientes de validación empírica.

| ID Requisito | Exigencia Oficial (Fuente PDF) | Decisión / Mecanismo Técnico | Documento Principal | Diapositiva Prevista | Estado / Evidencia Disponible |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **P1-REQ-001** | **Modelo Pari-Mutuel y Fases:** Bolsa común, 10% comisión, 90% neta, cuotas dinámicas y fijación al cierre (págs. 3, 6). | Algoritmo de mayores restos en enteros (`P1-DEC-003`). | `01_requisitos_y_negocio.md` y `05_datos_e_idempotencia.md` | Diapositiva 4 | **Diseño consolidado.** Verificado con ejemplo numérico determinista. |
| **P1-REQ-002** | **Cierre Estricto de Apuestas:** Cierre según reloj del servidor; rechazo inflexible de apuestas tardías (págs. 3, 5, 8, 9). | Condición atómica en SQL `CLOCK_TIMESTAMP() < races.start_time` y filtro en memoria. | `03_flujo_critico_y_comunicacion.md` y `06_escalabilidad_y_fallos.md` | Diapositiva 5 | **Diseño consolidado.** Requiere sincronización NTP de infraestructura. |
| **P1-REQ-003** | **Ciclo de Vida de Carrera y Reembolsos:** FSM determinista; cancelación previa a finalizada con devolución 100% (pág. 3). | Máquina de estados explícita y evento `CarreraCancelada`. | `01_requisitos_y_negocio.md` y `04_mensajeria_y_eventos.md` | Diapositiva 4 | **Diseño consolidado.** Trazabilidad completa en FSM. |
| **P1-REQ-004** | **Validaciones Previas de Apuesta:** Existencia de usuario, carrera abierta, mediano, saldo y no duplicados (pág. 5). | Filtro secuencial en transacción atómica local en BD. | `03_flujo_critico_y_comunicacion.md` | Diapositiva 10 | **Diseño consolidado.** Mapeado en diagrama de secuencia. |
| **P1-REQ-005** | **Invariante de Billetera:** Prohibición absoluta de doble gasto y saldo negativo bajo concurrencia (págs. 6, 15). | Bloqueo pesimista `SELECT FOR UPDATE` + restricción física `CHECK (balance >= 0)`. | `05_datos_e_idempotencia.md` y `ADR-003` | Diapositiva 5 | **Diseño consolidado.** Mitiga carreras por usuario en motor OLTP. |
| **P1-REQ-006** | **Carga Masiva:** 100k usuarios concurrentes y pico de 10k apuestas/s durante 30 s (págs. 8, 15). | Escalamiento asimétrico (Gateway + Core elásticos, BD con I/O provisionado, Kafka). | `06_escalabilidad_y_fallos.md` | Diapositiva 16 | **Objetivo de diseño.** Requiere validación empírica en pruebas de estrés. |
| **P1-REQ-007** | **Latencia al Apostar:** Respuesta determinista al apostador en menos de 1 segundo (págs. 9, 15). | Presupuesto de latencia estimado en 330-660 ms; Transactional Outbox asíncrono. | `03_flujo_critico_y_comunicacion.md` y `06_escalabilidad_y_fallos.md` | Diapositiva 9 | **Objetivo de diseño.** Estimado analíticamente; pendiente de telemetría real. |
| **P1-REQ-008** | **Durabilidad Absoluta:** Pérdida cero de apuestas aceptadas y movimientos contables (pág. 9). | `synchronous_commit = on`, replicación WAL síncrona y archivado PITR. | `06_escalabilidad_y_fallos.md` | Diapositiva 17 | **Diseño consolidado.** Cubre fallos de nodo y almacenamiento con réplica. |
| **P1-REQ-009** | **Plazo de Liquidación de Premios:** Pago en menos de 15 minutos para > 1.000.000 de apuestas (págs. 6, 9). | Reparto global previo y dispersión en lotes particionados consumidos en paralelo. | `04_mensajeria_y_eventos.md` y `06_escalabilidad_y_fallos.md` | Diapositiva 14 | **Objetivo de diseño.** Demanda I/O sostenido de ~1.500 escrituras/s en BD. |
| **P1-REQ-010** | **Retención y Auditoría:** Registro inalterable durante al menos 5 años; rol auditor de solo lectura (págs. 7, 8, 9). | Almacenamiento WORM / Object Lock, sellado SHA-256 y permisos exclusivos SELECT. | `05_datos_e_idempotencia.md` y `07_seguridad_y_costos.md` | Diapositiva 18 | **Diseño consolidado.** Distingue replicación de inmutabilidad física. |
| **P1-REQ-011** | **Aislamiento de Notificaciones:** Caída de notificaciones no bloquea apuestas (págs. 7, 16). | Desacoplamiento físico mediante Apache Kafka y consumo asíncrono diferido. | `04_mensajeria_y_eventos.md` y `06_escalabilidad_y_fallos.md` | Diapositiva 17 | **Diseño consolidado.** Resuelto en análisis de fallos (Caso A). |
| **P1-REQ-012** | **Seguridad y Control de Acceso:** 4 roles RBAC, protección perimetral, DMZ pública vs VPC privada (págs. 4, 7, 12). | Tokens JWT firmados, rate limiting Token Bucket y segmentación de subredes. | `07_seguridad_y_costos.md` | Diapositiva 18 | **Diseño consolidado.** Matriz RBAC y topología de red documentada. |
| **P1-REQ-013** | **Múltiples Apuestas Legítimas vs. Idempotencia:** Permitir varias jugadas válidas deduplicando reintentos (págs. 3, 9, 15). | Header `Idempotency-Key` por intención y clave de premio por apuesta (`bet_id`). | `05_datos_e_idempotencia.md` y `ADR-003` | Diapositiva 13 | **Diseño consolidado.** Deduplica fallos de red sin frenar nuevas jugadas. |
| **P1-REQ-014** | **Restricción de Costo y Simplicidad:** Regla de Dyllan ("no infraestructura de Netflix") (págs. 12, 13, 19, 20). | 1 Núcleo Modular replicable y 1 broker Kafka único, evitando sobreingeniería. | `02_arquitectura_y_componentes.md` y `07_seguridad_y_costos.md` | Diapositiva 19 | **Diseño consolidado.** Racionalización estricta de componentes. |
| **P1-REQ-015** | **Condiciones Académicas de Entrega:** Exposición 4-5 nov, máx. 20 slides, defensa individual y cambio en vivo (pág. 19). | Guion de 20 diapositivas, notas de orador y protocolo de Live Betting. | `09_presentacion_diapositivas.md` y `10_guia_sustentacion.md` | Diapositiva 1-20 | **Entregables estructurados.** Preparado para práctica y sustentación. |

---

<!-- DIVISOR:INICIO (bloque estetico; omitido en el PDF consolidado) -->
<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=rect&height=6&color=6B0F1A" alt=""/>
</p>
<!-- DIVISOR:FIN -->


## 2. Decisiones Arquitectónicas Formalizadas

- **P1-DEC-001 (Estilo Arquitectónico):** Adopción de la **Arquitectura Híbrida** (Núcleo Modular Transaccional para usuarios, medianos, carreras, apuestas y billetera, con servicios/workers desacoplados para notificaciones, analítica y liquidación masiva). Formalizada en `ADR-001`.
- **P1-DEC-002 (Tecnología de Mensajería):** Selección de **Apache Kafka como Broker Único** del sistema, aplicando el patrón Transactional Outbox para publicación confiable y desacoplamiento de consumidores. Formalizada en `ADR-002`.
- **P1-DEC-003 (Reparto de Premios):** Distribución de residuos de la bolsa común mediante el **Algoritmo de Mayores Restos** en centavos enteros con desempate determinista por `bet_id`, garantizando que la suma de premios y comisión coincida al centavo con la bolsa recaudada. Formalizada en `ADR-003`.
- **P1-DEC-004 (Ausencia de Ganadores):** Reembolso íntegro del 100% de los fondos a los apostadores participantes sin retener comisión ni acumular pozo, preservando la carrera en estado `LIQUIDADA` con motivo `SIN_APUESTAS_GANADORAS`. Formalizada en `05_datos_e_idempotencia.md`.
- **P1-DEC-005 (Granularidad de Idempotencia):** Deduplicación de pagos vinculada a la apuesta individual (`UNIQUE(bet_id, 'PRIZE_PAYOUT')`), permitiendo múltiples jugadas válidas de un mismo usuario. Formalizada en `ADR-003`.

---

<!-- DIVISOR:INICIO (bloque estetico; omitido en el PDF consolidado) -->
<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=rect&height=6&color=6B0F1A" alt=""/>
</p>
<!-- DIVISOR:FIN -->


## 3. Cobertura Documental de los 16 Puntos del PDF

1. **Arquitectura y Justificación:** [`02_arquitectura_y_componentes.md`](02_arquitectura_y_componentes.md) y [`08_diagramas_y_adrs/ADR-001_estilo_arquitectonico.md`](08_diagramas_y_adrs/ADR-001_estilo_arquitectonico.md).
2. **Identificación de Módulos y Responsabilidades:** [`02_arquitectura_y_componentes.md`](02_arquitectura_y_componentes.md).
3. **Diagrama General de Arquitectura:** [`08_diagramas_y_adrs/diagrama_general.md`](08_diagramas_y_adrs/diagrama_general.md).
4. **Diagrama de Secuencia de Apuesta:** [`08_diagramas_y_adrs/diagrama_secuencia_apuesta.md`](08_diagramas_y_adrs/diagrama_secuencia_apuesta.md).
5. **Comunicaciones Síncronas (Tabla Decisión 3):** [`03_flujo_critico_y_comunicacion.md`](03_flujo_critico_y_comunicacion.md).
6. **Eventos y Asincronía (Tabla Decisión 4):** [`04_mensajeria_y_eventos.md`](04_mensajeria_y_eventos.md).
7. **Diseño de Mensajería Kafka:** [`04_mensajeria_y_eventos.md`](04_mensajeria_y_eventos.md) y [`08_diagramas_y_adrs/topologia_mensajeria.md`](08_diagramas_y_adrs/topologia_mensajeria.md).
8. **Estrategia de Idempotencia:** [`05_datos_e_idempotencia.md`](05_datos_e_idempotencia.md) y [`08_diagramas_y_adrs/ADR-003_consistencia_billetera.md`](08_diagramas_y_adrs/ADR-003_consistencia_billetera.md).
9. **Datos y Consistencia:** [`05_datos_e_idempotencia.md`](05_datos_e_idempotencia.md).
10. **Manejo de Cargas Masivas:** [`06_escalabilidad_y_fallos.md`](06_escalabilidad_y_fallos.md).
11. **Estrategia de Seguridad y Segmentación:** [`07_seguridad_y_costos.md`](07_seguridad_y_costos.md).
12. **Consideraciones de Costo:** [`07_seguridad_y_costos.md`](07_seguridad_y_costos.md).
13. **Manejo de Fallos (Casos A, B y C):** [`06_escalabilidad_y_fallos.md`](06_escalabilidad_y_fallos.md).
14. **Registros ADR (3 formales):** En directorio [`08_diagramas_y_adrs/`](08_diagramas_y_adrs/).
15. **Respuesta a la Pregunta Final (Hoy vs. 100x):** [`09_presentacion_diapositivas.md`](09_presentacion_diapositivas.md).
16. **Conclusiones:** [`09_presentacion_diapositivas.md`](09_presentacion_diapositivas.md).
