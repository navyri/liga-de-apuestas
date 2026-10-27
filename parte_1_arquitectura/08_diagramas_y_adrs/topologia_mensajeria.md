# TOPOLOGÍA DE MENSAJERÍA: APACHE KAFKA
**Caso:** La Gran Liga de Apuestas de Medianos EIA  
**Organización:** Salchipapa Maker Racing S.A.S.  
**Entregable Oficial:** Punto 7 del PDF (págs. 14, 18)  
**Artefacto:** `P1-ART-009C`  

---

```mermaid
graph TD
    %% Estilos
    classDef prodStyle fill:#8B1E2D,stroke:#100D10,stroke-width:2px,color:#F4ECE4;
    classDef topicStyle fill:#100D10,stroke:#C6A66B,stroke-width:2px,color:#F4ECE4;
    classDef groupStyle fill:#540B13,stroke:#C6A66B,stroke-width:2px,color:#F4ECE4;
    classDef consumerStyle fill:#3D080E,stroke:#F4ECE4,stroke-width:1px,color:#F4ECE4;

    %% Productores
    subgraph PRODUCTORES ["🚀 PRODUCTORES (PRODUCERS)"]
        P_CORE["Núcleo Modular / Outbox Relay<br/>(Transactional Outbox)"]:::prodStyle
        P_SETTLE["Worker de Liquidación<br/>(Generador de Lotes)"]:::prodStyle
    end

    %% Tópicos y Particiones
    subgraph TOPICS ["⚡ CLÚSTER DE APACHE KAFKA (TOPICS & PARTITIONS)"]
        subgraph T1 ["Topic: apuestas.aceptadas (8 Particiones | Key: race_id)"]
            T1_P["P0 | P1 | P2 | P3 | P4 | P5 | P6 | P7"]:::topicStyle
        end
        subgraph T2 ["Topic: carreras.eventos (4 Particiones | Key: race_id)"]
            T2_P["P0 | P1 | P2 | P3"]:::topicStyle
        end
        subgraph T3 ["Topic: liquidacion.lotes (8 Particiones | Key: batch_id)"]
            T3_P["P0 | P1 | P2 | P3 | P4 | P5 | P6 | P7"]:::topicStyle
        end
        subgraph T4 ["Topic: notificaciones.dlt (Dead Letter Topic)"]
            T4_P["DLT - Mensajes Fallidos tras 3 Reintentos"]:::topicStyle
        end
    end

    %% Grupos de Consumidores
    subgraph GRUPOS ["👥 GRUPOS DE CONSUMIDORES (CONSUMER GROUPS)"]
        subgraph CG_CUOTAS ["Group: cuotas-dinamicas-workers"]
            C_CUOTAS["Workers de Cálculo de Cuotas en Vivo<br/>(Lectura secuencial por carrera)"]:::consumerStyle
        end
        subgraph CG_NOTIF ["Group: notificaciones-service"]
            C_NOTIF["Consumidores Multicanal<br/>(Despacho Push / Correo / App)"]:::consumerStyle
        end
        subgraph CG_ANALYTICS ["Group: analitica-ingesta-diaria"]
            C_ANALYTICS["Consumidores Micro-Lotes<br/>(Alimentación Almacén OLAP)"]:::consumerStyle
        end
        subgraph CG_AUDIT ["Group: auditoria-inmutable"]
            C_AUDIT["Consumidores de Auditoría<br/>(Sellado WORM / Hashes SHA-256)"]:::consumerStyle
        end
        subgraph CG_DISPERS ["Group: dispersores-premios-billetera"]
            C_DISPERS["Workers Acreditadores de Balance<br/>(Abono atómico con orden por user_id)"]:::consumerStyle
        end
    end

    %% Flujos de Publicación
    P_CORE -->|"Publica ApuestaAceptada"| T1_P
    P_CORE -->|"Publica CarreraIniciada / Finalizada / ResultadoOficial"| T2_P
    P_SETTLE -->|"Publica Lotes (batch_id)"| T3_P

    %% Flujos de Consumo Independiente (Offsets Desacoplados)
    T1_P -.->|"Lectura por Offset Propio"| CG_CUOTAS
    T1_P -.->|"Lectura por Offset Propio"| CG_NOTIF
    T1_P -.->|"Lectura por Offset Propio"| CG_ANALYTICS
    T1_P -.->|"Lectura por Offset Propio"| CG_AUDIT

    T2_P -.->|"Disparador de Liquidación"| P_SETTLE
    T2_P -.->|"Alertas de Eventos de Carrera"| CG_NOTIF

    T3_P -.->|"Consumo Paralelo de Lotes"| CG_DISPERS
    CG_NOTIF -.->|"Fallo tras 3 Reintentos"| T4_P
```
