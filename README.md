<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&height=210&color=6B0F1A&text=MEDIANOS%20EIA&fontColor=F4ECE4&fontSize=58&fontAlignY=32&desc=Diseño%20de%20Arquitectura%20Distribuida%20·%20Salchipapa%20Maker%20Racing%20S.A.S.&descColor=E8B4B8&descAlignY=58"/>
</p>

<p align="center">
  <img src="https://64.media.tumblr.com/3254f08405664a04d3c5a65f765eb8c9/61bf168659dda322-50/s2048x3072/36c765a65bc72096e27e85823017367c0b9b48b2.pnj" alt="Ilustración conceptual de estrategia y competición en la academia" width="650"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Alcance-Diseño%20Arquitectónico-540B13?style=flat-square&logoColor=white"/>
  <img src="https://img.shields.io/badge/Universidad-EIA-8B1E2D?style=flat-square&logoColor=white"/>
  <img src="https://img.shields.io/badge/Créditos-EIA%20Coins%20(Ficticios)-6B0F1A?style=flat-square&logoColor=white"/>
  <img src="https://img.shields.io/badge/Concurrencia-100k%20usuarios-A82336?style=flat-square&logoColor=white"/>
  <img src="https://img.shields.io/badge/Pico-10k%20apuestas%2Fs-8B1E2D?style=flat-square&logoColor=white"/>
  <img src="https://img.shields.io/badge/Latencia-Objetivo%20%3C%201s-540B13?style=flat-square&logoColor=white"/>
</p>

**La Gran Liga de Carreras de Medianos EIA** es un proyecto académico de diseño y justificación de arquitectura de software para la empresa **Salchipapa Maker Racing S.A.S.**

El sistema modela una plataforma de apuestas mutuas (*pari-mutuel*) sobre competiciones de medianos, orientada a soportar una carga base de 500 usuarios y picos de hasta **100.000 usuarios concurrentes** con ráfagas de **10.000 apuestas por segundo** durante los 30 segundos previos al cierre de cada carrera.

> **Aclaración institucional:** Los **EIA Coins** son créditos exclusivamente ficticios dentro del marco académico del enunciado: no poseen valor monetario, no se compran ni se canjean por dinero real. El alcance del trabajo corresponde íntegramente al análisis, diseño y sustentación técnica de la arquitectura distribuida, sin implementación física de la plataforma.

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=rect&height=6&color=6B0F1A"/>
</p>

## Requisitos y Atributos de Calidad

| Parámetro | Valor Objetivo | Implicación Arquitectónica |
|---|---|---|
| Usuarios concurrentes (normal) | 500 sesiones activas | Operación base con recursos de infraestructura controlados |
| Usuarios concurrentes (final) | 100.000 sesiones simultáneas | Escalamiento elástico en borde e interfaces de consulta |
| Pico transaccional | 10.000 apuestas/s en 30 s | Ingesta masiva (300.000 transacciones) con particionamiento de balance |
| Latencia de respuesta | Objetivo < 1 segundo | Confirmación determinista estimada en 330-660 ms; Transactional Outbox |
| Durabilidad de datos | Cero pérdida | Persistencia transaccional ACID local con replicación síncrona de WAL |
| Liquidación masiva | Objetivo < 15 min (> 1.000.000 apuestas) | Reparto global previo y dispersión paralela en lotes de acreditación |
| Retención para auditoría | Mínimo 5 años | Almacenamiento inmutable WORM / Object Lock con permisos de solo lectura |

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=rect&height=6&color=6B0F1A"/>
</p>

## Reglas de Negocio e Invariantes

- **Modelo Pari-Mutuel:** Las apuestas consolidan una bolsa común. La casa retiene una comisión del 10% y el 90% restante se distribuye proporcionalmente entre las apuestas ganadoras mediante el algoritmo de mayores restos. La cuota final queda fijada exactamente al cierre de la carrera.
- **Cierre por Reloj del Servidor:** Las apuestas cierran en el instante exacto fijado para el inicio de la carrera según la hora del servidor. Toda solicitud recibida con posterioridad es rechazada irrevocablemente.
- **Integridad de Saldo:** Prohibición absoluta de saldo negativo o doble gasto de EIA Coins ante apuestas concurrentes de un mismo usuario (`SELECT FOR UPDATE` + `CHECK (balance >= 0)`).
- **Idempotencia Transaccional:** Múltiples solicitudes idénticas originadas por reintentos de red o pulsaciones repetidas generan un único efecto contable y una sola apuesta registrada mediante `Idempotency-Key`.
- **Desacoplamiento Operativo:** Las fallas en canales externos de notificación no bloquean la admisión ni confirmación de apuestas.

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=rect&height=6&color=6B0F1A"/>
</p>

## Estructura del Repositorio

```text
liga-de-apuestas/
├── .gitignore
├── README.md
├── herramientas/                            # Generación reproducible de los entregables visuales
│   ├── generar_diagramas.mjs                # Fuentes Mermaid → SVG/PNG en exportados/
│   ├── generar_documento_tecnico.py         # Markdown consolidado → documento técnico
│   ├── tema_diagramas.json                  # Tema vinotinto de los diagramas
│   └── puppeteer-config.json                # Chrome local para mermaid-cli
└── parte_1_arquitectura/
    ├── trazabilidad_y_requisitos.md         # Matriz de trazabilidad y cobertura de los 16 puntos
    ├── 01_requisitos_y_negocio.md           # Análisis de dominio, actores, roles e invariantes
    ├── 02_arquitectura_y_componentes.md     # Evaluación de estilos arquitectónicos y boundaries
    ├── 03_flujo_critico_y_comunicacion.md   # Flujo transaccional y contratos síncronos
    ├── 04_mensajeria_y_eventos.md           # Diseño de streaming Kafka, eventos y topología
    ├── 05_datos_e_idempotencia.md           # Persistencia, consistencia, mayores restos y políticas
    ├── 06_escalabilidad_y_fallos.md         # Carga masiva, presupuesto de latencia y fallos (A, B, C)
    ├── 07_seguridad_y_costos.md             # Esquema RBAC, segmentación DMZ y optimización de costos
    ├── 08_diagramas_y_adrs/                 # Fuentes Mermaid y los 3 registros formales ADR
    │   └── exportados/                      # Renders oficiales SVG y PNG (regenerables)
    ├── 09_presentacion_diapositivas.md      # Guion ejecutivo de 20 diapositivas y conclusiones
    ├── 10_guia_sustentacion.md              # Banco de preguntas y absorción de apuestas en vivo
    ├── presentacion/
    │   └── index.html                       # Presentación ejecutiva (20 diapositivas, HTML + CSS + JS)
    └── entregables/
        ├── presentacion.pdf                 # Presentación exportada (una diapositiva por página)
        └── documento_tecnico.pdf            # Documento técnico consolidado (Markdown + ADR + anexos)
```

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=rect&height=6&color=6B0F1A"/>
</p>

## Documentación Técnica y Entregables Oficiales

| Documento | Área Temática | Enlace |
|---|---|---|
| **Trazabilidad y Requisitos** | Cobertura de los 16 puntos del PDF, decisiones y estado de evidencias | [trazabilidad_y_requisitos.md](parte_1_arquitectura/trazabilidad_y_requisitos.md) |
| **Requisitos y Reglas de Negocio** | FSM de carrera, modelo Pari-Mutuel y los 5 invariantes | [01_requisitos_y_negocio.md](parte_1_arquitectura/01_requisitos_y_negocio.md) |
| **Arquitectura y Componentes** | Estilo híbrido, descarte justificado de microservicios y módulos | [02_arquitectura_y_componentes.md](parte_1_arquitectura/02_arquitectura_y_componentes.md) |
| **Flujo Crítico y Comunicación Síncrona** | Flujo atómico de apuesta, tabla síncrona formal e incertidumbre de red | [03_flujo_critico_y_comunicacion.md](parte_1_arquitectura/03_flujo_critico_y_comunicacion.md) |
| **Mensajería y Event Streaming** | Apache Kafka, catálogo canónico, lotes de liquidación y Outbox | [04_mensajeria_y_eventos.md](parte_1_arquitectura/04_mensajeria_y_eventos.md) |
| **Persistencia, Consistencia e Idempotencia** | Esquema OLTP/OLAP, mayores restos, reembolso sin ganadores y WORM | [05_datos_e_idempotencia.md](parte_1_arquitectura/05_datos_e_idempotencia.md) |
| **Escalabilidad y Manejo de Fallos** | Ráfaga de 10k ops/s, Casos A, B y C (opcional) de fallos y latencia | [06_escalabilidad_y_fallos.md](parte_1_arquitectura/06_escalabilidad_y_fallos.md) |
| **Seguridad, Control de Acceso y Costos** | Matriz RBAC, rate limiting, segmentación de red y regla de Dyllan | [07_seguridad_y_costos.md](parte_1_arquitectura/07_seguridad_y_costos.md) |
| **Diagramas Oficiales y Registros ADR** | Diagrama general, secuencia de apuesta, topología y ADRs 1, 2 y 3 | [08_diagramas_y_adrs/](parte_1_arquitectura/08_diagramas_y_adrs/) |
| **Presentación y Pregunta Final** | Respuesta técnica hoy vs 100x y guion de 20 diapositivas | [09_presentacion_diapositivas.md](parte_1_arquitectura/09_presentacion_diapositivas.md) |
| **Guía de Sustentación Técnica** | Preguntas probables del jurado y absorción de Live Betting en vivo | [10_guia_sustentacion.md](parte_1_arquitectura/10_guia_sustentacion.md) |

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=rect&height=6&color=6B0F1A"/>
</p>

## Entregables Visuales de la Parte 1

| Entregable | Contenido | Ubicación |
|---|---|---|
| **Presentación ejecutiva (HTML)** | 20 diapositivas con navegación por teclado (← →, Inicio/Fin), indicador de progreso, notas del orador separadas (tecla `N`) y estilos propios en la paleta vinotinto. Sin dependencias remotas: se abre directamente en cualquier navegador. | [presentacion/index.html](parte_1_arquitectura/presentacion/index.html) |
| **Presentación ejecutiva (PDF)** | Exportación oficial: una diapositiva por página (20 páginas, 1280×720), sin controles ni notas. | [entregables/presentacion.pdf](parte_1_arquitectura/entregables/presentacion.pdf) |
| **Documento técnico consolidado (PDF)** | Los 7 documentos temáticos + los 3 ADR + Anexo A con las fuentes y renders de los 4 diagramas (53 páginas). | [entregables/documento_tecnico.pdf](parte_1_arquitectura/entregables/documento_tecnico.pdf) |
| **Diagramas oficiales exportados** | Diagrama general, secuencia de apuesta, topología de mensajería y ciclo de carrera en SVG y PNG de alta resolución, generados desde las fuentes Mermaid canónicas. | [08_diagramas_y_adrs/exportados/](parte_1_arquitectura/08_diagramas_y_adrs/exportados/) |

### Regeneración de los entregables visuales

Los entregables visuales son **generados** desde fuentes versionadas (Markdown y Mermaid). Para reproducirlos:

```bash
# 1) Diagramas (SVG y PNG) — requiere Node.js
cd herramientas && npm install && cd ..
node herramientas/generar_diagramas.mjs

# 2) Documento técnico consolidado — requiere Python con la librería `markdown`
python herramientas/generar_documento_tecnico.py
#    y luego exportar el PDF con Chrome (headless) desde herramientas/.tmp_doc_tecnico/documento_tecnico.html

# 3) Presentación — basta con abrir presentacion/index.html en un navegador
#    y usar "Imprimir → Guardar como PDF" (una página por diapositiva, sin encabezados)
```

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&height=120&section=footer&color=6B0F1A" alt=""/>
</p>
