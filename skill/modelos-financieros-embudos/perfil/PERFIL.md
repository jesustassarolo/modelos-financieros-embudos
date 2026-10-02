# Tu perfil: completalo una vez y la skill no te pregunta más

Copiá `mi_embudo.json`, completalo con tus números y guardalo con el mismo nombre en esta carpeta (o pegalo en el chat, o subilo a tu proyecto de Claude). Con el perfil presente, la skill calcula directo: tus umbrales, tu radiografía, tu proyección y una decisión.

## Qué va en cada bloque

- **embudo:** `low_ticket`, `webinar_gratuito`, `llamada` o `webinar_pago`.
- **supuestos:** tus números del período (los nombres exactos están en `../reference/embudos.md`, con el valor de ejemplo de cada embudo). Porcentajes como fracción: 15 % = 0.15. Lo que no completes toma el valor del ejemplo y la skill lo marca como supuesto.
- **historico:** la **mediana de tus últimas 4 semanas** de cada métrica que tengas: `cpu` (tu CPL, costo por visita o por entrada), `gan_visita`, `conv_landing` (o `conv_checkout` / `conv_entrada`), `show_vivo`, `solic_vivo_pct`, `cierre_pct` (o `cierre`), `roas`, `anuncios_nuevos`, `frecuencia`, `reembolsos`, `cpm`. Con esto los umbrales son tuyos; sin esto, la skill usa puntos de partida de mercado y te lo dice.
- **testeo:** `anuncios_nuevos` (publicados en los últimos 7 días), `pct_testeo` (parte del presupuesto en testeo), `dias_ganador` (edad de tu anuncio principal), `frecuencia`.
- **proyeccion:** `meses` (12), `crecimiento` por mes (0.10), `lanz_mes` (cuántos períodos como el de supuestos hacés por mes: 4 si tu período es una semana, 1 si es un mes), `cobranza` (qué parte del facturado entra el mes 1, 2 y 3; tiene que sumar 1) y `caja_inicial`.
- **tolerancia:** cuánto peor que tu promedio se tolera antes del rojo (0.20 a 0.30).

Si llevás el Excel de métricas diarias de este sistema, la hoja `Semanal` tiene las medianas listas para copiar.

Modelo financiero de embudos · creado por Jesús Tassarolo · TooAudience · youtube.com/@JesusTassaroloSinFiltro
