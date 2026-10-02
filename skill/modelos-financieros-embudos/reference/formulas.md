# Fórmulas (las mismas en los cuatro embudos)

```
unidades               = inversión ÷ costo por unidad
                         (webinar y llamada: costo por unidad = CPM ÷ 1.000 ÷ (CTR × clic→visita × conversión de la página))
                         (webinar pago: costo por entrada = costo por visita ÷ % de visitas que compran la entrada)
cantidad en el paso k  = unidades × producto de las conversiones hasta k
ventas de un producto  = unidades × conversión acumulada hasta ese producto
facturado              = Σ ventas × precio
cash neto              = facturado × cobranza completa × (1 − pasarela − closers − reembolsos)
costos por unidad      = unidades × costo semivariable (WhatsApp, IA, herramientas)
ganancia del período   = cash neto − costos por unidad − fijos − inversión
valor neto por unidad  = (cash neto − costos por unidad) ÷ unidades          ← lo que vale un lead
techo                  = valor neto por unidad                                 ← no ganás ni perdés
objetivo               = techo ÷ (1 + margen de seguridad)                     ← 30 % → techo ÷ 1,3
techo del paso k       = valor neto por unidad ÷ conversión acumulada hasta k
costo del paso k       = inversión ÷ cantidad en k
ganancia por paso k    = ganancia del período ÷ cantidad en k                  ← la ganancia por visita es la más valiosa
ganancia por visita    = ganancia del período ÷ visitas                       ← se juzga contra tu promedio (mediana de 4 semanas); rojo solo si es negativa
inversión para la meta = ventas meta ÷ conversión (unidad → venta) × costo por unidad
ROAS sobre cash neto   = cash neto ÷ inversión   (ROAS del mes 1 = igual, con la cobranza del mes 1)
semáforo               = ROJO si costo > techo · VERDE si costo ≤ objetivo y ROAS ≥ objetivo · AMARILLO el resto
identidad              = ganancia = unidades × (valor neto por unidad − costo por unidad) − fijos
techo por paso         = costo por paso + ganancia por paso + fijos ÷ cantidad en k    ← por eso el techo es mayor que la ganancia
```

Pasos sin costo propio (bumps, OTOs, ascensión, downsell): no se les calcula costo ni techo; se pagan con el CPA del comprador principal y se miden por lo que suman al AOV (order value). AOV neto = (cash neto − costos por unidad) ÷ compradores del principal; su par es el CPA.

Rendimientos decrecientes: a más inversión, menos ROAS. Lo que decide subir es el ROAS marginal (lo que devolvió la última subida): si el cash neto subió menos de 1,3 veces lo que subió la inversión, se vuelve atrás. Pisos de ROAS sobre cash neto por tipo de embudo (umbrales.md § 1): se escala hasta 1,5 (evergreen) o 1,7 con objetivo 2,0 (lanzamiento); nunca debajo de 1,3 salvo low-ticket evergreen con mucha inversión y escalera sólida. Guardarraíl por nivel: ROAS mínimo(S) = (S0 × R0 + 1,3 × (S − S0)) ÷ S, con S0 y R0 la inversión y el ROAS actuales.

Modelo financiero de embudos · creado por Jesús Tassarolo · TooAudience · youtube.com/@JesusTassaroloSinFiltro
