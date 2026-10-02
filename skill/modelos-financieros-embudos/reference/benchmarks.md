# Benchmarks y umbrales de decisión

El orden de evaluación (macro → fugas por porcentaje → costos relativos), los pisos de ROAS por tipo de embudo y los percentiles por paso están en `umbrales.md`; este archivo guarda las tablas de referencia. Dos reglas antes de cualquier número. **Primera: el umbral de cada métrica es el promedio propio del usuario** (la mediana de sus últimas 4 semanas, o el último mes de su campaña madre), con 20 a 30 % de tolerancia: igual o mejor que su promedio es verde; hasta 20 a 30 % peor, amarillo; más que eso, rojo. No se inventan umbrales: cada escenario es distinto. **Segunda: los umbrales de costo dependen del nicho, y el nicho se ve en el CPM.** Un CPL de 1 con un CPM de 3 y un CPL de 10 con un CPM de 25 son el mismo embudo: lo comparable no es el CPL, es cuántas unidades salen por cada 1.000 impresiones (CPL ÷ CPM). Los rangos de mercado de este archivo sirven solo para arrancar sin históricos, se dicen como "punto de partida" y se reemplazan por los números del usuario en cuanto tiene 4 semanas.

## 1. Lo que más importa, en orden, con su umbral

| # | Métrica | Cómo se calcula | Verde | Amarillo | Rojo | Qué hacer si no está en verde |
|---|---|---|---|---|---|---|
| 1 | **Macro: ¿gana plata y el ROAS está sobre el piso?** | ganancia del período (cash neto − costos por unidad − fijos − inversión) y ROAS sobre cash neto contra los pisos de su tipo de embudo (`umbrales.md` § 1): escala 1,5 evergreen / 1,7 lanzamiento (objetivo 2,0); absoluto 1,3 | gana y ROAS ≥ piso de escala | gana, ROAS entre 1,3 y el piso de escala | pierde, o ROAS < 1,3 | Rojo: no invertir más hasta cerrar la fuga principal; si el front pierde, pulir la oferta del front. Amarillo: sostener, no escalar, mejorar lo mejorable |
| 2 | **Fugas en la cadena** (porcentaje entre pasos) | cada conversión contra los percentiles de `umbrales.md` § 2 y contra tu promedio propio (20 a 30 % de tolerancia) | todos los pasos en la mediana o más (y no peor que tu promedio) | algún paso entre p25 y la mediana | algún paso bajo p25, o más de 30 % bajo tu promedio | Cerrar la fuga principal (la más lejos de la mediana; a igual brecha, la más arriba del embudo) antes de escalar: ganar más sin pagar más |
| 3 | **Ganancia por visita** (la métrica más valiosa: resume todo lo que pasa después de la página) | ganancia del período ÷ visitas; su par es el costo por visita | igual o mejor que tu promedio | hasta 20 a 30 % por debajo de tu promedio | más que eso, o negativa | Si el costo por visita está en verde, el problema está después de la página: es una fuga |
| 4 | **Costo por unidad** (CPL, costo por visita, costo por entrada), **solo relativo** | contra tu techo (valor de la unidad en tu cash neto) y tu objetivo (techo ÷ 1,3); contra tu CPL promedio; en relación a tu CPM (unidades por cada 1.000 impresiones). Nunca contra un número absoluto | costo ≤ objetivo y ≤ tu promedio | entre objetivo y techo, o hasta 20 a 30 % peor que tu promedio | costo > techo, o más de 30 % peor que tu promedio | CPM → CTR → clic a visita → conversión de la landing, en ese orden. Nunca "bajar presupuesto". CPL subiendo dos días seguidos = anuncios nuevos hoy |
| 5 | **Testeo** (¿estás alimentando el embudo?) | anuncios nuevos por semana contra tu ritmo; frecuencia contra la habitual; % del presupuesto en testeo; edad del ganador principal | tu ritmo o más; frecuencia igual o menor | 20 a 30 % menos piezas, o frecuencia subiendo | 0 anuncios nuevos en 7 días con el CPL subiendo; frecuencia más de 30 % sobre la habitual | Producir y publicar todos los días (sección 3) |
| 6 | **Cash contra facturado** | cobranza por mes y reembolsos contra tus promedios; ROAS de caja del primer mes | como siempre; el primer mes cubre la pauta siguiente | cobranza menor a la planificada; reembolsos subiendo | reembolsos más de 30 % sobre lo habitual; caja necesaria mayor que la disponible | Cobranza y forma de pago, no tráfico |

Regla de lectura: se mira en este orden y se para en el primer rojo. Las reglas fijas son cuatro: ganancia negativa, ROAS bajo el piso de su tipo de embudo, conversión bajo p25 y costo por encima del techo propio. Todo lo demás se juzga contra el promedio de la persona.

## 2. Puntos de partida sin históricos

### 2a. Costos: siempre en relación al CPM

El CPM es el precio del nicho. Todo costo por paso se lee como una razón del CPM, o como unidades por cada 1.000 impresiones; así un embudo en un nicho de CPM 3 y otro en un nicho de CPM 25 se comparan con la misma vara.

| Costo | Fórmula | Malo | Aceptable | Bueno | Ganador |
|---|---|---|---|---|---|
| Costo por visita ÷ CPM (visitas por cada 1.000 impresiones) | 1 ÷ (CTR × clic→visita × 1.000) | > 12 % (menos de 8 visitas por mil) | 8 a 12 % (8 a 12 por mil) | 3 a 8 % (12 a 30 por mil) | < 3 % (más de 30 por mil) |
| CPL ÷ CPM (registros o leads por cada 1.000 impresiones) | 1 ÷ (CTR × clic→visita × conversión de la landing × 1.000) | > 67 % (menos de 1,5 por mil) | 40 a 67 % (1,5 a 2,5 por mil) | 25 a 40 % (2,5 a 4 por mil) | < 25 % (más de 4 por mil) |
| Costo por entrada ÷ CPM (webinar pago) | 1 ÷ (visitas por mil × visita→entrada) | > 5 veces el CPM | 3 a 5 veces | 1 a 3 veces | < 1 vez |
| Costo por asistente, por solicitud, por agenda, por comprador | CPL ÷ conversión acumulada hasta ese paso | se juzgan por las conversiones (2b) y por el techo de ese paso, nunca por un número absoluto | | | |

Ejemplos: CPM 3 → CPL bueno entre 0,75 y 1,20; CPM 10 → CPL bueno entre 2,50 y 4,00; CPM 25 → CPL bueno entre 6 y 10. Si el usuario dice "mi CPL es 10", la primera pregunta es "¿y tu CPM?".

### 2b. Conversiones (porcentajes: no dependen del CPM, sí del nicho; tráfico frío en español). El ROAS no es punto de partida: son los pisos fijos por tipo de embudo de `umbrales.md` § 1

| Embudo | Métrica | Malo | Aceptable | Bueno | Ganador |
|---|---|---|---|---|---|
| Todos | CTR al enlace | < 1 % | 1 a 1,8 % | 1,8 a 3 % | > 3 % |
| Todos | Clic → visita (carga de la página) | < 75 % | 75 a 85 % | 85 a 95 % | > 95 % |
| Todos | Retención a los 3 segundos (hook rate) | < 15 % | 15 a 20 % | 20 a 30 % | 40 a 55 % |
| Low-ticket | Visita → checkout | < 2 % | 2 a 3 % | 3 a 5 % | > 5 % |
| Low-ticket | Checkout → compra | < 15 % | 15 a 22 % | 22 a 30 % | > 30 % |
| Low-ticket | Visita → compra | < 0,5 % | 0,5 a 0,9 % | 0,9 a 1,5 % | > 1,5 % |
| Low-ticket | Bump tomado | < 15 % | 15 a 25 % | 25 a 35 % | > 35 % |
| Low-ticket | OTO 1 tomada | < 5 % | 5 a 9 % | 9 a 14 % | > 14 % |
| Low-ticket | AOV ÷ precio del principal | < 1,2 | 1,2 a 1,4 | 1,4 a 1,7 | > 1,7 |
| Webinar gratuito | Visita → registro | < 15 % | 15 a 22 % | 22 a 30 % | > 30 % |
| Webinar gratuito | Registro → grupo de WhatsApp | < 50 % | 50 a 65 % | 65 a 80 % | > 80 % |
| Webinar gratuito | Registro → en vivo | < 10 % | 10 a 15 % | 15 a 22 % | > 22 % |
| Webinar gratuito | Registro → replay | < 40 % | 40 a 60 % | 60 a 80 % | > 80 % |
| Webinar gratuito | En vivo → solicitud | < 5 % | 5 a 10 % | 10 a 15 % | > 15 % |
| Webinar gratuito | Replay → solicitud | < 1 % | 1 a 2 % | 2 a 4 % | > 4 % |
| Webinar gratuito | Solicitud → compra | < 25 % | 25 a 40 % | 40 a 55 % | > 55 % |
| Llamada | Lead → aplicación | < 5 % | 5 a 10 % | 10 a 18 % | > 18 % |
| Llamada | Aplicación → calificado | < 40 % | 40 a 55 % | 55 a 70 % | > 70 % |
| Llamada | Calificado → agenda | < 40 % | 40 a 55 % | 55 a 70 % | > 70 % |
| Llamada | Agenda → llamada (show) | < 55 % | 55 a 65 % | 65 a 75 % | > 75 % |
| Llamada | Llamada → venta (cierre) | < 15 % | 15 a 25 % | 25 a 35 % | > 35 % |
| Webinar pago | ROAS del front (entrada + bump ÷ inversión) | < 0,5 | 0,5 a 0,8 | 0,8 a 1,2 | > 1,2 |
| Webinar pago | Visita → entrada | < 1 % | 1 a 2 % | 2 a 3,5 % | > 3,5 % |
| Webinar pago | Entrada → en vivo | < 35 % | 35 a 50 % | 50 a 65 % | > 65 % |
| Webinar pago | En vivo → solicitud | < 8 % | 8 a 14 % | 14 a 22 % | > 22 % |
| Todos | Reembolsos | > 10 % | 7 a 10 % | 4 a 7 % | < 4 % |

### 2c. Ejemplo de mercado hispano con CPM de 3 a 6 (solo para dimensionar)

CPL de webinar gratuito 0,80 a 1,50 bueno; costo por asistente en vivo 5 a 8 bueno; CPL de llamada 1,50 a 3 bueno con ticket de 500 a 3.000; costo por agenda 60 a 120 bueno; costo por visita a la VSL 0,20 a 0,35 bueno. En un nicho con CPM de 20, multiplicá todo por 4 o 5.

## 3. Testeo y escalado (los números que uso para operar)

- **Presupuesto de testeo por anuncio:** 2 USD por día por conjunto en Latinoamérica (1 costo por resultado por día en mercados caros). Un anuncio por conjunto, campaña ABO, excluyendo a quien ya vio 3 segundos de un video y a quien ya convirtió.
- **Ritmo de revisión:** a las 12 horas, clics (se apagan los que tienen CPC muy por encima del promedio y los que con 1 USD no tuvieron ningún clic: entre 30 y 50 % de los anuncios); a las 24 horas, visitas a la página; a las 48 horas, el evento próximo (registro, lead, inicio de pago); a las 72 horas o más, el evento final. Un ganador se nota desde el día uno: lo que arranca mal no mejora con tiempo.
- **Tolerancia contra la campaña madre:** un anuncio nuevo se mantiene si su CPC, costo por visita y costo por conversión están hasta 20 a 30 % por encima del promedio del último mes de la campaña madre. Por encima de eso, se apaga. La campaña madre es la única referencia válida; los benchmarks de otros son ruido.
- **Tasa de ganadores:** 3 a 4 de cada 50 anuncios (6 a 8 %). El ganador tiene que absorber la pérdida de los otros 46: por eso el testeo se hace con poco presupuesto por anuncio y se corta rápido.
- **Producción:** 20 a 30 piezas para arrancar un embudo nuevo (videos a cámara sin edición e imágenes con texto sirven); 30 a 50 variaciones por semana cuando se escala. Primero validar ángulos con imágenes baratas, después grabar video sobre los ángulos que funcionaron.
- **Presupuesto total de testeo:** 10 a 15 % de la inversión cuando se escala. Es el costo de mantener el CPL debajo del objetivo, no un gasto creativo.
- **Vida útil:** los anuncios pierden 30 a 50 % de CTR cada 4 semanas; el webinar o la VSL dura meses; la oferta, más. Si 2 a 3 semanas de anuncios nuevos no levantan los números, el problema es el embudo.
- **Escalado de la campaña madre:** nunca más de 10 % por día de presupuesto (o escalones de 25 % cada 7 días si se decide por semana). Saturación: frecuencia por encima de 2,5 a 3 en tráfico frío, CTR cayendo y CPM subiendo a la vez. Cada anuncio tiene un punto dulce de inversión; pasado ese punto, se escala con más anuncios en paralelo, no con más presupuesto en el mismo.
- **Umbral operativo:** entre 1.000 y 5.000 USD por día la operación cambia: anuncios nuevos todos los días, caja para la pauta antes de cobrar las cuotas, alguien mirando en tiempo real. Escalar es más riesgo: hay que testear más para encontrar ganadores antes de que el testeo se coma la ganancia.

## 4. Referencias reales (medianas de embudos hispanos que operamos, con CPM de 3 a 6; anonimizadas)

- Webinar gratuito con taller low-ticket, 15 semanas: CPL 1,02 · valor por lead 1,52 · registro → grupo 67 % · registro → en vivo 15 % · ROAS sobre cash neto 1,9. Las tres semanas en que la inversión saltó de 7.500 a 10.000 a 15.000 fueron las de pérdida; el semáforo las hubiera marcado antes.
- Embudo de llamada, 14 webinars: CPL 1,43 · registro → en vivo 12 % · en vivo → agenda 14 % · agenda → venta 44 % · costo por agenda 80 (de 57 a 225) · valor por lead 4,34 · ROAS sobre cash 3,2. Dos webinars seguidos con el mismo CPL dieron ROAS 0,6 y 3,2: en llamada se juzga con 3 o 4 eventos.
- Low-ticket con VSL, dos meses: CPA 16 · AOV neto 41 · ROAS neto 2,5 · techo rentable de inversión cerca de 150 por día con los creativos de ese momento (de 117 a 189 por día, cada dólar extra devolvió 0,20).

## 5. Otros mercados, para no copiarlos

En B2B de Estados Unidos la asistencia en vivo promedia 33 % y se habla de 10 a 15 % de compra sobre asistentes; en info-productos de Estados Unidos los bumps convierten 30 a 40 %. Con tráfico frío en español, 12 a 16 % de asistencia y 2 a 7 % de compra sobre asistentes son un embudo normal. Si copiás el número de allá, vas a creer que tu embudo está roto cuando está normal.

Modelo financiero de embudos · creado por Jesús Tassarolo · TooAudience · youtube.com/@JesusTassaroloSinFiltro
