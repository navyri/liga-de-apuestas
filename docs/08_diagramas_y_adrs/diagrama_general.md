# DIAGRAMA GENERAL DE ARQUITECTURA
**Caso:** La Gran Liga de Apuestas de Medianos EIA  
**Organización:** Salchipapa Maker Racing S.A.S.  
**Entregable Oficial:** Punto 3 del PDF (págs. 17, 18)  
**Artefacto:** `P1-ART-009A`  

---

```mermaid
graph TD
    %% Estilos de Nodos
    classDef clientStyle fill:#F4ECE4,stroke:#100D10,stroke-width:2px,color:#100D10;
    classDef edgeStyle fill:#6B0F1A,stroke:#100D10,stroke-width:2px,color:#F4ECE4;
    classDef coreStyle fill:#8B1E2D,stroke:#100D10,stroke-width:2px,color:#F4ECE4;
    classDef dbStyle fill:#540B13,stroke:#100D10,stroke-width:2px,color:#F4ECE4;
    classDef brokerStyle fill:#100D10,stroke:#C6A66B,stroke-width:2px,color:#F4ECE4;
    classDef asyncWorker fill:#3D080E,stroke:#C6A66B,stroke-width:2px,color:#F4ECE4;

    %% 1. CLIENTES (Dispositivos Externos)
    subgraph CLIENTES ["👥 CAPA DE CLIENTES (PÚBLICA)"]
        C1["Apostador (Web / App Móvil)"]:::clientStyle
        C2["Operador de Carrera (Consola Web)"]:::clientStyle
        C3["Auditor (Consola de Solo Lectura)"]:::clientStyle
    end

    %% 2. BORDE Y SEGURIDAD (DMZ)
    subgraph BORDE ["🛡️ ZONA DESMILITARIZADA (DMZ)"]
        GW["API Gateway / WAF / Reverse Proxy<br/>- Terminación TLS 1.3<br/>- Rate Limiting (Token Bucket)<br/>- Validación Criptográfica JWT"]:::edgeStyle
    end

    %% 3. NÚCLEO MODULAR TRANSACCIONAL (VPC Privada)
    subgraph CORE ["🏛️ NÚCLEO TRANSACCIONAL MODULAR (core-api en Réplicas Stateless)"]
        direction TB
        M_AUTH["Módulo Usuarios & Auth<br/>(RBAC / Claims)"]:::coreStyle
        M_RACERS["Módulo Medianos<br/>(Catálogo / Fichas)"]:::coreStyle
        M_RACES["Módulo Carreras<br/>(Ciclo / Reloj Servidor)"]:::coreStyle
        M_BETS["Módulo Apuestas<br/>(Admisión / Idempotencia)"]:::coreStyle
        M_WALLET["Módulo Billetera<br/>(EIA Coins / Débito)"]:::coreStyle
        M_OUTBOX["Módulo Outbox<br/>(Tabla de Eventos)"]:::coreStyle
    end

    %% 4. PERSISTENCIA TRANSACCIONAL
    subgraph PERSISTENCIA ["💾 CAPA DE PERSISTENCIA OPERATIVA (OLTP)"]
        DB_PRIMARY[("PostgreSQL Primario (ACID)<br/>- Bloqueo FOR UPDATE<br/>- Inserción Atómica Apuesta<br/>- Tabla outbox_events")]:::dbStyle
        DB_REPLICA[("PostgreSQL Réplica Lectura<br/>- Cuotas Estimadas<br/>- Catálogo de Medianos")]:::dbStyle
    end

    %% 5. MENSAJERÍA Y STREAMING
    subgraph MENSAJERIA ["⚡ APACHE KAFKA (BROKER DISTRIBUIDO)"]
        T_BETS["Topic: apuestas.aceptadas<br/>(Key: race_id)"]:::brokerStyle
        T_RACES["Topic: carreras.eventos<br/>(Key: race_id)"]:::brokerStyle
        T_SETTLE["Topic: liquidacion.lotes<br/>(Key: batch_id)"]:::brokerStyle
    end

    %% 6. COMPONENTES Y CONSUMIDORES DESACOPLADOS
    subgraph ASINCRONOS ["⚙️ COMPONENTES Y WORKERS FUERA DE LA RUTA CRÍTICA"]
        W_SETTLE["Worker de Liquidación Masiva<br/>- Algoritmo Mayores Restos<br/>- Generador de Lotes"]:::asyncWorker
        W_DISPERS["Workers Dispersores de Balance<br/>- Acreditación en Lotes<br/>- Idempotencia UNIQUE(bet_id)"]:::asyncWorker
        S_NOTIF["Servicio de Notificaciones<br/>- Correo, Push, App<br/>- Falla NO bloquea Core"]:::asyncWorker
        S_ANALYTICS["Servicio de Analítica & Stats<br/>- Ingesta Diaria Millones Regs<br/>- Almacén Columnar OLAP"]:::asyncWorker
        S_AUDIT["Almacén Inmutable de Auditoría<br/>- Retención 5 Años WORM<br/>- Hashes SHA-256"]:::asyncWorker
    end

    %% Relaciones Síncronas (Flecha Sólida ===)
    C1 == "HTTPS / REST (POST /bets)<br/>[Síncrono < 1s]" ===> GW
    C2 == "HTTPS / REST (POST /results)<br/>[Síncrono]" ===> GW
    C3 == "HTTPS / REST (GET /audit)<br/>[Síncrono]" ===> DB_REPLICA
    GW == "gRPC / HTTP/2 Interno<br/>[Síncrono]" ===> CORE
    M_BETS == "Transacción Local ACID<br/>[SELECT FOR UPDATE]" ===> DB_PRIMARY
    M_WALLET == "Débito Atómico en Saldo" ===> DB_PRIMARY
    M_OUTBOX == "INSERT outbox_events" ===> DB_PRIMARY
    DB_PRIMARY -.->|"Replicación WAL Síncrona"| DB_REPLICA

    %% Relaciones Asíncronas (Flecha Punteada -.-)
    DB_PRIMARY -.->|"Outbox Relay / CDC"| MENSAJERIA
    T_BETS -.->|"Consumer Group: notificaciones"| S_NOTIF
    T_BETS -.->|"Consumer Group: analitica"| S_ANALYTICS
    T_BETS -.->|"Consumer Group: auditoria"| S_AUDIT
    T_RACES -.->|"ResultadoOficialPublicado"| W_SETTLE
    W_SETTLE -.->|"Lotes Particionados (Key: batch_id)"| T_SETTLE
    T_SETTLE -.->|"Consumer Group: dispersores"| W_DISPERS
    W_DISPERS == "Acreditación Contable en Lote<br/>[ACID en Wallets]" ===> DB_PRIMARY
```

### Leyenda y Diferenciación Visual Exigida (PDF pág. 17):
- **Línea Sólida (`===`):** **Comunicación Síncrona** en la ruta crítica del usuario y operaciones administrativas interactivas.
- **Línea Punteada (`-.->`):** **Comunicación Asíncrona** basada en eventos a través de Apache Kafka y procesos en segundo plano.
