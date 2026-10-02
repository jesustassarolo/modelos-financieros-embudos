# La inteligencia de los umbrales (lo que esta skill evalúa y en qué orden)

Regla de Jesús Tassarolo: **lo que se evalúa son umbrales, no costos.** El costo por lead depende del mercado, del nicho y del CPM, así que nunca se juzga contra un número absoluto. Lo que sí se puede juzgar, y es donde está la inteligencia, son tres cosas: **el macro** (¿gana plata? ¿el ROAS sobre cash neto está sobre el piso de su tipo de embudo?), **las fugas** (los porcentajes de conversión entre cada paso contra percentiles de la industria y contra el promedio propio) y, recién después, **los costos en relación** (al CPM, al techo propio y al promedio propio). Siempre en ese orden.

## 1. Macro: primero, ¿gana plata y puede escalar?

1. **Ganancia del período** (cash neto − costos por unidad − fijos − inversión). Si es cero o negativa: rojo, sin importar lo demás. Un embudo que pierde no se escala; se arregla la fuga principal.
2. **ROAS sobre cash neto contra el piso de su tipo de embudo.** Se escala hasta que el ROAS baja al piso de escala; a esa altura se frena y se arregla la fuga principal antes de volver a subir.

| Tipo de embudo (`modo`) | Piso de escala (hasta acá se escala) | Objetivo | Nunca por debajo de |
|---|---|---|---|
| Evergreen (low-ticket VSL evergreen, llamada evergreen, webinar automatizado) | 1,5 | 1,7 | 1,3 |
| Lanzamiento o webinar en vivo (webinar gratuito, webinar pago) | 1,7 | 2,0 | 1,3 |
| Excepción: low-ticket evergreen con mucha inversión (30.000 o más por mes) y escalera sólida (2 bumps + OTOs + ascensión) | 1,5 | 1,7 | puede operar más abajo mientras la ganancia siga positiva |

Semáforo del macro: verde si gana y el ROAS está en el piso de escala o más; amarillo si gana pero el ROAS está entre el piso absoluto y el de escala (no se escala: se sostiene y se mejora); rojo si pierde o el ROAS está debajo del piso absoluto.

El ROAS que decide es sobre **cash neto** (cobrado, menos comisiones y reembolsos), nunca sobre facturado. En low-ticket, el ROAS del front es el ROAS del embudo: si el front pierde, se pule la oferta del front antes de tocar tráfico. Caso real: un cliente perdía plata en el front de su low-ticket; no se tocó el tráfico, se pulió la oferta del front (promesa, precio, bumps) y el front pasó a ROAS positivo.

## 2. Fugas: los porcentajes entre pasos contra percentiles

Cada paso tiene una conversión. Debajo de **p25** es una **fuga**; entre p25 y la **mediana**, mejorable; mediana o más, ok; **p75** o más, fortaleza. La **fuga principal** es la que está más lejos de la mediana (y, a igual brecha, la que está más arriba en el embudo, porque multiplica todo lo que viene después). Cerrar una fuga es ganar más sin pagar más: por eso se mira antes que los costos.

Los percentiles de esta tabla son puntos de partida para tráfico frío en español (nuestra experiencia operando embudos hispanos, con la referencia externa que existe en la sección 4). En cuanto el usuario tiene 4 semanas, su propio promedio se suma como segunda vara: una conversión puede estar en la mediana de la industria y 30 % por debajo de su propio promedio, y eso también es una fuga.

### Low-ticket con VSL (evergreen)

| Paso | p25 (fuga por debajo) | Mediana | p75 (fortaleza) | Qué tocar si es fuga |
|---|---|---|---|---|
| Visita → checkout | 2 % | 3 % | 5 % | La VSL y la oferta del front: gancho, promesa, congruencia con el anuncio, el botón |
| Checkout → compra | 15 % | 22 % | 30 % | El checkout: fricción, formas de pago, cuotas, garantía, velocidad |
| Visita → compra | 0,5 % | 0,9 % | 1,5 % | El front completo (VSL + checkout): la fuga que más plata cuesta en un low-ticket |
| Bump 1 tomado | 15 % | 25 % | 35 % | Complemento obvio del principal, precio bajo, una casilla, copy de dos líneas |
| Bump 2 tomado | 10 % | 18 % | 25 % | Que no compita con el bump 1 |
| OTO 1 tomada | 5 % | 9 % | 14 % | La consecuencia lógica de lo que acaba de comprar; precio y video corto |
| OTO 2 (downsell) tomada | 3 % | 6 % | 9 % | Versión más barata o en cuotas de la OTO 1 |
| Ascensión al programa | 1 % | 2 % | 4 % | El camino al programa: llamada, aplicación o secuencia posterior |
| AOV ÷ precio del principal | 1,2 | 1,4 | 1,7 | La escalera entera: sin bumps y OTOs que sumen, el low-ticket no se paga |

### Webinar gratuito (lanzamiento)

| Paso | p25 | Mediana | p75 | Qué tocar si es fuga |
|---|---|---|---|---|
| Visita → registro | 15 % | 22 % | 30 % | Promesa igual a la del anuncio, formulario corto, velocidad, un solo llamado a la acción |
| Registro → grupo de WhatsApp | 50 % | 65 % | 80 % | Botón directo al grupo, incentivo por entrar, bienvenida con fecha y hora |
| Registro → en vivo | 10 % | 15 % | 22 % | Recordatorios 24 h / 2 h / 30 min, ventana corta, calentar el grupo, la expectativa del anuncio |
| Registro → replay | 40 % | 60 % | 80 % | Replay el mismo día por WhatsApp y mail, ventana de 72 h |
| En vivo → solicitud | 5 % | 10 % | 15 % | Congruencia contenido-oferta, claridad, pitch, momento del formulario (sin tocar precio) |
| Replay → solicitud | 1 % | 2 % | 4 % | El seguimiento del replay: recordatorios de cierre, escasez real |
| Solicitud → compra | 25 % | 40 % | 55 % | Seguimiento en minutos, closer, cuotas, nutrición previa |
| Bump tomado | 15 % | 25 % | 35 % | El bump del checkout |
| Pasan al programa superior | 3 % | 5 % | 8 % | El camino al programa |

### Embudo de llamada (high ticket)

| Paso | p25 | Mediana | p75 | Qué tocar si es fuga |
|---|---|---|---|---|
| Visita → lead | 15 % | 22 % | 30 % | La página: promesa igual a la del anuncio, formulario corto |
| Lead → aplicación | 5 % | 10 % | 18 % | El video o la página de aplicación: por qué aplicar y qué gana; primeras preguntas fáciles |
| Aplicación → calificado | 40 % | 55 % | 70 % | La pregunta que califica y el público del anuncio |
| Calificado → agenda | 40 % | 55 % | 70 % | Velocidad de respuesta, huecos en el calendario, confirmación por WhatsApp |
| Agenda → llamada (show) | 55 % | 65 % | 75 % | Nutrición antes de la llamada, recordatorios, confirmación: 700 agendas y 100 llamadas no es el closer, es nutrición |
| Llamada → venta (cierre) | 15 % | 25 % | 35 % | Guion, objeciones, cuotas, calidad del lead; se juzga con 3 o 4 eventos |

### Webinar pago (evento con entrada)

| Paso | p25 | Mediana | p75 | Qué tocar si es fuga |
|---|---|---|---|---|
| Visita → entrada | 1 % | 2 % | 3,5 % | La página de ventas de la entrada: promesa, precio escalonado, prueba |
| ROAS del front (entrada + bump ÷ pauta) | 0,5 | 0,8 | 1,2 | La página de la entrada y el bump: cerca de 1, el evento se paga solo |
| Bump de la entrada tomado | 15 % | 20 % | 30 % | El bump de la entrada |
| Entrada → grupo | 60 % | 80 % | 90 % | Botón directo al grupo después de pagar |
| Entrada → en vivo | 35 % | 50 % | 65 % | Recordatorios, grupo, horario: ya pagaron, tienen que venir |
| En vivo → solicitud | 8 % | 14 % | 22 % | Congruencia contenido-oferta, claridad, pitch |
| Solicitud → compra | 25 % | 40 % | 55 % | Seguimiento en minutos, closer, cuotas |
| Pasan al programa superior | 5 % | 10 % | 15 % | El camino al programa |

## 3. Costos: solo en relación

El CPL, el costo por visita, por asistente o por agenda no se juzgan contra un número absoluto. Se leen de tres formas: contra el **techo y el objetivo** que salen de los propios números del usuario (lo que vale la unidad en su cash neto), contra su **promedio propio** (mediana de sus últimas 4 semanas, 20 a 30 % de tolerancia) y contra su **CPM** (unidades por cada 1.000 impresiones: con CPM de 3 un CPL de 1 y con CPM de 25 un CPL de 10 son el mismo embudo). Si el costo está en verde y el macro en rojo, el problema nunca es el tráfico: es una fuga de la cadena o la oferta.

## 4. Referencias externas (confianza marcada; ninguna es hispana ni de tráfico frío)

- Asistencia en vivo a webinars B2B: mediana 41,6 % (p25 28,4 %, p75 55,2 %) sobre unos 12.400 webinars de ON24, GoTo y BrightTALK, 2025 a 2026 (Nunify; ON24 reporta 60 % en su plataforma). Confianza media. No aplica a tráfico frío hispano, donde 12 a 16 % es normal.
- Conversión mediana de landing pages, todas las industrias: 6,6 % (Unbounce, 57 millones de conversiones, 2024). Confianza alta. Una landing de registro con nombre y WhatsApp a tráfico frío convierte 15 a 30 %: no es comparable con una página de venta.
- Abandono de carrito: 70,2 % promedio de 50 estudios (Baymard, 2025), es decir, 30 % de los carritos se completan. Confianza alta. Coincide con nuestro checkout → compra de 15 a 30 %.
- Order bump: 20 a 40 % se considera sano; debajo de 15 %, relevancia o precio flojos (Focus Digital, 2025; CartFlows). Confianza media. Coincide con nuestra tabla.
- Upsells: el 58 % de los ingresos procesados por SamCart viene de upsells (SamCart, 2025). Confianza alta como señal de que la escalera es el negocio, no como tasa.
- Cierre en llamada high ticket: 20 a 45 % según el nivel del closer (academia de closers hispana, 2026); 10 a 25 % en blogs de tracking (Cometly). Confianza baja. Nuestra tabla: 15 / 25 / 35 %.
- Pisos de ROAS: la literatura pública da el ROAS de equilibrio como 1 ÷ margen bruto (2 a 2,5 para márgenes de 40 a 50 %) y cita "escalar a partir de 3" (Hormozi). Los pisos de esta skill (1,5 evergreen, 1,7 a 2,0 lanzamiento, nunca bajo 1,3) son sobre **cash neto** y vienen de la operación de Jesús Tassarolo, no de un benchmark público.

Modelo financiero de embudos · creado por Jesús Tassarolo · TooAudience · youtube.com/@JesusTassaroloSinFiltro
