# Supuestos que pide cada embudo (nombre del parámetro en `scripts/calculadora.py` y valor del ejemplo)

## low_ticket (visita → checkout → compra → bumps, OTO 1 a 4, ascensión)
inversion 9000 · costo_visita 0.30 · conv_checkout 0.035 · conv_venta 0.26 · precio_front 37 · bump1_precio 17 / bump1_conv 0.25 · bump2_precio 17 / bump2_conv 0.18 · oto1_precio 47 / oto1_conv 0.10 · oto2_precio 17 / oto2_conv 0.06 · oto3_precio 97 / oto3_conv 0.03 · oto4_precio 27 / oto4_conv 0.04 · ascension_precio 297 / ascension_conv 0.02 · pasarela 0.10 · closers 0 · reembolsos 0.05 · costo_semivar 0 · fijos 1500 · cobro_m1 1.0 · roas_obj 2.0 · margen_seg 0.30 · meta_ventas 500

## webinar_gratuito (impresión → clic → visita → registro → calificado → grupo → en vivo / replay → solicitud → compra → bump, programa)
inversion 6000 (por lanzamiento) · cpm 4.5 · ctr 0.022 · clic_visita 0.90 · conv_landing 0.23 · calif_pct 0.60 (1.0 si el formulario no califica) · grupo_pct 0.67 · show_vivo 0.15 · show_replay 0.55 · solic_vivo_pct 0.10 · solic_replay_pct 0.025 · cierre_pct 0.40 · precio_oferta 297 · bump_precio 47 / bump_conv 0.20 · backend_precio 997 / backend_conv 0.05 · pasarela 0.10 · closers 0 · reembolsos 0.05 · costo_semivar 0.10 (por registro) · fijos 1200 · cobro_m1 0.70 · roas_obj 2.0 · margen_seg 0.30 · meta_ventas 60

## llamada (impresión → clic → visita → lead → [evento] → aplicación → calificado → agenda → llamada → cierre → downsell)
inversion 4500 · cpm 10 · ctr 0.015 · clic_visita 0.85 · conv_landing 0.28 · hay_evento 0 (1 si hay webinar antes de la aplicación) · show_evento 0.14 · aplic_pct 0.10 · calif_pct 0.60 · agenda_pct 0.60 · show_llamada 0.70 · cierre 0.25 · ticket 1500 · ds_precio 497 / ds_conv 0.10 · pasarela 0.05 · closers 0.10 · reembolsos 0.05 · costo_semivar 0.20 (por lead) · fijos 2500 · cobro_m1 0.60 · roas_obj 2.5 · margen_seg 0.30 · meta_ventas 15

## webinar_pago (visita → entrada + bump → grupo → en vivo / replay → solicitud → compra → programa)
inversion 3000 (por lanzamiento) · costo_visita 0.35 · conv_entrada 0.025 · precio_entrada 9 (promedio cobrado si es escalonado) · bump_e_precio 27 / bump_e_conv 0.20 · grupo_pct 0.85 · show_vivo 0.55 · show_replay 0.25 · solic_vivo_pct 0.16 · solic_replay_pct 0.04 · cierre_pct 0.50 · precio_oferta 497 · backend_precio 1997 / backend_conv 0.10 · pasarela 0.08 · closers 0 · reembolsos 0.05 · costo_semivar 0.30 (por entrada) · fijos 800 · cobro_m1 0.50 · roas_obj 2.0 · margen_seg 0.30 · meta_ventas 25

Las conversiones van como fracción (15 % = 0.15). La "solicitud" es lo que hace el asistente cuando se presenta la oferta: completa el formulario de compra, la aplicación, o pide hablar con un vendedor. Los porcentajes de bumps, OTOs, programa y downsell van sobre los compradores del paso anterior.

Modelo financiero de embudos · creado por Jesús Tassarolo · TooAudience
