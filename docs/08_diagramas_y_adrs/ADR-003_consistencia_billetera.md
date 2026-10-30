<!-- BANNER:INICIO (bloque estetico; omitido en el PDF consolidado) -->
<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&height=170&color=6B0F1A&text=ADR-003%20%C2%B7%20CONSISTENCIA%20E%20IDEMPOTENCIA&fontColor=F4ECE4&fontSize=44&fontAlignY=34&desc=ACID%20local%2C%20idempotencia%20por%20apuesta%20y%20modelo%20de%20liquidaci%C3%B3n&descColor=E8B4B8&descAlignY=60"
       alt="Banner: ADR-003 · CONSISTENCIA E IDEMPOTENCIA"/>
</p>

<p align="center">
  <img src="https://64.media.tumblr.com/3254f08405664a04d3c5a65f765eb8c9/61bf168659dda322-50/s2048x3072/36c765a65bc72096e27e85823017367c0b9b48b2.pnj" alt="Ilustración conceptual de estrategia y competición en la academia" width="520"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Estructura-Contexto%20%C2%B7%20Opciones%20%C2%B7%20Decision%20%C2%B7%20Consecuencias-540B13?style=flat-square&logoColor=white" alt="Estructura: Contexto · Opciones · Decision · Consecuencias"/>
  <img src="https://img.shields.io/badge/Maximo-1%20pagina-6B0F1A?style=flat-square&logoColor=white" alt="Maximo: 1 pagina"/>
</p>


<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=rect&height=6&color=6B0F1A"
       alt=""/>
</p>

<!-- BANNER:FIN -->

# ADR-003: Consistencia Transaccional, Idempotencia y Modelo de Liquidación
**Proyecto:** La Gran Liga de Apuestas de Medianos EIA  
**Empresa:** Salchipapa Maker Racing S.A.S.  
**Estado:** `[x]` Aprobado por el usuario  
**Fecha:** 2026-10-27  

---

<!-- DIVISOR:INICIO (bloque estetico; omitido en el PDF consolidado) -->
<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=rect&height=6&color=6B0F1A" alt=""/>
</p>
<!-- DIVISOR:FIN -->

## 1. Contexto y Problema
La plataforma maneja EIA Coins bajo una ráfaga masiva de hasta 10.000 apuestas/s en los 30 segundos previos al cierre, exigiendo respuesta en menos de 1 segundo sin incurrir jamás en saldo negativo ni doble gasto. Se requiere además procesar la liquidación masiva de más de 1.000.000 de apuestas en menos de 15 minutos, garantizar idempotencia ante múltiples pulsaciones del usuario o reintentos de red, distribuir los residuos fraccionarios de la bolsa común de forma justa y matemáticamente exacta, y definir el comportamiento del sistema cuando ningún apostador acierta al mediano ganador.

<!-- DIVISOR:INICIO (bloque estetico; omitido en el PDF consolidado) -->
<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=rect&height=6&color=6B0F1A" alt=""/>
</p>
<!-- DIVISOR:FIN -->

## 2. Opciones Consideradas
1. **Transacciones Distribuidas (2PC / XA):** Bloqueo en dos fases coordinando apuestas y billetera en bases de datos separadas.
2. **Patrón Saga en Ruta Crítica:** Aceptación eventual con llamadas asíncronas entre apuestas y billetera mediante transacciones compensatorias.
3. **Consistencia Local ACID en Núcleo Modular + Outbox + Algoritmo de Mayores Restos:** Validación de cierre, descuento de saldo y persistencia de apuesta en una misma transacción local en base de datos OLTP. Publicación asíncrona mediante Transactional Outbox. Reparto de premios mediante el algoritmo de mayores restos en centavos enteros con desempate determinista, y reembolso del 100% ante ausencia de ganadores sin alterar el ciclo deportivo de la carrera.

<!-- DIVISOR:INICIO (bloque estetico; omitido en el PDF consolidado) -->
<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=rect&height=6&color=6B0F1A" alt=""/>
</p>
<!-- DIVISOR:FIN -->

## 3. Decisión Tomada
Se adopta la **Opción 3**. La ruta crítica de admisión de apuestas opera bajo consistencia fuerte ACID local con bloqueos pesimistas a nivel de fila (`SELECT FOR UPDATE`) y restricción `CHECK (balance >= 0)`. La idempotencia se garantiza a tres niveles: en apuestas mediante `Idempotency-Key` en cabecera HTTP e índice `UNIQUE(user_id, idempotency_key)`, en premios mediante clave individual por apuesta `UNIQUE(bet_id, 'PRIZE_PAYOUT')`, y en consumidores Kafka mediante tabla de eventos procesados. Para el reparto de premios se adopta una precisión contable de dos decimales (centavos enteros) y el algoritmo de mayores restos con desempate determinista por `bet_id`, asegurando que la suma de premios y comisión coincida al centavo con la bolsa recaudada. Ante ausencia de ganadores, se devuelve el 100% de los fondos sin retener comisión, manteniendo el historial deportivo de la carrera con motivo `SIN_APUESTAS_GANADORAS`.

<!-- DIVISOR:INICIO (bloque estetico; omitido en el PDF consolidado) -->
<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=rect&height=6&color=6B0F1A" alt=""/>
</p>
<!-- DIVISOR:FIN -->

## 4. Consecuencias

### Lo que se gana:
- **Integridad contable absoluta:** Imposibilidad matemática de saldo negativo o duplicación de pagos por reintentos de workers o cliente.
- **Conservación exacta de la bolsa:** Cero pérdida o creación espuria de centavos; la regla determinista de mayores restos es 100% reproducible por el auditor.
- **Rendimiento predecible en borde:** Respuesta transaccional local en decenas de milisegundos sin latencias de red distribuidas.
- **Transparencia en devoluciones:** Diferenciación clara entre carreras canceladas y eventos deportivos válidos sin aciertos de usuarios.

### Lo que se sacrifica y límites:
- **Contención en cuentas activas:** Usuarios que apuestan masivamente en paralelo serializan sus transacciones por el bloqueo de fila de su billetera.
- **Cálculo previo centralizado:** La liquidación exige una fase analítica global para determinar los mayores restos antes de generar los lotes de dispersión.
- **Complejidad de almacenamiento inmutable:** La retención de auditoría a 5 años requiere políticas WORM y sellado criptográfico en almacenes dedicados fuera del motor OLTP.

<!-- DIVISOR:INICIO (bloque estetico; omitido en el PDF consolidado) -->
<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&height=120&section=footer&color=6B0F1A" alt=""/>
</p>
<!-- DIVISOR:FIN -->
