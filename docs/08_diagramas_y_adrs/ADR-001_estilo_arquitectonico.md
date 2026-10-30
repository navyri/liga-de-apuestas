<!-- BANNER:INICIO (bloque estetico; omitido en el PDF consolidado) -->
<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&height=170&color=6B0F1A&text=ADR-001%20%C2%B7%20ESTILO%20ARQUITECTONICO&fontColor=F4ECE4&fontSize=44&fontAlignY=34&desc=Monolito%20vs%20monolito%20modular%20vs%20microservicios%20vs%20h%C3%ADbrida&descColor=E8B4B8&descAlignY=60"
       alt="Banner: ADR-001 · ESTILO ARQUITECTONICO"/>
</p>

<p align="center">
  <img src="https://64.media.tumblr.com/3254f08405664a04d3c5a65f765eb8c9/61bf168659dda322-50/s2048x3072/36c765a65bc72096e27e85823017367c0b9b48b2.pnj" alt="Ilustración conceptual de estrategia y competición en la academia" width="520"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Estructura-Contexto%20%C2%B7%20Opciones%20%C2%B7%20Decision%20%C2%B7%20Consecuencias-540B13?style=flat-square&logoColor=white" alt="Estructura: Contexto · Opciones · Decision · Consecuencias"/>
  <img src="https://img.shields.io/badge/Maximo-1%20pagina-6B0F1A?style=flat-square&logoColor=white" alt="Maximo: 1 pagina"/>
  <img src="https://img.shields.io/badge/Universidad-EIA-8B1E2D?style=flat-square&logoColor=white" alt="Universidad: EIA"/>
</p>


<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=rect&height=6&color=6B0F1A"
       alt=""/>
</p>

<!-- BANNER:FIN -->

# ADR-001: Selección del Estilo Arquitectónico
**Proyecto:** La Gran Liga de Apuestas de Medianos EIA  
**Empresa:** Salchipapa Maker Racing S.A.S.  
**Estado:** `[x]` Aprobado por el usuario  
**Fecha:** 2026-10-27  

---

## 1. Contexto y Problema
Salchipapa Maker Racing S.A.S. requiere diseñar la arquitectura de la plataforma de apuestas mutuas sobre carreras de medianos. El sistema debe gestionar una carga base de 500 usuarios y absorber picos de hasta 100.000 usuarios concurrentes con ráfagas de 10.000 apuestas por segundo durante los 30 segundos previos al cierre. La solución debe informar la aceptación o rechazo de cada apuesta en menos de 1 segundo, garantizar que ningún saldo quede negativo ni se duplique un débito, asegurar el cierre estricto según el reloj del servidor y cumplir la regla directiva de Dyllan: *"No quiero pagar una infraestructura de Netflix para una carrera de cinco medianos"*.

## 2. Opciones Consideradas
1. **Monolito Tradicional:** Sistema acoplado en un único proceso desplegable con base de datos compartida y sin fronteras modulares estrictas.
2. **Monolito Modular Completo:** Todas las capacidades agrupadas en un único artefacto desplegable replicable horizontalmente, estructurado internamente en módulos con límites y contratos de interfaz formales.
3. **Microservicios Puros:** Descomposición completa de las capacidades en 9 servicios autónomos con bases de datos privadas (*database-per-service*) y comunicación distribuida síncrona/asíncrona.
4. **Arquitectura Híbrida (Núcleo Modular Transaccional + Servicios Asíncronos Desacoplados):** Núcleo modular replicable para el flujo transaccional cohesivo (usuarios, medianos, carreras, apuestas, billetera), complementado con servicios/workers autónomos para procesos asíncronos desacoplados (notificaciones, analítica masiva y liquidación de premios).

## 3. Decisión Tomada
Se adopta la **Arquitectura Híbrida**. El flujo crítico de admisión y cobro se concentra en un Núcleo Modular Transaccional desplegado en instancias replicables, permitiendo diseñar la validación de saldo, el débito y el registro de la apuesta dentro de una misma transacción local atómica (ACID). Las capacidades de Notificaciones, Analítica/Estadísticas y Liquidación masiva se segregan en unidades y procesos especializados fuera de la ruta crítica de aceptación.

## 4. Justificación del Descarte de Alternativas
- **Descarte de Microservicios Puros:** La separación física de apuestas y billetera impondría coordinación distribuida (patrón Saga con transacciones compensatorias) en la ruta crítica, aumentando la exposición a inconsistencias y saldos negativos bajo concurrencia masiva. Asimismo, la sobrecarga operativa y de infraestructura asociada contraviene la política de costo y simplicidad exigida por la dirección.
- **Descarte del Monolito Tradicional:** La ausencia de límites físicos permitiría que la saturación en proveedores externos de notificación o la carga pesada de reportes analíticos degrade el hilo transaccional y bloquee la admisión de apuestas, violando el requisito de aislamiento de fallos.

## 5. Consecuencias

### Lo que se gana:
- **Consistencia atómica simplificada:** Eliminación de protocolos de coordinación distribuida (2PC o Sagas) en el flujo crítico de débito y apuesta.
- **Aislamiento efectivo de fallas:** La caída o lentitud de notificaciones no impacta la recepción ni confirmación de apuestas.
- **Aislamiento de carga analítica:** Millones de eventos analíticos se ingieren y consultan en un almacén optimizado sin canibalizar recursos transaccionales.
- **Gobernanza de costos:** Infraestructura moderada, mantenible y proporcional a la escala de la organización.

### Lo que se sacrifica y límites:
- **Disciplina modular obligatoria:** Requiere control riguroso del código para impedir dependencias circulares o violaciones de encapsulamiento entre módulos del núcleo.
- **Contención en almacenamiento compartido:** Al replicar el núcleo transaccional en múltiples instancias, el cuello de botella se traslada a la base de datos operativa, exigiendo particionamiento por usuario, bloqueos a nivel de fila y separación estricta de lecturas y escrituras que deberán validarse en las etapas de persistencia y escalabilidad.
