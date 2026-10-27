# Liga de Apuestas de Medianos EIA — Diseño de Arquitectura de Software

Este repositorio contiene la **Parte 1** del proyecto académico de Arquitectura de Software (Universidad EIA) para la empresa ficticia **Salchipapa Maker Racing S.A.S.**

## Objetivo Académico y Alcance
- **Alcance estricto de diseño:** Este trabajo comprende exclusivamente el análisis de requisitos, diseño de arquitectura distribuida, justificación técnica, elaboración de diagramas, redacción de registros de decisiones arquitectónicas (ADR) y preparación de la sustentación técnica.
- **Sin implementación ejecutable:** Conforme al enunciado oficial (`Trabajo de Arquitectura de Software.pdf`), **no se implementa la plataforma**, código de aplicación, pipelines ni infraestructura ejecutable en esta parte.
- **Git como herramienta organizativa:** El versionado en este repositorio se utiliza con fines estrictamente documentales, de trazabilidad y gobernanza de entregables.

## Organización de la Documentación
Toda la documentación técnica se gestiona en el directorio `parte_1_arquitectura/`:
```text
parte_1_arquitectura/
├── 00_registro_maestro_p1.md              # Registro maestro: checklist, trazabilidad, supuestos y bitácora
├── 01_requisitos_y_negocio.md             # Etapa P1-1: Actores, roles, reglas de negocio y cargas
├── 02_arquitectura_y_componentes.md       # [Previsto] Etapa P1-2: Estilo y división de servicios
├── 03_flujo_critico_y_comunicacion.md     # [Previsto] Etapa P1-3: Flujo de apuesta y tabla síncrona
├── 04_mensajeria_y_eventos.md             # [Previsto] Etapa P1-4: Broker, tabla de eventos y topología
├── 05_datos_e_idempotencia.md             # [Previsto] Etapa P1-5: Persistencia, consistencia y transacciones
├── 06_escalabilidad_y_fallos.md           # [Previsto] Etapa P1-6: Cargas masivas y análisis de fallos
├── 07_seguridad_y_costos.md               # [Previsto] Etapa P1-7: RBAC, zonas de red y costos
├── 08_diagramas_y_adrs/                   # [Previsto] Etapa P1-8: Diagramas de arquitectura y ADRs
├── 09_presentacion_diapositivas.md        # [Previsto] Etapa P1-9: Presentación (máx. 20 diapositivas)
└── 10_guia_sustentacion.md                # [Previsto] Etapa P1-10: Banco de preguntas y cambio en vivo
```

## Estado Actual
- **Fuente de verdad:** `Trabajo de Arquitectura de Software.pdf` (Universidad EIA, 20 páginas).
- **Etapa P1-0 (Lectura y organización):** Completada y aprobada formalmente.
- **Etapa P1-1 (Negocio y requisitos):** En desarrollo. P1-1.1 (Actores, roles y capacidades) completado y aprobado.
- **Registro Maestro:** Disponible y versionado en [`parte_1_arquitectura/00_registro_maestro_p1.md`](parte_1_arquitectura/00_registro_maestro_p1.md).
