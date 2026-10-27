# ETAPA P1-7: SEGURIDAD, CONTROL DE ACCESO Y GOBERNANZA DE COSTOS
**Caso:** La Gran Liga de Apuestas de Medianos EIA  
**Organización:** Salchipapa Maker Racing S.A.S.  
**Artefacto:** `P1-ART-008`  
**Versión:** `v1.0`  
**Estado:** `[x]` Consolidado y verificado por revisión autónoma  

---

## P1-7.1: AUTENTICACIÓN, AUTORIZACIÓN Y MATRIZ RBAC (PDF pág. 4, 12)

Para proteger las operaciones que involucran EIA Coins y credenciales de usuario, se diseña un esquema de seguridad perimetral basado en estándares de la industria:

1. **Autenticación Basada en Tokens Criptográficos (JWT Stateless):**
   - El usuario se autentica mediante `POST /api/v1/auth/login`. Tras validar el hash seguro de la contraseña (Argon2id / bcrypt), el servicio emite un token de acceso firmado digitalmente (EdDSA / RS256) con tiempo de expiración corto (15 a 30 minutos) y un *refresh token* opaco de rotación persistido de forma segura.
   - El token contiene las credenciales de identidad (`sub: user_id`) y el rol asignado (`role`), permitiendo a las réplicas del Núcleo Modular validar la firma y permisos localmente en memoria sin consultar a la base de datos en cada una de las 10.000 req/s.
2. **Matriz de Control de Acceso Basado en Roles (RBAC):**

| Capacidad / Endpoint | Apostador | Operador de Carrera | Administrador | Auditor |
| :--- | :---: | :---: | :---: | :---: |
| **Consultar carreras y catálogo de medianos** | Permitido | Permitido | Permitido | Permitido |
| **Emitir apuesta (`POST /bets`)** | **Permitido** | Denegado | Denegado | Denegado |
| **Consultar saldo y movimientos propios** | **Permitido** | Denegado | Denegado | Denegado |
| **Programar carrera y pistas (`POST /races`)** | Denegado | **Permitido** | Permitido | Denegado |
| **Publicar resultado oficial (`POST /results`)**| Denegado | **Permitido** | Denegado | Denegado |
| **Bloquear / Desbloquear usuarios** | Denegado | Denegado | **Permitido** | Denegado |
| **Consultar registros de auditoría y trazas** | Denegado | Denegado | Solo métricas | **Solo Lectura Exclusivo** |
| **Modificar saldos o apuestas directamente** | **Prohibido** | **Prohibido** | **Prohibido** | **Prohibido** |

---

## P1-7.2: PROTECCIÓN DE APIS, LIMITACIÓN DE TASA (RATE LIMITING) Y ANTI-BOT

En la final de la Copa Intersemestral, el pico de 10.000 apuestas/s puede ser agravado por scripts maliciosos o usuarios recargando compulsivamente. Se establecen mecanismos de protección perimetral en el API Gateway:
1. **Rate Limiting Multinivel (Algoritmo Token Bucket / Leaky Bucket):**
   - *Por Usuario Autenticado:* Límite de **5 apuestas por segundo por usuario** (con ráfagas de hasta 10). Suficiente para permitir apuestas múltiples legítimas en distintos medianos, pero bloqueando scripts agresivos que monopolicen el pool de conexiones.
   - *Por Dirección IP:* Límite sobre endpoints públicos de consulta (`GET /races`, `GET /odds`) de 50 peticiones por minuto por IP para mitigar raspado (*scraping*) de cuotas.
   - *Respuesta a Excesos:* HTTP `429 Too Many Requests` con cabecera `Retry-After: <segundos>`.
2. **Mitigación de Bots y Apuestas Masivas al Cierre:**
   - Detección en tiempo real de huellas digitales de dispositivos y firmas de cliente sospechosas.
   - Bloqueo preventivo de múltiples cuentas autenticadas operando concurrentemente desde una misma IP en los últimos 10 segundos antes del corte.

---

## P1-7.3: GESTIÓN DE CIFRADO Y CREDENCIALES

1. **Cifrado en Tránsito:**
   - Todo el tráfico externo (cliente hacia API Gateway) exige **TLS 1.3** estricto con renovación automática de certificados.
   - El tráfico interno en la red privada (entre Gateway, `core-api`, Kafka y base de datos) utiliza mTLS (*Mutual TLS*) o red virtual aislada (VPC/VNet con cifrado nativo de infraestructura).
2. **Cifrado en Reposo:**
   - Bases de datos operativas y almacenes analíticos operan con cifrado de volumen a nivel de disco (AES-256).
   - Datos personales sensibles y claves de billetera se almacenan en reposo cifrados mediante claves custodiadas en un servicio de gestión de secretos (*KMS / Secret Manager*).
3. **Manejo Seguro de Credenciales:**  
   Prohibición absoluta de almacenar secretos, cadenas de conexión o tokens en el código fuente, archivos del repositorio o variables de entorno expuestas. Las credenciales se inyectan en tiempo de ejecución desde un gestor de secretos administrado.

---

## P1-7.4: REGISTRO DE ACCIONES ADMINISTRATIVAS Y AUDITORÍA FORENSE (PDF pág. 12)

Toda mutación administrativa u operativa que afecte saldos, usuarios o estados de carrera genera una traza obligatoria:
- **Campos del Registro de Auditoría:** `audit_id`, `operator_id`, `action_type`, `resource_id`, `before_state`, `after_state`, `ip_address`, `timestamp`.
- **Inalterabilidad de la Traza:** La inserción de la auditoría administrativa ocurre en la misma transacción local o se despacha hacia el log seguro append-only. Ningún usuario, incluido el Administrador, cuenta con privilegios SQL de `UPDATE` o `DELETE` sobre las tablas de auditoría.

---

## P1-7.5: SEGMENTACIÓN DE RED: COMPONENTES PÚBLICOS VS. PRIVADOS (PDF pág. 12)

```text
  RED PÚBLICA (INTERNET)
      │
      ▼ (HTTPS / TLS 1.3 - Puerto 443)
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │  ZONA DESMILITARIZADA (DMZ) / COMPONENTES PÚBLICOS                          │
 │  - Cloud CDN (Caché de contenido estático web y fichas de medianos)         │
 │  - API Gateway / Balanceador de Carga (Rate limiting, terminación TLS, WAF) │
 └──────────────────────────────────────┬──────────────────────────────────────┘
                                        │ (Red Privada / VPC Peering)
  RED PRIVADA (ZONA AISLADA - SIN ACCESO DIRECTO DESDE INTERNET)
 ┌──────────────────────────────────────┴──────────────────────────────────────┐
 │  CAPA DE CÓMPUTO PRIVADA                                                    │
 │  - Instancias escalables del Núcleo Modular (core-api)                      │
 │  - Worker de Liquidación Masiva y Devoluciones (settlement-worker)          │
 │  - Servicio de Notificaciones (notification-service)                        │
 │  - Servicio de Analítica e Ingesta (analytics-service)                      │
 ├─────────────────────────────────────────────────────────────────────────────┤
 │  CAPA DE PERSISTENCIA Y MENSAJERÍA PRIVADA                                  │
 │  - Clúster de Apache Kafka (Brokers y Zookeeper/KRaft)                      │
 │  - Base de Datos Transaccional OLTP (PostgreSQL Primario + Réplica)         │
 │  - Almacén Analítico Columnar OLAP (ClickHouse / BigQuery)                  │
 │  - Almacén de Auditoría Inmutable (WORM / Object Lock)                       │
 └─────────────────────────────────────────────────────────────────────────────┘
```

- **Componentes Públicos:** Exclusivamente el CDN y el API Gateway/WAF. Ningún microservicio ni base de datos expone puertos directos a Internet.
- **Componentes Privados:** Todas las instancias de cómputo (`core-api`, workers, analítica), el clúster de Kafka y las bases de datos transaccionales y analíticas residen en subredes privadas sin IP pública accesible.

---

## P1-7.6 Y P1-7.7: GOBERNANZA DE COSTOS, SERVICIOS ADMINISTRADOS Y JUSTIFICACIÓN (PDF pág. 12-13)

### 1. Cumplimiento de la Directriz de Dyllan ("No pagar infraestructura de Netflix")
El diseño arquitectónico adoptado erradica activamente la sobreingeniería:
- **Consolidación en 1 Solo Servicio Core Replicable:** En lugar de operar 9 microservicios con 9 bases de datos, registros de servicios y balanceadores independientes, el Núcleo Modular agrupa las capacidades transaccionales en un único artefacto desplegable (`core-api`).
- **Broker Único:** Un solo clúster de Apache Kafka cubre streaming, analítica, auditoría y lotes de liquidación, evitando la duplicidad de costes de operar RabbitMQ simultáneamente.
- **Servicios Administrados Justificados:**  
  Es razonable utilizar servicios administrados (ej. Base de Datos Administrada y Kafka Administrado) para transferir la carga de alta disponibilidad, parches de seguridad, conmutación por error y respaldos automáticos, reduciendo a cero la necesidad de un equipo de operaciones dedicado 24/7.
- **Apagado y Elasticidad en Horas Valle:** La carga extrema solo ocurre durante torneos semestrales específicos. La infraestructura de cómputo escala a un mínimo económico (ej. 2 instancias pequeñas) en operación normal de 500 usuarios, y escala elásticamente solo durante los días de competencia de la Liga.
