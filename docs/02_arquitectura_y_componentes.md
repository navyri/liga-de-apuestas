<!-- BANNER:INICIO (bloque estetico; omitido en el PDF consolidado) -->
<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&height=170&color=6B0F1A&text=ARQUITECTURA%20Y%20COMPONENTES&fontColor=F4ECE4&fontSize=44&fontAlignY=34&desc=Documento%2002%20%C2%B7%20Estilo%20h%C3%ADbrido%2C%20descartes%20justificados%20y%20m%C3%B3dulos&descColor=E8B4B8&descAlignY=60"
       alt="Banner: ARQUITECTURA Y COMPONENTES"/>
</p>

<p align="center">
  <img src="https://64.media.tumblr.com/3254f08405664a04d3c5a65f765eb8c9/61bf168659dda322-50/s2048x3072/36c765a65bc72096e27e85823017367c0b9b48b2.pnj" alt="Ilustración conceptual de estrategia y competición en la academia" width="520"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Estilo-Hibrido%20%28monolito%20modular%29-540B13?style=flat-square&logoColor=white" alt="Estilo: Hibrido (monolito modular)"/>
  <img src="https://img.shields.io/badge/Nucleo-core-api%20stateless-6B0F1A?style=flat-square&logoColor=white" alt="Nucleo: core-api stateless"/>
</p>


<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=rect&height=6&color=6B0F1A"
       alt=""/>
</p>

<!-- BANNER:FIN -->

# ETAPA P1-2: ARQUITECTURA Y COMPONENTES
**Caso:** La Gran Liga de Apuestas de Medianos EIA  
**Organización:** Salchipapa Maker Racing S.A.S.  
**Artefacto:** `P1-ART-003`  
**Versión:** `v1.0`  
**Estado:** `[x]` Consolidado (Estilo arquitectónico aprobado por el usuario; desglose de límites y componentes verificado por revisión autónoma)  

---

## P1-2.1 Y P1-2.2: DECISIÓN 1 — ESTILO ARQUITECTÓNICO APROBADO

### 1. Dirección Arquitectónica Aprobada: Arquitectura Híbrida
Se adopta formalmente una **Arquitectura Híbrida** estructurada a partir de un **Núcleo Modular Transaccional (Core Modular)** complementado con **Componentes y Workers Asíncronos Desacoplados**.

> **Fundamento metodológico y precisión de garantías:**  
> La elección de este estilo **no garantiza por sí sola** el cumplimiento de la respuesta en menos de un segundo, la absorción de 10.000 apuestas/s ni el cierre exacto. Su mérito radica en que **elimina dependencias de red distribuidas intermedias en la ruta crítica** y simplifica el plano de consistencia al permitir transacciones locales para el débito y la apuesta, facilitando el diseño de los mecanismos específicos de concurrencia, particionamiento, durabilidad e idempotencia que se validarán en las etapas posteriores.

### 2. Estructura General del Estilo Aprobado
1. **Núcleo Transaccional Modular (Core Monolith replicable):**
   - Agrupa con límites estrictos de módulo: *Usuarios/Autenticación*, *Medianos*, *Carreras*, *Apuestas* y *Billetera de EIA Coins*.
   - **Frontera transaccional estricta:** La verificación de saldo, la deducción de EIA Coins y la persistencia de la apuesta admitida se diseñan para ejecutarse dentro de una **misma transacción local atómica**, suprimiendo la necesidad de protocolos de coordinación distribuida (2PC o Sagas con compensación) en la ruta crítica de admisión.
2. **Componentes y Workers Desacoplados de la Ruta Crítica:**
   - **Servicio Autónomo de Notificaciones:** Desacoplado físicamente para que cualquier fallo o lentitud en canales externos (push, correo) jamás bloquee el flujo de admisión de apuestas.
   - **Pipeline y Servicio de Analítica / Estadísticas:** Desacoplado del motor transaccional, alimentado por eventos para no canibalizar recursos de base de datos durante las consultas analíticas pesadas.
   - **Proceso / Worker de Liquidación Masiva y Devoluciones:** Proceso especializado que procesa el cálculo y dispersión masiva de premios fuera del hilo interactivo de los usuarios.

### 3. Justificación del Descarte de Alternativas (Obligatorio PDF pág. 13)

#### A. Descarte de Microservicios Puros
- **Justificación técnica:** Una descomposición en microservicios independientes con bases de datos privadas para cada capacidad introduce una sobrecarga significativa de coordinación distribuida. Exigiría implementar orquestación o coreografía de Sagas y transacciones compensatorias complejas únicamente para sincronizar el débito en billetera con el registro de la apuesta, incrementando el riesgo de condiciones de carrera y exposición a saldo negativo bajo concurrencia masiva.
- **Criterio de gobernanza y costo:** La complejidad operativa (service discovery, distributed tracing, mTLS, múltiples esquemas de despliegue y particionamiento) resulta desproporcionada frente a las necesidades operativas de Salchipapa Maker Racing S.A.S., contraviniendo la regla rectora de Dyllan sobre evitar costos y complejidad innecesarios (PDF pág. 12, 19, 20). *(Nota: El descarte se fundamenta en la complejidad de consistencia, operación y costo, no en una incapacidad intrínseca de rendimiento).*

#### B. Descarte del Monolito Tradicional (Acoplado / No modular)
- **Justificación técnica:** Un monolito convencional sin fronteras modulares estrictas propaga fallos entre dominios dispares: una degradación en el despacho de notificaciones externas puede agotar el pool de hilos o conexiones HTTP, bloqueando la recepción de apuestas legítimas.
- **Contención de recursos:** La ingesta diaria de millones de registros analíticos y la ejecución de consultas pesadas de tendencias competirían directamente por los mismos recursos de memoria y bloqueos de almacenamiento que el pico de apuestas previo al cierre.

---

## P1-2.3: DEFINICIÓN DE RESPONSABILIDADES, LÍMITES Y UBICACIÓN DE CAPACIDADES

A continuación se formaliza la ubicación arquitectónica de las nueve capacidades del negocio, integrando expresamente los dominios de **Resultados**, **Liquidación de Premios**, **Devoluciones** y **Auditoría / Control de Fraude**:

```text
 ┌──────────────────────────────────────────────────────────────────────────────────────────────┐
 │                              ZONA PRIVADA / NÚCLEO TRANSACCIONAL                             │
 │                                                                                              │
 │   ┌──────────────────────────────────────────────────────────────────────────────────────┐   │
 │   │                   NÚCLEO MODULAR COHESIVO (Unidad Desplegable Web/API)               │   │
 │   │                                                                                      │   │
 │   │  [Módulo Usuarios/Auth]       [Módulo Medianos]          [Módulo Carreras]           │   │
 │   │  - Credenciales y RBAC        - Ficha de competidor      - Ciclo de estados          │   │
 │   │  - Validación de sesión       - Historial y estado       - Verificación hora cierre  │   │
 │   │                                                          - Registro resultado oficial│   │
 │   │                                                                                      │   │
 │   │  [Módulo Apuestas] ◄──────── (Transacción Local ACID) ────────► [Módulo Billetera]   │   │
 │   │  - Admisión y filtros                                    - Saldo de EIA Coins        │   │
 │   │  - Idempotencia de intención                             - Débito inmediato          │   │
 │   │  - Registro de apuesta                                   - Anti-doble gasto          │   │
 │   └──────────────────────────────────────────┬───────────────────────────────────────────┘   │
 │                                              │ Eventos de Dominio / Outbox                   │
 └──────────────────────────────────────────────┼───────────────────────────────────────────────┘
                                                ▼
 ┌──────────────────────────────────────────────────────────────────────────────────────────────┐
 │                      COMPONENTES Y WORKERS FUERA DE LA RUTA CRÍTICA                          │
 │                                                                                              │
 │   ┌────────────────────────┐  ┌────────────────────────┐  ┌──────────────────────────────┐   │
 │   │   WORKER LIQUIDACIÓN   │  │ SERVICIO NOTIFICACIONES│  │     SERVICIO ANALÍTICA       │   │
 │   │    Y DEVOLUCIONES      │  │  (Unidad Desplegable)  │  │    (Unidad Desplegable)      │   │
 │   │ (Proceso Especializado)│  │                        │  │                              │   │
 │   │ - Detección ganadores  │  │ - Consumo de eventos   │  │ - Ingesta masiva diaria      │   │
 │   │ - Cálculo Pari-Mutuel  │  │ - Enrutamiento multican│  │ - Agregación de tendencias   │   │
 │   │ - Dispersión en lotes  │  │ - Reintentos aislados  │  │ - Almacén analítico dedicado │   │
 │   │ - Dispersión reembolsos│  │ - Falla no frena Core  │  │ - Reportes premium diferidos │   │
 │   └───────────┬────────────┘  └────────────────────────┘  └──────────────────────────────┘   │
 │               │                                                                              │
 │               ▼ Acreditación en Billetera                                                    │
 │   ┌──────────────────────────────────────────────────────────────────────────────────────┐   │
 │   │              MÓDULO DE AUDITORÍA Y CONTROL DE FRAUDE (Transversal)                   │   │
 │   │ - Registro append-only inmutable de apuestas, transacciones, resultados y premios     │   │
 │   │ - Consola de consulta de Solo Lectura para el rol Auditor                            │   │
 │   │ - Detección asíncrona de anomalías de cierre y concurrencia por dispositivo          │   │
 │   └──────────────────────────────────────────────────────────────────────────────────────┘   │
 └──────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Tabla de Ubicación y Frontera Transaccional de Responsabilidades

| Capacidad / Responsabilidad | Módulo Lógico | Unidad Desplegable | Frontera Transaccional | Justificación de Ubicación |
| :--- | :--- | :--- | :--- | :--- |
| **Usuarios y Autenticación** | `UsersModule` | Núcleo Modular (Core) | Dentro de frontera | Autenticación y validación de permisos de sesión en memoria/borde sin llamadas remotas. |
| **Medianos** | `RacersModule` | Núcleo Modular (Core) | Lectura local / Caché | Datos maestros de baja volatilidad consultados directamente al validar la apuesta. |
| **Carreras (Programación y Cierre)** | `RacesModule` | Núcleo Modular (Core) | Dentro de frontera | El control del reloj del servidor y el estado de la carrera (`ABIERTA`/`CERRADA`) deben validarse atómicamente al recibir la apuesta. |
| **Apuestas (Admisión e Idempotencia)** | `BetsModule` | Núcleo Modular (Core) | **Ruta crítica transaccional** | Debe coordinarse atómicamente con la billetera para admitir la jugada. |
| **Billetera de EIA Coins (Débito)** | `WalletModule` | Núcleo Modular (Core) | **Ruta crítica transaccional** | Descuento atómico junto a la apuesta para garantizar que no exista saldo negativo. |
| **Recepción de Resultado Oficial** | `RacesModule` | Núcleo Modular (Core) | Transaccional administrativa | Sellado formal del ganador oficial por el Operador, disparando el evento de cierre de ciclo. |
| **Liquidación de Premios** | `SettlementModule` | Worker de Liquidación | **Fuera de la ruta crítica** | El cálculo sobre más de 1.000.000 de apuestas y la acreditación masiva se ejecutan asíncronamente en lotes para no bloquear peticiones HTTP. |
| **Devoluciones por Cancelación** | `SettlementModule` | Worker de Liquidación | **Fuera de la ruta crítica** | Si la carrera pasa a `CANCELADA`, un proceso batch dispersa el 100% de los reembolsos a las billeteras de manera controlada. |
| **Notificaciones** | `NotificationService` | Servicio Autónomo | **Fuera de la ruta crítica** | Su fallo no debe afectar el registro transaccional; consume eventos de dominio mediante colas. |
| **Estadísticas y Analítica** | `AnalyticsService` | Servicio Autónomo | **Fuera de la ruta crítica** | Procesa millones de eventos diarios en un almacén optimizado para lecturas agregadas sin sobrecargar la base de datos operativa. |
| **Auditoría y Control de Fraude** | `AuditModule` | Núcleo Core + Almacén Inmutable | Híbrida (Registro local + Análisis asíncrono) | Las mutaciones generan un registro de auditoría append-only atómico; el análisis forense y la consulta de solo lectura se ejecutan en réplica dedicada. |

---

## P1-2.4: DISTINCIÓN ENTRE MÓDULOS, UNIDADES DESPLEGABLES Y PROPIEDAD DE DATOS

Para evitar acoplamientos ocultos y respetar la regla de Dyllan, se formalizan las tres dimensiones arquitectónicas:

1. **Módulos Lógicos (Estructura de Código):**  
   Encapsulan lógica de negocio, entidades y reglas en paquetes con interfaces explícitas. Un módulo no puede consultar directamente las tablas internas de otro módulo ni mutar sus estructuras en memoria; toda interacción interna se realiza mediante contratos de interfaz de dominio.
2. **Unidades Desplegables (Procesos en Ejecución):**
   - **`core-api`:** Servicio web/API escalable que contiene el Núcleo Modular Transaccional. Recibe el tráfico de apostadores y operadores.
   - **`settlement-worker`:** Proceso en segundo plano dedicado a la liquidación masiva de premios y dispersión de devoluciones.
   - **`notification-service`:** Demonio/consumidor independiente para despacho de mensajes multicanal.
   - **`analytics-service`:** Pipeline y API de consulta analítica especializada.
3. **Propiedad y Almacenamiento de Datos:**
   - **Base de Datos Operativa Transaccional (OLTP):** Propiedad exclusiva del Núcleo Modular. Aloja esquemas aislados para usuarios, carreras, apuestas, billetera y libro contable. Soporta transacciones ACID locales.
   - **Almacén Analítico e Histórico (OLAP):** Propiedad exclusiva del servicio de analítica. Esquema desnormalizado optimizado para consultas agregadas masivas y retención histórica de 5 años.
   - **Aislamiento de Recursos:** El almacén analítico se encuentra físicamente separado del almacén transaccional operativo, impidiendo que la generación de reportes premium degrade el rendimiento de las apuestas.

---

## P1-2.5: ESTRATEGIA DE ESCALAMIENTO INDEPENDIENTE Y MITIGACIÓN DE CUELLOS DE BOTELLA

### 1. Escalamiento Horizontal del Núcleo Modular (`core-api`)
- El Núcleo Modular se despliega en **múltiples instancias idénticas** detrás de un balanceador de carga con terminación TLS.
- Las instancias son completamente *stateless* a nivel de sesión HTTP (autenticación mediante tokens criptográficos verificables localmente sin consulta de sesión a base de datos).

### 2. Cuellos de Botella del Almacenamiento Compartido y Mitigaciones
- **Desafío:** Al tener múltiples instancias de `core-api` concurriendo sobre la misma base de datos operativa durante el pico de 10.000 apuestas/s, el cuello de botella físico se traslada a los bloqueos de fila de saldo de billetera y contención en la tabla de apuestas.
- **Estrategia de mitigación arquitectónica:**
  1. *Particionamiento lógico por usuario:* Las actualizaciones de saldo se bloquean estrictamente a nivel del registro individual de cada usuario (`SELECT FOR UPDATE` sobre la fila del usuario), evitando bloqueos de tabla. Como un usuario emite un número finito de apuestas, la contención ocurre por usuario y no globalmente.
  2. *Separación de lecturas y escrituras:* Las consultas masivas de cuotas estimadas, catálogo de medianos y perfiles de carreras son atendidas mediante réplicas de lectura y mecanismos de almacenamiento en caché en memoria, reservando el nodo primario de base de datos exclusivamente para inserciones de apuestas y débitos.
  3. *Aislamiento del Worker de Liquidación:* Durante la liquidación masiva posterior al cierre, el worker procesa las acreditaciones en bloques (*chunks*) con límites de concurrencia para no saturar las conexiones ni bloquear la base de datos transaccional si hay otra carrera abierta en paralelo.
