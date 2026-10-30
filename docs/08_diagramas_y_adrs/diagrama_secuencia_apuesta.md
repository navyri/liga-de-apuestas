<!-- BANNER:INICIO (bloque estetico; omitido en el PDF consolidado) -->
<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&height=170&color=6B0F1A&text=DIAGRAMA%20DE%20SECUENCIA%20DE%20UNA%20APUESTA&fontColor=F4ECE4&fontSize=44&fontAlignY=34&desc=Desde%20APOSTAR%20hasta%20la%20confirmaci%C3%B3n%2C%20con%20descuento%20en%20billetera&descColor=E8B4B8&descAlignY=60"
       alt="Banner: DIAGRAMA DE SECUENCIA DE UNA APUESTA"/>
</p>

<p align="center">
  <img src="https://64.media.tumblr.com/3254f08405664a04d3c5a65f765eb8c9/61bf168659dda322-50/s2048x3072/36c765a65bc72096e27e85823017367c0b9b48b2.pnj" alt="Ilustración conceptual de estrategia y competición en la academia" width="520"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Formato-Mermaid-540B13?style=flat-square&logoColor=white" alt="Formato: Mermaid"/>
  <img src="https://img.shields.io/badge/Entregable-Punto%204%20del%20enunciado-6B0F1A?style=flat-square&logoColor=white" alt="Entregable: Punto 4 del enunciado"/>
  <img src="https://img.shields.io/badge/Universidad-EIA-8B1E2D?style=flat-square&logoColor=white" alt="Universidad: EIA"/>
</p>


<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=rect&height=6&color=6B0F1A"
       alt=""/>
</p>

<!-- BANNER:FIN -->

# DIAGRAMA DE SECUENCIA: FLUJO COMPLETO DE UNA APUESTA
**Caso:** La Gran Liga de Apuestas de Medianos EIA  
**Organización:** Salchipapa Maker Racing S.A.S.  
**Entregable Oficial:** Punto 4 del PDF (págs. 17, 18)  
**Artefacto:** `P1-ART-009B`  

---

```mermaid
sequenceDiagram
    autonumber
    actor U as 👤 Apostador (Cliente)
    participant GW as 🛡️ API Gateway / WAF
    participant CORE as 🏛️ Núcleo Modular (core-api)
    participant DB as 💾 Base de Datos OLTP (PostgreSQL)
    participant RELAY as ⚙️ Outbox Relay
    participant KAFKA as ⚡ Apache Kafka
    participant NOTIF as 📬 Servicio Notificaciones

    %% 1. Inicio de la Petición
    U->>+GW: POST /api/v1/bets<br/>{raceId, racerId, amount}<br/>Header: Idempotency-Key
    
    %% 2. Filtros Perimetrales
    Note over GW: 1. Rate Limiting (Token Bucket)<br/>2. Validación JWT & Claims RBAC
    
    %% 3. Enrutamiento al Núcleo
    GW->>+CORE: Enrutamiento gRPC/HTTP-2 con contexto
    
    %% 4. Transacción Local ACID
    Note over CORE,DB: INICIO DE TRANSACCIÓN LOCAL ACID
    CORE->>DB: BEGIN TRANSACTION
    
    %% 5. Verificación de Idempotencia
    CORE->>DB: SELECT response FROM bets_idempotency WHERE key = :idemp_key
    alt Clave Ya Procesada (Reintento de Red)
        DB-->>CORE: Retorna respuesta previa
        CORE-->>GW: HTTP 200 OK (Cacheada)
        GW-->>U: HTTP 200 OK (Apuesta ya confirmada)
    end
    
    %% 6. Validación de Cierre Atómico
    CORE->>DB: SELECT status, start_time FROM races WHERE id = :raceId
    alt Hora Servidor >= Hora Inicio Carrera O Estado != 'ABIERTA'
        DB-->>CORE: Carrera Cerrada
        CORE->>DB: ROLLBACK
        CORE-->>GW: HTTP 409 Conflict (CARRERA_CERRADA)
        GW-->>U: HTTP 409 Rechazada: Fuera de Tiempo
    end

    %% 7. Bloqueo de Billetera y Verificación de Saldo
    CORE->>DB: SELECT balance FROM wallets WHERE user_id = :uid FOR UPDATE
    alt Saldo Insuficiente (balance < amount)
        DB-->>CORE: Saldo Insuficiente
        CORE->>DB: ROLLBACK
        CORE-->>GW: HTTP 422 Unprocessable Entity
        GW-->>U: HTTP 422 Rechazada: Saldo Insuficiente
    end

    %% 8. Débito, Registro y Outbox en la Misma Transacción
    Note over CORE,DB: OPERACIÓN ATÓMICA CONJUNTA
    CORE->>DB: UPDATE wallets SET balance = balance - amount WHERE user_id = :uid
    CORE->>DB: INSERT INTO bets (id, user_id, race_id, racer_id, amount, created_at)
    CORE->>DB: INSERT INTO bets_idempotency (user_id, idemp_key, bet_id, response)
    CORE->>DB: INSERT INTO outbox_events (topic, payload, status='PENDING')
    
    %% 9. Commit Local y Respuesta Inmediata
    CORE->>DB: COMMIT TRANSACTION
    DB-->>CORE: Confirmación Exitosa (Commit OK)
    CORE-->>-GW: HTTP 201 Created {status: 'ACEPTADA', betId, newBalance}
    GW-->>-U: HTTP 201 Created (Confirmación en Pantalla < 1s)

    %% 10. Flujo Asíncrono Desacoplado (Fuera de la Ruta Crítica)
    Note over RELAY,NOTIF: PROCESAMIENTO ASÍNCRONO DESACOPLADO
    RELAY->>+DB: Leer eventos 'PENDING' en outbox_events
    DB-->>-RELAY: Lista de eventos
    RELAY->>+KAFKA: Publicar en topic: apuestas.aceptadas (Key: user_id)
    KAFKA-->>-RELAY: ACK (Confirmado por Kafka)
    RELAY->>DB: UPDATE outbox_events SET status='PUBLISHED'
    
    KAFKA--)NOTIF: Consumo por Consumer Group 'notificaciones'
    NOTIF-->>U: Notificación Push / Correo ("¡Apuesta aceptada!")
```
