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
  <img src="https://img.shields.io/badge/Latencia-%3C%201%20segundo-540B13?style=flat-square&logoColor=white"/>
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
| Latencia de respuesta | < 1 segundo | Confirmación o rechazo determinista sin degradación de cola |
| Durabilidad de datos | Cero pérdida | Persistencia transaccional estricta en apuestas y balance |
| Liquidación masiva | < 15 minutos para > 1.000.000 apuestas | Procesamiento asíncrono en lotes paralelos |
| Retención para auditoría | Mínimo 5 años | Almacenamiento histórico inmutable con permisos de solo lectura |

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=rect&height=6&color=6B0F1A"/>
</p>

## Reglas de Negocio e Invariantes

- **Modelo Pari-Mutuel:** Las apuestas consolidan una bolsa común. La casa retiene una comisión del 10% y el 90% restante se distribuye proporcionalmente entre las apuestas ganadoras. La cuota final queda fijada exactamente al cierre de la carrera.
- **Cierre por Reloj del Servidor:** Las apuestas cierran en el instante exacto fijado para el inicio de la carrera según la hora del servidor. Toda solicitud recibida con posterioridad es rechazada irrevocablemente.
- **Integridad de Saldo:** Prohibición absoluta de saldo negativo o doble gasto de EIA Coins ante apuestas concurrentes de un mismo usuario.
- **Idempotencia Transaccional:** Múltiples solicitudes idénticas originadas por reintentos de red o pulsaciones repetidas generan un único efecto contable y una sola apuesta registrada.
- **Desacoplamiento Operativo:** Las fallas en canales externos de notificación no bloquean la admisión ni confirmación de apuestas.

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=rect&height=6&color=6B0F1A"/>
</p>

## Estructura del Repositorio

```text
liga-de-apuestas/
├── .gitignore
├── README.md
└── parte_1_arquitectura/
    ├── 00_registro_maestro_p1.md          # Trazabilidad, bitácora y control de decisiones
    ├── 01_requisitos_y_negocio.md         # Análisis de dominio, actores, roles e invariantes
    ├── 02_arquitectura_y_componentes.md   # Evaluación de estilos arquitectónicos y límites
    ├── 03_flujo_critico_y_comunicacion.md # Flujo de apuesta y contratos síncronos
    ├── 04_mensajeria_y_eventos.md         # Diseño de mensajería, eventos y topología
    ├── 05_datos_e_idempotencia.md         # Modelo de datos, consistencia y transacciones
    ├── 06_escalabilidad_y_fallos.md       # Carga masiva y análisis de escenarios de fallo
    ├── 07_seguridad_y_costos.md           # Esquema RBAC, segmentación y optimización
    ├── 08_diagramas_y_adrs/               # Diagramas Mermaid y registros formales ADR
    ├── 09_presentacion_diapositivas.md    # Estructura de presentación ejecutiva
    └── 10_guia_sustentacion.md            # Defensa técnica y absorción de cambios en vivo
```

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=rect&height=6&color=6B0F1A"/>
</p>

## Documentación Técnica

| Documento | Estado | Enlace |
|---|---|---|
| Registro Maestro y Trazabilidad | Activo | [00_registro_maestro_p1.md](parte_1_arquitectura/00_registro_maestro_p1.md) |
| Análisis de Requisitos y Dominio | Consolidado | [01_requisitos_y_negocio.md](parte_1_arquitectura/01_requisitos_y_negocio.md) |
| Arquitectura y Componentes | En elaboración | [02_arquitectura_y_componentes.md](parte_1_arquitectura/02_arquitectura_y_componentes.md) |

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&height=120&section=footer&color=6B0F1A" alt=""/>
</p>
