# Modelos financieros de embudos

Cuatro modelos financieros en Excel, una skill para Claude y un documento de mejores prácticas para entender el embudo como una cadena de números: cuánto vale cada lead, hasta cuánto pagarlo con un ROAS sano, cuánto invertir, cuándo subir, cuándo bajar y qué palanca mover.

Creado por **Jesús Tassarolo** (TooAudience) · youtube.com/@JesusTassaroloSinFiltro

## Qué hay acá

| Carpeta | Qué es |
|---|---|
| `excel/` | Los cuatro modelos, uno por embudo, con un negocio de ejemplo cargado: **01** low-ticket con VSL (producto principal, bumps 1 y 2, OTO 1 a 4, ascensión) · **02** webinar gratuito · **03** embudo de llamada (high ticket) · **04** webinar pago. Funcionan en Excel, Google Sheets y Numbers, sin macros. |
| `skill/` | La skill `modelos-financieros-embudos` para Claude: te pregunta tus datos y te dice cuánto vale tu lead, hasta cuánto podés pagar, cuánto te conviene pagar, cuánto invertir y qué palanca mover, con un gráfico. Carpeta lista y `.zip` para subir. |
| `paper/` | *Modelos financieros de embudos: cuánto invertir, cuánto pagar y cuándo frenar*. Los conceptos detrás de cada consejo, con figuras y las tablas de ejemplo de los cuatro embudos. PDF y fuente en markdown. |
| `generador/` | El código que genera y verifica los Excel (Python, `openpyxl`). Para quien quiera ver cómo están hechas las fórmulas o regenerarlos. |

## Cómo usar los Excel

1. Abrí el del embudo que usás. La hoja **Inicio** es el instructivo.
2. En **Supuestos** reemplazá el ejemplo por tus números (amarillo = se edita, azul = se calcula). Si no tenés datos, escenario 1 (conservador) y la hoja **Benchmarks**.
3. **Resumen**: ganancia, ROAS sobre cash neto, techo y objetivo de tu unidad, semáforo, y las dos caras de cada número (costo y ganancia por visita, por lead, por cliente; order value bruto y neto).
4. **Embudo**: todos los pasos en orden con cantidad, % que pasa, % acumulado, lo que pagás hoy por cada uno (costo), lo que te queda por cada uno (ganancia) y lo máximo que podrías pagar (techo), con la fila de comprobación costo + ganancia + fijos repartidos = techo.
5. **Escenarios**, **Sensibilidad**, **Proyección 12 meses** y **Seguimiento** (una columna por semana con tus datos reales y semáforo).

## Cómo usar la skill

- **En claude.ai**: Configuración → Capacidades → Skills → subir `skill/modelos-financieros-embudos-skill.zip`. Después preguntale a Claude, por ejemplo: "¿hasta cuánto puedo pagar por lead en mi webinar?" y seguí sus preguntas.
- **En Claude Code**: copiá la carpeta `skill/modelos-financieros-embudos` a `~/.claude/skills/`.
- **Sin Claude**, la calculadora sola: `python3 skill/modelos-financieros-embudos/scripts/calculadora.py --embudo webinar_gratuito --set cpm=4.5 ctr=0.022 conv_landing=0.23 --html grafico.html` (no necesita librerías; `--supuestos` lista los parámetros).

## Los cuatro embudos

| Embudo | Unidad que compra la pauta | Cadena | Número que manda |
|---|---|---|---|
| Low-ticket con VSL | visita | visita → checkout → compra → bumps, OTO 1 a 4, ascensión | AOV neto contra CPA |
| Webinar gratuito | registro | impresión → clic → visita → registro (y calificado) → grupo → en vivo / replay → solicitud → compra → bump, programa | valor por registro contra CPL |
| Embudo de llamada | lead | lead → aplicación → calificado → agenda → llamada → cierre → downsell | costo por agenda contra su valor; cierre; cash en cuotas |
| Webinar pago | entrada | visita → entrada + bump → grupo → en vivo / replay → solicitud → compra → programa | ROAS del front, después la oferta |

## Regenerar los Excel

```bash
python3 -m pip install --user openpyxl formulas
python3 generador/build.py        # genera los cuatro libros en excel/
python3 generador/verificar.py    # recalcula todas las fórmulas sin Excel y compara con cuentas a mano; termina en "RESULTADO GENERAL: OK"
```

## Licencia y atribución

Este material se publica bajo **Creative Commons BY-NC-ND 4.0**: podés descargarlo, usarlo con tus números y compartirlo tal cual, citando al autor; no podés venderlo, modificarlo ni redistribuir versiones modificadas. Cada Excel, la skill y el documento llevan la línea de autoría *Modelo financiero de embudos · creado por Jesús Tassarolo · TooAudience*. Dejala donde está: es la forma de saber de dónde salió.

No contiene datos de clientes ni información sensible: los ejemplos son negocios ficticios calibrados con rangos de mercado.

Versión 1.3 · octubre 2026.
