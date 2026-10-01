#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Calculadora de modelos financieros de embudos · creada por Jesús Tassarolo (TooAudience).
Cuatro embudos: low_ticket, webinar_gratuito, llamada, webinar_pago. Misma matemática que los Excel.

Uso:
  python3 calculadora.py --embudo webinar_gratuito                      # con los supuestos del ejemplo
  python3 calculadora.py --embudo llamada --set cpm=12 cierre=0.3 ticket=2000
  python3 calculadora.py --embudo low_ticket --json mis_datos.json --html grafico.html
  python3 calculadora.py --embudo webinar_pago --supuestos               # lista los supuestos que acepta
Salida: el bloque de respuesta (valor por unidad, techo, objetivo, techos por etapa, semáforo, inversión para la meta,
palanca que más mueve) y, con --html, un gráfico (embudo, costo vs techo por paso, sensibilidad) con marca de agua.
"""
import argparse, json, sys
MARCA = "Modelo financiero de embudos · creado por Jesús Tassarolo · TooAudience · youtube.com/@JesusTassaroloSinFiltro"

# ------------------------------------------------------------ supuestos por embudo (los del ejemplo de cada Excel)
SUPUESTOS = {
 "low_ticket": dict(inversion=9000, costo_visita=0.30, conv_checkout=0.035, conv_venta=0.26, precio_front=37,
    bump1_precio=17, bump1_conv=0.25, bump2_precio=17, bump2_conv=0.18, oto1_precio=47, oto1_conv=0.10, oto2_precio=17, oto2_conv=0.06,
    oto3_precio=97, oto3_conv=0.03, oto4_precio=27, oto4_conv=0.04, ascension_precio=297, ascension_conv=0.02,
    pasarela=0.10, closers=0.0, reembolsos=0.05, costo_semivar=0.0, fijos=1500, cobro_m1=1.0, roas_obj=2.0, margen_seg=0.30, meta_ventas=500),
 "webinar_gratuito": dict(inversion=6000, cpm=4.5, ctr=0.022, clic_visita=0.90, conv_landing=0.23, calif_pct=0.60, grupo_pct=0.67,
    show_vivo=0.15, show_replay=0.55, solic_vivo_pct=0.10, solic_replay_pct=0.025, cierre_pct=0.40, precio_oferta=297,
    bump_precio=47, bump_conv=0.20, backend_precio=997, backend_conv=0.05, pasarela=0.10, closers=0.0, reembolsos=0.05,
    costo_semivar=0.10, fijos=1200, cobro_m1=0.70, roas_obj=2.0, margen_seg=0.30, meta_ventas=60),
 "llamada": dict(inversion=4500, cpm=10.0, ctr=0.015, clic_visita=0.85, conv_landing=0.28, hay_evento=0, show_evento=0.14,
    aplic_pct=0.10, calif_pct=0.60, agenda_pct=0.60, show_llamada=0.70, cierre=0.25, ticket=1500, ds_precio=497, ds_conv=0.10,
    pasarela=0.05, closers=0.10, reembolsos=0.05, costo_semivar=0.20, fijos=2500, cobro_m1=0.60, roas_obj=2.5, margen_seg=0.30, meta_ventas=15),
 "webinar_pago": dict(inversion=3000, costo_visita=0.35, conv_entrada=0.025, precio_entrada=9, bump_e_precio=27, bump_e_conv=0.20,
    grupo_pct=0.85, show_vivo=0.55, show_replay=0.25, solic_vivo_pct=0.16, solic_replay_pct=0.04, cierre_pct=0.50, precio_oferta=497,
    backend_precio=1997, backend_conv=0.10, pasarela=0.08, closers=0.0, reembolsos=0.05, costo_semivar=0.30, fijos=800, cobro_m1=0.50,
    roas_obj=2.0, margen_seg=0.30, meta_ventas=25),
}
UNIDAD = {"low_ticket": "visita", "webinar_gratuito": "registro", "llamada": "lead", "webinar_pago": "entrada"}
PALANCAS = {
 "low_ticket": [("costo_visita", 0.9, "costo por visita 10 % más barato"), ("conv_checkout", 1.1, "10 % más visitas al checkout"), ("conv_venta", 1.1, "10 % más checkouts que compran"), ("precio_front", 1.1, "precio del principal 10 % más alto"), ("bump1_conv", 1.1, "bump 1 10 % más tomado"), ("oto1_conv", 1.1, "OTO 1 10 % más tomada"), ("ascension_conv", 1.1, "ascensión 10 % más alta")],
 "webinar_gratuito": [("cpm", 0.9, "CPM 10 % más barato"), ("ctr", 1.1, "CTR 10 % más alto"), ("conv_landing", 1.1, "landing 10 % más conversión"), ("show_vivo", 1.1, "show en vivo 10 % más alto"), ("solic_vivo_pct", 1.1, "10 % más asistentes que solicitan"), ("cierre_pct", 1.1, "10 % más solicitudes que compran"), ("precio_oferta", 1.1, "precio 10 % más alto"), ("backend_conv", 1.1, "programa superior 10 % más tomado")],
 "llamada": [("cpm", 0.9, "CPM 10 % más barato"), ("conv_landing", 1.1, "página 10 % más conversión"), ("aplic_pct", 1.1, "10 % más aplicaciones"), ("agenda_pct", 1.1, "10 % más agendas"), ("show_llamada", 1.1, "show de llamada 10 % más alto"), ("cierre", 1.1, "cierre 10 % más alto"), ("ticket", 1.1, "precio 10 % más alto")],
 "webinar_pago": [("costo_visita", 0.9, "costo por visita 10 % más barato"), ("conv_entrada", 1.1, "página de la entrada 10 % más conversión"), ("precio_entrada", 1.1, "precio de la entrada 10 % más alto"), ("show_vivo", 1.1, "asistencia 10 % más alta"), ("solic_vivo_pct", 1.1, "10 % más asistentes que solicitan"), ("cierre_pct", 1.1, "10 % más solicitudes que compran"), ("precio_oferta", 1.1, "precio de la oferta 10 % más alto")],
}

def d(a, b): return a / b if b else 0.0

# ------------------------------------------------------------ la cadena de cada embudo
def cadena(e, s):
    """Devuelve pasos [(nombre, cantidad, con_costo)], facturado, ventas del principal y costo por unidad."""
    I = s["inversion"]; pasos = []; fact = 0.0
    if e == "low_ticket":
        cpu = s["costo_visita"]; u = d(I, cpu); ck = u * s["conv_checkout"]; v = ck * s["conv_venta"]
        pasos += [("Visitas a la página", u, True), ("Abren el checkout", ck, True), ("Compran el principal", v, True)]
        fact = v * s["precio_front"]
        for k, n in [("bump1", "Bump 1"), ("bump2", "Bump 2"), ("oto1", "OTO 1"), ("oto2", "OTO 2"), ("oto3", "OTO 3"), ("oto4", "OTO 4"), ("ascension", "Ascensión")]:
            q = v * s[k + "_conv"]; fact += q * s[k + "_precio"]; pasos.append((f"Toman {n}", q, False))
        return pasos, fact, v, cpu, u
    if e in ("webinar_gratuito", "llamada"):
        cpu = d(s["cpm"] / 1000, s["ctr"] * s["clic_visita"] * s["conv_landing"]); u = d(I, cpu)
        imp = d(I, s["cpm"]) * 1000; cl = imp * s["ctr"]; vis = cl * s["clic_visita"]
        pasos += [("Impresiones", imp, False), ("Clics", cl, True), ("Visitas", vis, True)]
    if e == "webinar_gratuito":
        pasos.append(("Registros", u, True)); pasos.append(("Registros calificados", u * s["calif_pct"], True))
        pasos.append(("Entran al grupo", u * s["grupo_pct"], True)); av = u * s["show_vivo"]; ar = u * s["show_replay"]
        pasos += [("Asisten en vivo", av, True), ("Ven el replay", ar, True)]
        sol = av * s["solic_vivo_pct"] + ar * s["solic_replay_pct"]; v = sol * s["cierre_pct"]
        pasos += [("Solicitudes", sol, True), ("Compran la oferta", v, True)]
        fact = v * (s["precio_oferta"] + s["bump_conv"] * s["bump_precio"] + s["backend_conv"] * s["backend_precio"])
        pasos += [("Toman el bump", v * s["bump_conv"], False), ("Programa superior", v * s["backend_conv"], False)]
        return pasos, fact, v, cpu, u
    if e == "llamada":
        pasos.append(("Leads", u, True)); base = u * s["show_evento"] if s["hay_evento"] else u
        if s["hay_evento"]: pasos.append(("Asisten al evento", base, True))
        ap = base * s["aplic_pct"]; ca = ap * s["calif_pct"]; ag = ca * s["agenda_pct"]; ll = ag * s["show_llamada"]; v = ll * s["cierre"]
        pasos += [("Aplicaciones", ap, True), ("Calificados", ca, True), ("Agendas", ag, True), ("Llamadas (show)", ll, True), ("Compran el programa", v, True)]
        ds = (ll - v) * s["ds_conv"]; fact = v * s["ticket"] + ds * s["ds_precio"]; pasos.append(("Toman el downsell", ds, False))
        return pasos, fact, v, cpu, u
    if e == "webinar_pago":
        vis = d(I, s["costo_visita"]); cpu = d(s["costo_visita"], s["conv_entrada"]); u = d(I, cpu)
        pasos += [("Visitas a la página", vis, True), ("Compran la entrada", u, True)]
        fact = u * s["precio_entrada"] + u * s["bump_e_conv"] * s["bump_e_precio"]
        pasos.append(("Entran al grupo", u * s["grupo_pct"], True)); av = u * s["show_vivo"]; ar = u * s["show_replay"]
        pasos += [("Asisten en vivo", av, True), ("Ven el replay", ar, True)]
        sol = av * s["solic_vivo_pct"] + ar * s["solic_replay_pct"]; v = sol * s["cierre_pct"]
        pasos += [("Solicitudes", sol, True), ("Compran la oferta", v, True)]
        fact += v * (s["precio_oferta"] + s["backend_conv"] * s["backend_precio"]); pasos.append(("Programa superior", v * s["backend_conv"], False))
        return pasos, fact, v, cpu, u
    raise SystemExit(f"embudo desconocido: {e}")

def modelo(e, s):
    pasos, fact, v, cpu, u = cadena(e, s)
    I = s["inversion"]; neto = fact * (1 - s["pasarela"] - s["closers"] - s["reembolsos"]); semi = u * s["costo_semivar"]
    profit = neto - semi - s["fijos"] - I
    vpu = d(neto - semi, u); techo = vpu; obj = techo / (1 + s["margen_seg"]); roas = d(neto, I)
    sem = "ROJO" if cpu > techo else ("VERDE" if cpu <= obj and roas >= s["roas_obj"] else "AMARILLO")
    conv = d(v, u)
    etapas = [(n, q, d(I, q), d(vpu * u, q), d(profit, q)) for n, q, c in pasos if c and q > 0]
    return dict(unidad=UNIDAD[e], unidades=u, cpu=cpu, ventas=v, facturado=fact, neto=neto, profit=profit, vpu=vpu, techo=techo,
                objetivo=obj, roas=roas, roas_m1=d(fact * s["cobro_m1"] * (1 - s["pasarela"] - s["closers"] - s["reembolsos"]), I),
                semaforo=sem, conv=conv, cpa=d(I, v), aov=d(fact, v), aov_neto=d(neto - semi, v),
                inv_meta=(s["meta_ventas"] / conv * cpu) if conv else None, inv_meta_obj=(s["meta_ventas"] / conv * obj) if conv else None,
                gan_unidad=d(profit, u), etapas=etapas)

def sensibilidad(e, s):
    base = modelo(e, s)["profit"]; out = []
    for k, mult, lab in PALANCAS[e]:
        s2 = dict(s); s2[k] = s[k] * mult; out.append((lab, modelo(e, s2)["profit"] - base))
    return sorted(out, key=lambda x: -x[1])

def money(x): return ("$" + f"{x:,.2f}").replace(",", "X").replace(".", ",").replace("X", ".")
def entero(x): return f"{x:,.0f}".replace(",", ".")

def reporte(e, s):
    m = modelo(e, s); sens = sensibilidad(e, s); un = m["unidad"]
    L = [f"EMBUDO: {e}   (supuestos en uso: los que cargaste; lo demás, el ejemplo)",
         f"Tu {un} vale (cash neto):            {money(m['vpu'])}",
         f"Hasta cuánto podés pagar (techo):    {money(m['techo'])}   <- acá no ganás ni perdés",
         f"Cuánto te conviene pagar (objetivo): {money(m['objetivo'])}   <- con {s['margen_seg']:.0%} de colchón",
         "Por cada paso: lo que pagás hoy, lo que te queda y lo máximo que podrías pagar (techo = costo + ganancia + fijos repartidos):"]
    for n, q, c, t, g in m["etapas"]:
        L.append(f"   {n:<24} cantidad {entero(q):>9}   pagás hoy {money(c):>10}   te queda {money(g):>10}   techo {money(t):>10}")
    L += [f"Con tu costo actual de {money(m['cpu'])} por {un}: SEMÁFORO {m['semaforo']}  (ROAS sobre cash neto {m['roas']:.2f}x; objetivo {s['roas_obj']:.1f}x; el primer mes entra {m['roas_m1']:.2f}x)",
          f"Ganancia del período: {money(m['profit'])}   |   ganancia por {un}: {money(m['gan_unidad'])}   |   CPA {money(m['cpa'])}   |   AOV {money(m['aov'])} (neto {money(m['aov_neto'])})"]
    if m["inv_meta"] is None:
        L.append(f"Para {s['meta_ventas']} ventas por período: inalcanzable con estos supuestos (la conversión a venta es 0)")
    else:
        L.append(f"Para {s['meta_ventas']} ventas por período necesitás invertir ≈ {money(m['inv_meta'])} (al costo actual) o {money(m['inv_meta_obj'])} (al objetivo)")
    L.append("La palanca que más mueve (+10 % en cada una): " + "; ".join(f"{lab}: {money(dp)}" for lab, dp in sens[:3]))
    L.append(MARCA)
    return "\n".join(L), m, sens

def html(e, s, m, sens, path):
    W = 900; pasos = m["etapas"]; mx = max(q for _, q, *_ in pasos) or 1
    rows = ""; y = 40
    for n, q, c, t, g in pasos:
        w = max(4, 520 * q / mx); col = "#DC2626" if c > t else ("#00996A" if c <= t / (1 + s["margen_seg"]) else "#F59E0B")
        rows += f'<text x="10" y="{y+15}" font-size="12">{n}</text><rect x="200" y="{y}" width="{w}" height="22" fill="#E8F8F1" stroke="#00996A"/>'
        rows += f'<text x="{205+w}" y="{y+15}" font-size="11" fill="#3D3D40">{entero(q)} · costo {money(c)} · techo {money(t)} · gana {money(g)}</text><circle cx="190" cy="{y+11}" r="5" fill="{col}"/>'
        y += 30
    sy = y + 30; mxs = max(abs(dp) for _, dp in sens) or 1; srows = ""
    for lab, dp in sens:
        w = 400 * abs(dp) / mxs; srows += f'<text x="10" y="{sy+13}" font-size="11">{lab}</text><rect x="330" y="{sy}" width="{w}" height="16" fill="{"#00996A" if dp>=0 else "#DC2626"}"/><text x="{335+w}" y="{sy+13}" font-size="11">{money(dp)}</text>'; sy += 24
    H = sy + 60
    doc = f'''<!doctype html><html lang="es"><meta charset="utf-8"><title>Modelo financiero · {e}</title>
<body style="font-family:Inter,Helvetica,Arial,sans-serif;margin:24px;color:#0A0A0B">
<h1 style="font-size:22px;margin:0 0 4px">Modelo financiero · {e.replace("_"," ")}</h1>
<p style="color:#3D3D40;margin:0 0 14px">Tu {m["unidad"]} vale <b>{money(m["vpu"])}</b> · techo <b>{money(m["techo"])}</b> · objetivo <b>{money(m["objetivo"])}</b> · costo hoy <b>{money(m["cpu"])}</b> · semáforo <b style="color:{"#00996A" if m["semaforo"]=="VERDE" else ("#B45309" if m["semaforo"]=="AMARILLO" else "#DC2626")}">{m["semaforo"]}</b> · ROAS cash neto <b>{m["roas"]:.2f}x</b> · ganancia <b>{money(m["profit"])}</b></p>
<svg viewBox="0 0 {W} {H}" width="100%" style="max-width:{W}px;display:block">
<text x="10" y="22" font-size="14" font-weight="700">El embudo: cantidad por paso (barra), costo hoy vs techo (punto: verde dentro del objetivo, ámbar entre objetivo y techo, rojo por encima)</text>{rows}
<text x="10" y="{y+18}" font-size="14" font-weight="700">Qué palanca mueve más la ganancia (+10 % en cada una)</text>{srows}
<text x="10" y="{H-14}" font-size="10" fill="#6B6B70">{MARCA}</text></svg></body></html>'''
    open(path, "w", encoding="utf-8").write(doc)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--embudo", required=True, choices=list(SUPUESTOS))
    ap.add_argument("--json", help="archivo JSON con supuestos (solo los que quieras cambiar)")
    ap.add_argument("--set", nargs="*", default=[], help="clave=valor (porcentajes como 0.15)")
    ap.add_argument("--html", help="escribe un gráfico HTML en esta ruta")
    ap.add_argument("--supuestos", action="store_true", help="lista los supuestos y sus valores de ejemplo")
    a = ap.parse_args(); s = dict(SUPUESTOS[a.embudo])
    if a.supuestos:
        for k, v in s.items(): print(f"{k} = {v}")
        return
    if a.json: s.update(json.load(open(a.json, encoding="utf-8")))
    for kv in a.set:
        k, v = kv.split("="); s[k] = float(v)
    texto, m, sens = reporte(a.embudo, s); print(texto)
    if a.html:
        html(a.embudo, s, m, sens, a.html); print(f"gráfico: {a.html}")

if __name__ == "__main__":
    main()
