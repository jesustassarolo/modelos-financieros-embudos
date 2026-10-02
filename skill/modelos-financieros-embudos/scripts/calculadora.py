#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Calculadora de modelos financieros de embudos · creada por Jesús Tassarolo (TooAudience).
Cuatro embudos: low_ticket, webinar_gratuito, llamada, webinar_pago. Misma matemática que los Excel.

Uso:
  python3 calculadora.py --embudo webinar_gratuito                      # con los supuestos del ejemplo
  python3 calculadora.py --embudo llamada --set cpm=12 cierre=0.3 ticket=2000
  python3 calculadora.py --embudo low_ticket --json mis_datos.json --html grafico.html
  python3 calculadora.py --embudo webinar_pago --supuestos               # lista los supuestos que acepta
  python3 calculadora.py --embudo webinar_gratuito --testeo anuncios_nuevos=12 pct_testeo=0.10 dias_ganador=20 frecuencia=2.1
  python3 calculadora.py --embudo webinar_gratuito --set cpm=5.2 --historico cpu=0.95 gan_visita=0.48 show_vivo=0.16 roas=3.1   # umbrales = tus promedios
  python3 calculadora.py --embudo llamada --periodos ultimas_semanas.json      # mediana de tus períodos como histórico
  python3 calculadora.py --perfil perfil/mi_embudo.json                            # plug and play: todo sale del perfil de la persona
Salida: el bloque de respuesta (valor por unidad, techo, objetivo, costo / ganancia / techo por paso, la radiografía de lo que
más importa con semáforo y UNA decisión, inversión para la meta, palanca que más mueve) y, con --html, un gráfico con marca de agua.
"""
import argparse, json, sys
AUTOR = "Jesús Tassarolo"
INSTAGRAM = ""   # usuario de Instagram del autor (p. ej. "@usuario"); si está, viaja en la marca de agua
MARCA = ("Modelo financiero de embudos · creado por " + AUTOR + " · TooAudience" + (" · Instagram " + INSTAGRAM if INSTAGRAM else "")
         + " · youtube.com/@JesusTassaroloSinFiltro")

# ------------------------------------------------------------ supuestos por embudo (los del ejemplo de cada Excel)
SUPUESTOS = {
 "low_ticket": dict(inversion=9000, costo_visita=0.30, conv_checkout=0.035, conv_venta=0.26, precio_front=37,
    bump1_precio=17, bump1_conv=0.25, bump2_precio=17, bump2_conv=0.18, oto1_precio=47, oto1_conv=0.10, oto2_precio=17, oto2_conv=0.06,
    oto3_precio=97, oto3_conv=0.03, oto4_precio=27, oto4_conv=0.04, ascension_precio=297, ascension_conv=0.02,
    pasarela=0.10, closers=0.0, reembolsos=0.05, costo_semivar=0.0, fijos=1500, cobro_m1=1.0, roas_obj=2.0, margen_seg=0.30, meta_ventas=500, modo="evergreen", escalera_solida=1),
 "webinar_gratuito": dict(inversion=6000, cpm=4.5, ctr=0.022, clic_visita=0.90, conv_landing=0.23, calif_pct=0.60, grupo_pct=0.67,
    show_vivo=0.15, show_replay=0.55, solic_vivo_pct=0.10, solic_replay_pct=0.025, cierre_pct=0.40, precio_oferta=297,
    bump_precio=47, bump_conv=0.20, backend_precio=997, backend_conv=0.05, pasarela=0.10, closers=0.0, reembolsos=0.05,
    costo_semivar=0.10, fijos=1200, cobro_m1=0.70, roas_obj=2.0, margen_seg=0.30, meta_ventas=60, modo="lanzamiento", escalera_solida=0),
 "llamada": dict(inversion=4500, cpm=10.0, ctr=0.015, clic_visita=0.85, conv_landing=0.28, hay_evento=0, show_evento=0.14,
    aplic_pct=0.10, calif_pct=0.60, agenda_pct=0.60, show_llamada=0.70, cierre=0.25, ticket=1500, ds_precio=497, ds_conv=0.10,
    pasarela=0.05, closers=0.10, reembolsos=0.05, costo_semivar=0.20, fijos=2500, cobro_m1=0.60, roas_obj=2.5, margen_seg=0.30, meta_ventas=15, modo="evergreen", escalera_solida=0),
 "webinar_pago": dict(inversion=3000, costo_visita=0.35, conv_entrada=0.025, precio_entrada=9, bump_e_precio=27, bump_e_conv=0.20,
    grupo_pct=0.85, show_vivo=0.55, show_replay=0.25, solic_vivo_pct=0.16, solic_replay_pct=0.04, cierre_pct=0.50, precio_oferta=497,
    backend_precio=1997, backend_conv=0.10, pasarela=0.08, closers=0.0, reembolsos=0.05, costo_semivar=0.30, fijos=800, cobro_m1=0.50,
    roas_obj=2.0, margen_seg=0.30, meta_ventas=25, modo="lanzamiento", escalera_solida=0),
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
    pz = pisos(e, s)
    sem = "ROJO" if (cpu > techo or profit <= 0 or roas < pz["absoluto"]) else ("VERDE" if (cpu <= obj and roas > pz["escala"]) else "AMARILLO")
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

# ------------------------------------------------------------ lo que más importa (radiografía): umbrales 'mayor es mejor'
# (rojo si < t1, amarillo si < t2, verde si >= t2); los mismos de reference/benchmarks.md
# ------------------------------------------------------------ LA INTELIGENCIA DE LOS UMBRALES
# Lo que se evalúa son porcentajes y ROAS, no costos: el costo por lead depende del mercado y del nicho (se lee contra el
# CPM y contra el promedio propio); los porcentajes de conversión entre pasos se comparan con percentiles de la industria
# y con el promedio propio para detectar fugas; y antes que nada el macro: si gana plata y si el ROAS está sobre el piso.
LANZ_MES = {"low_ticket": 1, "webinar_gratuito": 4, "llamada": 1, "webinar_pago": 2}
PISOS = {"evergreen": {"escala": 1.5, "objetivo": 1.7, "absoluto": 1.3}, "lanzamiento": {"escala": 1.7, "objetivo": 2.0, "absoluto": 1.3}}
MODO_DEFAULT = {"low_ticket": "evergreen", "webinar_gratuito": "lanzamiento", "llamada": "evergreen", "webinar_pago": "lanzamiento"}
MODO_SINONIMOS = [("evergreen", "evergreen"), ("perpetuo", "evergreen"), ("automatizado", "evergreen"), ("vsl", "evergreen"), ("siempre", "evergreen"),
                  ("lanzamiento", "lanzamiento"), ("webinar", "lanzamiento"), ("vivo", "lanzamiento"), ("live", "lanzamiento"), ("plf", "lanzamiento"), ("evento", "lanzamiento")]

def modo_de(e, s):
    """Normaliza el modo (evergreen o lanzamiento). Desconocido → el default del embudo, con aviso."""
    bruto = str(s.get("modo") or "").strip().lower()
    if not bruto: return MODO_DEFAULT[e], ""
    for k, v in MODO_SINONIMOS:
        if k in bruto: return v, ""
    return MODO_DEFAULT[e], f"modo '{bruto}' no reconocido (vale evergreen o lanzamiento): se usa {MODO_DEFAULT[e]}"

def pisos(e, s, lanz_mes=None):
    """Pisos de ROAS sobre cash neto (regla de Jesús Tassarolo): se escala hasta que el ROAS cae al piso de escala
    (evergreen 1,5 · lanzamiento 1,7 con objetivo 2,0); nunca por debajo de 1,3, salvo low-ticket evergreen con mucha
    inversión (30.000 o más por mes) y escalera sólida real (2 bumps + alguna OTO o ascensión), mientras la ganancia sea positiva."""
    modo, aviso = modo_de(e, s); p = dict(PISOS[modo]); p["modo"] = modo; p["nota"] = aviso
    if e == "low_ticket" and modo == "evergreen" and float(s.get("escalera_solida", 0) or 0) >= 1:
        inv_mes = s["inversion"] * (lanz_mes or LANZ_MES[e])
        escalera = s.get("bump1_conv", 0) > 0 and s.get("bump2_conv", 0) > 0 and any(s.get(k, 0) > 0 for k in ("oto1_conv", "oto2_conv", "oto3_conv", "oto4_conv", "ascension_conv"))
        if escalera and inv_mes >= 30000:
            p["absoluto"] = 1.0; p["nota"] = (p["nota"] + "; " if p["nota"] else "") + f"excepción: low-ticket evergreen con {money(inv_mes)} por mes y escalera sólida; se tolera hasta 1,0 mientras la ganancia siga positiva"
        else:
            motivo = "la escalera no es sólida (hacen falta 2 bumps y alguna OTO o ascensión con conversión)" if not escalera else f"la inversión mensual ({money(inv_mes)}) no llega a 30.000"
            p["nota"] = (p["nota"] + "; " if p["nota"] else "") + f"la excepción del piso no aplica: {motivo}"
    return p

def _desc(s): return 1 - s["pasarela"] - s["closers"] - s["reembolsos"]

# Percentiles de conversión por paso (tráfico frío hispano; punto de partida). Debajo de p25 = FUGA · p25 a mediana = MEJORABLE ·
# mediana o más = OK · p75 o más = FORTALEZA. 'precio' = paso opcional: con conversión y precio en 0, NO APLICA. 'informativo' = no elige fuga principal.
PERCENTILES = {
 "low_ticket": [
  dict(k="conv_checkout", label="visita → checkout", p=(0.02, 0.03, 0.05), tocar="la VSL y la oferta del front: gancho, promesa, congruencia con el anuncio, el botón"),
  dict(k="conv_venta", label="checkout → compra", p=(0.15, 0.22, 0.30), tocar="el checkout: fricción, formas de pago, cuotas, garantía, velocidad"),
  dict(calc=lambda s, m: s["conv_checkout"] * s["conv_venta"], label="visita → compra (lectura: producto de los dos pasos)", p=(0.003, 0.0066, 0.015), informativo=True, tocar="el front completo"),
  dict(calc=lambda s, m: d(m["ventas"] * (s["precio_front"] + s["bump1_conv"] * s["bump1_precio"] + s["bump2_conv"] * s["bump2_precio"]) * _desc(s), s["inversion"]), label="ROAS del front sobre cash neto (principal + bumps ÷ pauta)", p=(0.7, 1.0, 1.3), es_ratio=True, tocar="la oferta del front: promesa, precio y bumps. Si el front pierde, se pule la oferta antes de tocar tráfico"),
  dict(k="bump1_conv", precio="bump1_precio", label="bump 1 tomado", p=(0.15, 0.25, 0.35), tocar="el bump: complemento obvio del principal, precio bajo, una casilla, copy de dos líneas"),
  dict(k="bump2_conv", precio="bump2_precio", label="bump 2 tomado", p=(0.10, 0.18, 0.25), tocar="el bump 2: que no compita con el bump 1"),
  dict(k="oto1_conv", precio="oto1_precio", label="OTO 1 tomada", p=(0.05, 0.09, 0.14), tocar="la OTO 1: la consecuencia lógica de lo que acaba de comprar, precio y video corto"),
  dict(k="oto2_conv", precio="oto2_precio", label="OTO 2 tomada", p=(0.03, 0.06, 0.09), tocar="la OTO 2 (downsell): versión más barata o en cuotas de la OTO 1"),
  dict(k="ascension_conv", precio="ascension_precio", label="ascensión al programa", p=(0.01, 0.02, 0.04), tocar="el camino al programa: llamada, aplicación o secuencia después de la compra"),
  dict(calc=lambda s, m: d(m["aov"], s["precio_front"]), label="AOV ÷ precio del principal", p=(1.2, 1.4, 1.7), es_ratio=True, tocar="la escalera entera: sin bumps y OTOs que sumen, el low-ticket no se paga"),
 ],
 "webinar_gratuito": [
  dict(k="conv_landing", label="visita → registro", p=(0.15, 0.22, 0.30), tocar="la landing: promesa igual a la del anuncio, formulario corto, velocidad, un solo llamado a la acción"),
  dict(k="grupo_pct", label="registro → grupo", p=(0.50, 0.65, 0.80), tocar="botón directo al grupo, incentivo concreto por entrar, bienvenida con fecha y hora"),
  dict(k="show_vivo", label="registro → en vivo", p=(0.10, 0.15, 0.22), tocar="recordatorios 24 h / 2 h / 30 min, ventana corta entre registro y evento, calentar el grupo, la expectativa que creó el anuncio"),
  dict(k="show_replay", label="registro → replay", p=(0.40, 0.60, 0.80), tocar="replay el mismo día por WhatsApp y mail, ventana de 72 h"),
  dict(k="solic_vivo_pct", label="en vivo → solicitud", p=(0.05, 0.10, 0.15), tocar="congruencia entre el contenido y la oferta, claridad de la oferta, pitch, momento en que abrís el formulario (sin tocar el precio)"),
  dict(k="solic_replay_pct", label="replay → solicitud", p=(0.01, 0.02, 0.04), tocar="el seguimiento del replay: recordatorios de cierre, escasez real"),
  dict(k="cierre_pct", label="solicitud → compra", p=(0.25, 0.40, 0.55), tocar="seguimiento en minutos, closer, cuotas, nutrición previa"),
  dict(k="bump_conv", precio="bump_precio", label="bump tomado", p=(0.15, 0.25, 0.35), tocar="el bump del checkout"),
  dict(k="backend_conv", precio="backend_precio", label="pasan al programa", p=(0.03, 0.05, 0.08), tocar="el camino al programa superior"),
 ],
 "llamada": [
  dict(k="conv_landing", label="visita → lead", p=(0.15, 0.22, 0.30), tocar="la página: promesa igual a la del anuncio, formulario corto"),
  dict(k="aplic_pct", label="lead → aplicación", p=(0.05, 0.10, 0.18), tocar="el video o la página de aplicación: por qué aplicar y qué gana; primeras preguntas fáciles"),
  dict(k="calif_pct", label="aplicación → calificado", p=(0.40, 0.55, 0.70), tocar="la pregunta que califica y el público del anuncio"),
  dict(k="agenda_pct", label="calificado → agenda", p=(0.40, 0.55, 0.70), tocar="velocidad de respuesta, huecos en el calendario, confirmación por WhatsApp"),
  dict(k="show_llamada", label="agenda → llamada (show)", p=(0.55, 0.65, 0.75), tocar="nutrición antes de la llamada, recordatorios, confirmación; 700 agendas y 100 llamadas no es el closer, es nutrición"),
  dict(k="cierre", label="llamada → venta (cierre)", p=(0.15, 0.25, 0.35), tocar="guion, objeciones, cuotas, calidad del lead; se juzga con 3 o 4 eventos"),
  dict(k="ds_conv", precio="ds_precio", label="downsell tomado", p=(0.05, 0.10, 0.15), tocar="el downsell: versión en cuotas o más chica del programa"),
 ],
 "webinar_pago": [
  dict(k="conv_entrada", label="visita → entrada", p=(0.01, 0.02, 0.035), tocar="la página de ventas de la entrada: promesa, precio escalonado, prueba"),
  dict(calc=lambda s, m: d((s["precio_entrada"] + s["bump_e_conv"] * s["bump_e_precio"]) * _desc(s), s["costo_visita"] / s["conv_entrada"]) if s["conv_entrada"] else 0.0, label="ROAS del front sobre cash neto (entrada + bump ÷ pauta)", p=(0.5, 0.8, 1.2), es_ratio=True, tocar="la página de la entrada y el bump: cerca de 1 el evento se paga solo"),
  dict(k="bump_e_conv", precio="bump_e_precio", label="bump de la entrada tomado", p=(0.15, 0.20, 0.30), tocar="el bump de la entrada"),
  dict(k="grupo_pct", label="entrada → grupo", p=(0.60, 0.80, 0.90), tocar="botón directo al grupo después de pagar"),
  dict(k="show_vivo", label="entrada → en vivo", p=(0.35, 0.50, 0.65), tocar="recordatorios, grupo, horario: ya pagaron, tienen que venir"),
  dict(k="solic_vivo_pct", label="en vivo → solicitud", p=(0.08, 0.14, 0.22), tocar="congruencia contenido-oferta, claridad, pitch"),
  dict(k="cierre_pct", label="solicitud → compra", p=(0.25, 0.40, 0.55), tocar="seguimiento en minutos, closer, cuotas"),
  dict(k="backend_conv", precio="backend_precio", label="pasan al programa", p=(0.05, 0.10, 0.15), tocar="el camino al programa superior"),
 ],
}
HIST_EXTRA = {"cpu", "gan_visita", "roas", "anuncios_nuevos", "frecuencia", "cpm", "reembolsos"}

def fugas(e, s, m, hist=None, tol=0.25):
    """Cada porcentaje entre pasos contra sus percentiles (industria) y contra el promedio propio (hist). Devuelve (filas, principal, semáforo)."""
    filas = []; hist = hist or {}
    for i, it in enumerate(PERCENTILES[e]):
        v = it["calc"](s, m) if "calc" in it else float(s.get(it["k"], 0) or 0)
        p25, p50, p75 = it["p"]
        if "precio" in it and v == 0 and float(s.get(it["precio"], 0) or 0) == 0:
            filas.append(dict(label=it["label"], valor=v, p=it["p"], estado="NO APLICA", brecha=0.0, tocar=it["tocar"], orden=i, propio="", es_ratio=it.get("es_ratio", False), informativo=True)); continue
        estado = "FUGA" if v < p25 else ("MEJORABLE" if v < p50 else ("FORTALEZA" if v >= p75 else "OK"))
        brecha = d(p50 - v, p50) if v < p50 else 0.0
        propio = ""
        if "k" in it and hist.get(it["k"]):
            prom = float(hist[it["k"]]); sh = sem_rel(v, prom, "mayor", tol); dif = d(v - prom, prom)
            propio = f"; tu promedio {pct(prom)} ({'+' if dif >= 0 else ''}{dif*100:.0f} %)".replace(".", ",")
            if sh == "ROJO" and estado != "FUGA": estado = "FUGA"; brecha = max(brecha, -dif); propio += " → fuga contra tu promedio"
            elif sh == "AMARILLO" and estado in ("OK", "FORTALEZA"): estado = "MEJORABLE"; brecha = max(brecha, -dif)
        filas.append(dict(label=it["label"], valor=v, p=it["p"], estado=estado, brecha=brecha, tocar=it["tocar"], orden=i, propio=propio, es_ratio=it.get("es_ratio", False), informativo=it.get("informativo", False)))
    elegibles = [f for f in filas if not f["informativo"] and f["estado"] in ("FUGA", "MEJORABLE")]
    principal = max(elegibles, key=lambda f: (f["estado"] == "FUGA", f["brecha"], -f["orden"])) if elegibles else None
    sem = "ROJO" if any(f["estado"] == "FUGA" for f in elegibles) else ("AMARILLO" if elegibles else "VERDE")
    return filas, principal, sem

def fmt_fuga(f):
    fx = (lambda x: ratio(x)) if f["es_ratio"] else pct
    if f["estado"] == "NO APLICA": return f"{f['label']}: no aplica (no tenés este paso)"
    return f"{f['label']} {fx(f['valor'])} [{f['estado'].lower()}; p25 {fx(f['p'][0])} · mediana {fx(f['p'][1])} · p75 {fx(f['p'][2])}{f.get('propio', '')}]"

ACCION = {
 3: "El problema está después de la página (si el costo por visita está en verde): revisá la fuga principal; no toques el presupuesto.",
 4: "Tráfico caro para tu nicho o contra tu promedio: CPM → CTR → clic a visita → conversión de la landing, en ese orden. Anuncios nuevos hoy. Nunca bajar presupuesto para 'arreglar' el CPL.",
 5: "Alimentá el embudo: 20 a 50 piezas nuevas por semana escalando (10 a 20 sin escalar), 10 a 15 % del presupuesto en testeo, 2 USD por día por anuncio en Latinoamérica, apagar a las 12 h lo que no tiene clics.",
 6: "Cobranza y forma de pago, no tráfico. Reembolsos altos son oferta o expectativa; caja corta es la caja necesaria de la proyección, tenela antes de escalar.",
}
PEOR = {"ROJO": 0, "AMARILLO": 1, "VERDE": 2, "SIN DATOS": 3, "SIN HISTÓRICO": 3}
REF_CPM = {"visita": "bueno 3 a 8 % del CPM, es decir 12 a 30 visitas por cada 1.000 impresiones",
           "registro": "bueno 25 a 40 % del CPM (2,5 a 4 registros por cada 1.000 impresiones), aceptable hasta 67 %; con CPM de 3 un CPL de 1 y con CPM de 25 un CPL de 10 son el mismo embudo",
           "lead": "bueno 25 a 40 % del CPM (2,5 a 4 leads por cada 1.000 impresiones), aceptable hasta 67 %; con CPM de 3 un CPL de 1 y con CPM de 25 un CPL de 10 son el mismo embudo",
           "entrada": "normal entre 1 y 4 veces el CPM (0,25 a 1 entrada por cada 1.000 impresiones); lo que decide es el ROAS del front"}
DIRECCION = {"cpu": "menor", "cpm": "menor", "costo_visita": "menor", "frecuencia": "menor", "reembolsos": "menor"}  # el resto: mayor es mejor

def sem_rel(v, prom, direccion="mayor", tol=0.25):
    """Semáforo contra el promedio propio: verde = igual o mejor; amarillo = hasta `tol` peor; rojo = más que `tol` peor."""
    if prom is None or prom == 0: return None
    if direccion == "menor":
        return "VERDE" if v <= prom else ("AMARILLO" if v <= prom * (1 + tol) else "ROJO")
    return "VERDE" if v >= prom else ("AMARILLO" if v >= prom * (1 - tol) else "ROJO")

def _contra(v, k, hist, tol, fmt, direccion=None):
    """Compara v con el promedio propio de la clave k. Devuelve (semáforo o None, texto)."""
    prom = (hist or {}).get(k)
    if prom is None: return None, "sin histórico"
    sem = sem_rel(v, float(prom), direccion or DIRECCION.get(k, "mayor"), tol)
    dif = d(v - float(prom), float(prom))
    return sem, f"tu promedio {fmt(float(prom))} ({'+' if dif >= 0 else ''}{dif*100:.0f} %)".replace(".", ",")

def macro(e, s, m, hist=None, tol=0.25, lanz_mes=None):
    """¿Gana plata? ¿El ROAS sobre cash neto está sobre el piso de su tipo de embudo? Verde solo por encima del piso de escala;
    en el piso o entre el absoluto y el de escala, amarillo (se frena); debajo del absoluto o perdiendo, rojo."""
    p = pisos(e, s, lanz_mes); r = m["roas"]; g = m["profit"]
    if g <= 0 or r < p["absoluto"]: sem = "ROJO"
    elif r <= p["escala"]: sem = "AMARILLO"
    else: sem = "VERDE"
    estado_g = "no ganás ni perdés" if g == 0 else (f"ganás {money(g)}" if g > 0 else f"perdés {money(abs(g))}")
    txt = (f"{estado_g} en el período; ROAS sobre cash neto {ratio(r)} contra el piso de escala {ratio(p['escala'])} y el objetivo {ratio(p['objetivo'])} "
           f"de un embudo {p['modo']}; nunca debajo de {ratio(p['absoluto'])}")
    sh, th = _contra(r, "roas", hist, tol, ratio)
    if sh: txt += f"; {th}" + (" → cayó más que la tolerancia contra tu propio promedio" if sh == "ROJO" else "")
    if p["nota"]: txt += f" ({p['nota']})"
    if sem == "VERDE": txt += ". Se escala hasta que el ROAS baje al piso de escala; a esa altura se frena y se arregla la fuga principal"
    elif sem == "AMARILLO" and g > 0 and r <= p["escala"] and r >= p["absoluto"]: txt += ". En el piso de escala o debajo: se frena, no se escala"
    return sem, txt, p

def decidir(e, s, m, p, sem_m, fl, principal, sem_f, filas_resto):
    """Una sola decisión, en el orden del autor: macro → fugas → el resto."""
    tocar = f"{principal['label']}: tocar {principal['tocar']}" if principal else ""
    hay_fuga = sem_f == "ROJO"
    front = next((f for f in fl if f["label"].startswith("ROAS del front")), None)
    costo_rojo = m["cpu"] > m["techo"]
    rojo_resto = next((f for f in filas_resto if f[3] == "ROJO"), None); amarillo_resto = next((f for f in filas_resto if f[3] == "AMARILLO"), None)
    if sem_m == "ROJO":
        if front and front["estado"] in ("FUGA", "MEJORABLE") and front["valor"] < 1.0:
            return f"ROJO en Macro: el front pierde (ROAS del front sobre cash neto {ratio(front['valor'])}). Pulí la oferta del front (promesa, precio, bumps) antes de tocar tráfico; no inviertas más hasta que el front se pague solo." + (f" Fuga principal: {tocar}." if principal else "")
        if hay_fuga:
            return f"ROJO en Macro: no inviertas más hasta cerrar la fuga principal ({tocar}). " + ("Perdés plata: " if m["profit"] <= 0 else f"ROAS debajo del piso absoluto {ratio(p['absoluto'])}: ") + "primero la oferta y la cadena, después el tráfico."
        if m["profit"] <= 0 and m["vpu"] > m["cpu"] and m["roas"] >= p["escala"]:
            unidades = d(s["fijos"], m["vpu"] - m["cpu"]); inv = unidades * m["cpu"]
            return f"ROJO en Macro por los fijos, no por el embudo: cada {m['unidad']} deja {money(m['vpu'] - m['cpu'])} por encima de su costo y la cadena está sana. La pérdida son los fijos de {money(s['fijos'])}: necesitás {entero(unidades)} {m['unidad']}s por período (≈ {money(inv)} de inversión) para cubrirlos, o bajar los fijos. Subí de a escalones de 25 % mientras el ROAS se mantenga sobre {ratio(p['escala'])}."
        if costo_rojo:
            return f"ROJO en Macro con la cadena sana: el problema es el valor por {m['unidad']} contra lo que pagás (costo {money(m['cpu'])} sobre el techo {money(m['techo'])}). {ACCION[4]}" + (f" Lo mejorable: {tocar}." if principal else "")
        if m["profit"] > 0:
            return f"ROJO en Macro: ROAS {ratio(m['roas'])} debajo del piso absoluto {ratio(p['absoluto'])} sin fugas en la cadena: bajá un escalón (−25 %) y medí 7 días hasta volver sobre el piso de escala {ratio(p['escala'])}." + (f" Lo mejorable: {tocar}." if principal else "")
        return f"ROJO en Macro: perdés plata sin una fuga clara en la cadena. Revisá la oferta (precio, escalera) y los costos fijos antes de invertir más." + (f" Lo mejorable: {tocar}." if principal else "")
    if rojo_resto:
        return f"{rojo_resto[3]} en «{rojo_resto[1]}»: {ACCION[rojo_resto[0]]}" + (f" Y antes de escalar, cerrá la fuga principal ({tocar})." if hay_fuga else "")
    if hay_fuga:
        return f"Hay una FUGA aunque el macro {'esté en verde' if sem_m == 'VERDE' else 'aguante'}: antes de escalar, cerrá {tocar}. Cerrar una fuga es ganar más sin pagar más."
    if sem_m == "AMARILLO":
        return f"AMARILLO en Macro: ROAS {ratio(m['roas'])} en el piso de escala ({ratio(p['escala'])}) o entre el piso absoluto y el de escala. No escales: sostené" + (f" y mejorá lo mejorable ({tocar})." if principal else " y buscá qué mejorar en la cadena.")
    if amarillo_resto:
        return f"AMARILLO en «{amarillo_resto[1]}»: {ACCION[amarillo_resto[0]]} Cuando esté en verde, subí un escalón (+25 %)." + (f" Lo mejorable: {tocar}." if principal else "")
    if sem_f == "AMARILLO":
        return f"Macro en verde y sin fugas bajo p25: subí un escalón (+25 %) y medí 7 días; frená cuando el ROAS baje a {ratio(p['escala'])}. Lo mejorable ({principal['label']}, {(ratio if principal['es_ratio'] else pct)(principal['valor'])}) queda anotado para la semana siguiente: tocar {principal['tocar']}."
    return f"Todo en verde y sin fugas: subí un escalón (+25 %) y medí 7 días; frená cuando el ROAS baje a {ratio(p['escala'])}. Si venís de bajar, dos semanas en verde antes de subir."

def radiografia(e, s, m, testeo=None, hist=None, tol=0.25, lanz_mes=None):
    """Lo que más importa, en orden: 1 macro · 2 fugas · 3 ganancia por visita · 4 costo por unidad (solo relativo) · 5 testeo · 6 cash."""
    hist = hist or {}; I = s["inversion"]; filas = []
    sem_m, txt_m, p = macro(e, s, m, hist, tol, lanz_mes)
    filas.append((1, "Macro: ¿gana plata y el ROAS está sobre el piso?", txt_m, sem_m))
    fl, principal, sem_f = fugas(e, s, m, hist, tol)
    txt = "; ".join(fmt_fuga(f) for f in fl)
    if principal:
        txt += f". FUGA PRINCIPAL: {principal['label']} ({(ratio if principal['es_ratio'] else pct)(principal['valor'])}, {principal['brecha']*100:.0f} % debajo de tu referencia): tocar {principal['tocar']}"
    filas.append((2, "Fugas en la cadena (porcentaje entre pasos contra percentiles de la industria y contra tu promedio)", txt, sem_f))
    vis = next((q for n, q, *_ in m["etapas"] if n.startswith("Visitas")), m["unidades"])
    gpv, cpv = d(m["profit"], vis), d(I, vis)
    sem, t2 = _contra(gpv, "gan_visita", hist, tol, money)
    if gpv <= 0: sem, t2 = "ROJO", "perdés plata por cada visita"
    filas.append((3, "Ganancia por visita", f"{money(gpv)} por visita (costo por visita {money(cpv)}); {t2}", sem or "SIN HISTÓRICO"))
    sem_t = "ROJO" if m["cpu"] > m["techo"] else ("AMARILLO" if m["cpu"] > m["objetivo"] else "VERDE")
    sem_h, t3 = _contra(m["cpu"], "cpu", hist, tol, money)
    sem = min([x for x in (sem_t, sem_h) if x], key=lambda x: PEOR[x])
    cpm = s.get("cpm") or hist.get("cpm")
    if cpm:
        cpm = float(cpm); por_mil = d(cpm, m["cpu"]); razon = d(m["cpu"], cpm); ref = REF_CPM.get(m["unidad"], "")
        txt_cpm = f"; en tu nicho: {money(m['cpu'])} es el {razon*100:.0f} % de tu CPM de {money(cpm)}, {por_mil:.1f} {m['unidad']}s por cada 1.000 impresiones".replace(f"{por_mil:.1f}", f"{por_mil:.1f}".replace(".", ",")) + (f" (práctica: {ref})" if ref else "")
    else:
        txt_cpm = "; pasá tu CPM (--historico cpm=…) para leer el costo en relación a tu nicho: el umbral de costo depende del CPM"
    filas.append((4, f"Costo por {m['unidad']} (solo relativo: nunca contra un número absoluto)", f"{money(m['cpu'])} contra tu techo {money(m['techo'])} y tu objetivo {money(m['objetivo'])}; {t3}{txt_cpm}", sem))
    if testeo:
        an = testeo.get("anuncios_nuevos"); pt = testeo.get("pct_testeo"); dg = testeo.get("dias_ganador"); fr = testeo.get("frecuencia")
        avisos, sems = [], []
        if an is not None:
            sh, th = _contra(an, "anuncios_nuevos", hist, tol, lambda x: f"{x:.0f}")
            if an == 0: avisos.append("0 anuncios nuevos en 7 días"); sems.append("ROJO" if filas[3][3] != "VERDE" else "AMARILLO")
            elif sh: avisos.append(f"{an:.0f} anuncios nuevos por semana; {th}"); sems.append(sh)
            else: avisos.append(f"{an:.0f} anuncios nuevos por semana (sin histórico; práctica: 10 a 20 sin escalar, 20 a 50 escalando)")
        if fr is not None:
            sh, th = _contra(fr, "frecuencia", hist, tol, lambda x: f"{x:.2f}".replace(".", ","))
            if sh: avisos.append(f"frecuencia {ratio(fr)[:-1]}; {th}"); sems.append(sh)
            else: avisos.append(f"frecuencia {ratio(fr)[:-1]} (sin histórico)")
        if pt is not None: avisos.append(f"testeo {pct(pt)} del presupuesto (práctica: 10 a 15 % escalando)")
        if dg is not None: avisos.append(f"el ganador principal tiene {dg:.0f} días")
        sem = min(sems, key=lambda x: PEOR[x]) if sems else "SIN HISTÓRICO"
        filas.append((5, "Testeo", "; ".join(avisos) if avisos else "sin datos de testeo", sem))
    else:
        filas.append((5, "Testeo", "sin datos: cargá anuncios nuevos por semana, % del presupuesto en testeo, días del ganador principal y frecuencia (--testeo), y tu ritmo habitual (--historico anuncios_nuevos=…)", "SIN HISTÓRICO"))
    r = s["reembolsos"]; sh, th = _contra(r, "reembolsos", hist, tol, pct)
    sem = sh or "SIN HISTÓRICO"
    if m["roas_m1"] < 1.0: sem = "AMARILLO" if sem in ("VERDE", "SIN HISTÓRICO") else sem
    filas.append((6, "Cash contra facturado", f"cobranza del primer mes {pct(s['cobro_m1'])}; el primer mes entra {ratio(m['roas_m1'])} la pauta" + (" (no cubre la pauta del mes que viene)" if m["roas_m1"] < 1.0 else "") + f"; reembolsos {pct(r)}; {th}", sem))
    decision = decidir(e, s, m, p, sem_m, fl, principal, sem_f, filas[2:])
    sin_hist = [f[1] for f in filas if f[3] == "SIN HISTÓRICO"]
    if sin_hist:
        decision += f" Sin umbral propio todavía en: {', '.join(sin_hist)}. Cargá la mediana de tus últimas 4 semanas (--historico o --periodos)."
    return filas, decision

def pct(x): return f"{x*100:.1f}".replace(".", ",") + " %"
def ratio(x): return f"{x:.2f}".replace(".", ",") + "x"
def proyeccion(e, s, m, meses=12, crecimiento=0.10, lanz_mes=None, cobranza=None, caja_inicial=0.0):
    """Proyección mes a mes: inversión creciendo, cash según la cobranza (mes 1 / 2 / 3), ganancia de caja y caja necesaria."""
    lanz_mes = lanz_mes or LANZ_MES[e]
    if cobranza is None:
        m1 = s.get("cobro_m1", 1.0); cobranza = [m1, (1 - m1) / 2, (1 - m1) / 2]
    cpu = m["cpu"]; fact_u = d(m["facturado"], m["unidades"]); ven_u = d(m["ventas"], m["unidades"]); desc = 1 - s["pasarela"] - s["closers"] - s["reembolsos"]
    filas, facts, acum = [], [], 0.0
    for i in range(meses):
        inv = s["inversion"] * lanz_mes * (1 + crecimiento) ** i
        uni = d(inv, cpu); fact = uni * fact_u; facts.append(fact)
        cash = sum(facts[i - k] * cobranza[k] for k in range(len(cobranza)) if i - k >= 0)
        gan = cash * desc - uni * s["costo_semivar"] - s["fijos"] * lanz_mes - inv; acum += gan
        filas.append(dict(mes=i + 1, inversion=inv, unidades=uni, ventas=uni * ven_u, facturado=fact, cash=cash, ganancia=gan, acumulado=acum))
    peor = min(f["acumulado"] for f in filas)
    return dict(filas=filas, caja_necesaria=max(0.0, -peor), saldo_minimo=caja_inicial + peor, ganancia_12m=acum, cobranza=cobranza, lanz_mes=lanz_mes, crecimiento=crecimiento)

def money(x): return ("$" + f"{x:,.2f}").replace(",", "X").replace(".", ",").replace("X", ".")
def entero(x): return f"{x:,.0f}".replace(",", ".")

def reporte(e, s, testeo=None, hist=None, tol=0.25, proy=None, nombre=None):
    m = modelo(e, s); sens = sensibilidad(e, s); un = m["unidad"]
    filas, decision = radiografia(e, s, m, testeo, hist, tol, (proy or {}).get("lanz_mes")); m["radiografia"] = filas; m["decision"] = decision
    L = [f"EMBUDO: {e}" + (f" · {nombre}" if nombre else "") + "   (supuestos en uso: los que cargaste; lo demás, el ejemplo)",
         f"LO QUE MÁS IMPORTA, en orden (se para en el primer rojo). Primero el macro, después las fugas por porcentaje; los costos solo en relación al CPM y a tu promedio (tolerancia {tol:.0%}):"]
    for n, nombre_f, lectura, sem in filas:
        L.append(f"   [{sem:<9}] {n}. {nombre_f}: {lectura}")
    L.append(f"DECISIÓN (una sola, medir 7 días): {decision}")
    L += ["TUS UMBRALES (hasta cuánto pagar por cada paso, con lo que pagás hoy al lado):",
         f"Tu {un} vale (cash neto):            {money(m['vpu'])}",
         f"Hasta cuánto podés pagar (techo):    {money(m['techo'])}   <- acá no ganás ni perdés",
         f"Cuánto te conviene pagar (objetivo): {money(m['objetivo'])}   <- con {s['margen_seg']:.0%} de colchón",
         "Por cada paso: lo que pagás hoy, lo que te queda y lo máximo que podrías pagar (techo = costo + ganancia + fijos repartidos):"]
    for n, q, c, t, g in m["etapas"]:
        L.append(f"   {n:<24} cantidad {entero(q):>9}   pagás hoy {money(c):>10}   te queda {money(g):>10}   techo {money(t):>10}")
    L += [f"Con tu costo actual de {money(m['cpu'])} por {un}: SEMÁFORO {m['semaforo']}  (ROAS sobre cash neto {ratio(m['roas'])}; objetivo {ratio(s['roas_obj'])}; el primer mes entra {ratio(m['roas_m1'])})",
          f"Ganancia del período: {money(m['profit'])}   |   ganancia por {un}: {money(m['gan_unidad'])}   |   CPA {money(m['cpa'])}   |   AOV {money(m['aov'])} (neto {money(m['aov_neto'])})"]
    if m["inv_meta"] is None:
        L.append(f"Para {s['meta_ventas']} ventas por período: inalcanzable con estos supuestos (la conversión a venta es 0)")
    else:
        L.append(f"Para {s['meta_ventas']} ventas por período necesitás invertir ≈ {money(m['inv_meta'])} (al costo actual) o {money(m['inv_meta_obj'])} (al objetivo)")
    L.append("La palanca que más mueve (+10 % en cada una): " + "; ".join(f"{lab}: {money(dp)}" for lab, dp in sens[:3]))
    proy = proy or {}
    P = proyeccion(e, s, m, proy.get("meses", 12), proy.get("crecimiento", 0.10), proy.get("lanz_mes"), proy.get("cobranza"), proy.get("caja_inicial", 0.0))
    L.append(f"TU PROYECCIÓN ({len(P['filas'])} meses; {P['lanz_mes']} período(s) por mes; inversión +{P['crecimiento']:.0%} por mes; cobranza {' / '.join(f'{c:.0%}' for c in P['cobranza'])}):")
    L.append(f"   {'mes':>3} {'inversión':>11} {'unidades':>9} {'ventas':>7} {'facturado':>11} {'cash cobrado':>13} {'ganancia caja':>14} {'acumulado':>12}")
    for f in P["filas"]:
        if f["mes"] in (1, 2, 3, 6, 9, 12) or f["mes"] == len(P["filas"]):
            L.append(f"   {f['mes']:>3} {money(f['inversion']):>11} {entero(f['unidades']):>9} {f['ventas']:>7.1f} {money(f['facturado']):>11} {money(f['cash']):>13} {money(f['ganancia']):>14} {money(f['acumulado']):>12}")
    L.append(f"   Caja necesaria para no frenar la pauta: {money(P['caja_necesaria'])} (peor momento del acumulado)" + (" → el embudo se autofinancia" if P["caja_necesaria"] == 0 else f"; con tu caja inicial el saldo mínimo es {money(P['saldo_minimo'])}"))
    L.append(f"   Ganancia de caja acumulada en el período: {money(P['ganancia_12m'])}")
    m["proyeccion"] = P
    L.append(MARCA)
    return "\n".join(L), m, sens

def html(e, s, m, sens, path):
    W = 900; pasos = m["etapas"]; mx = max((q for _, q, *_ in pasos), default=0) or 1
    rows = ""; y = 40
    for n, q, c, t, g in pasos:
        w = max(4, 400 * q / mx); col = "#DC2626" if c > t else ("#00996A" if c <= t / (1 + s["margen_seg"]) else "#F59E0B")
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
<h2 style="font-size:15px;margin:0 0 6px">Lo que más importa, en orden</h2>
<table style="border-collapse:collapse;font-size:12px;margin:0 0 14px">{"".join(f'<tr><td style="padding:3px 8px 3px 0;white-space:nowrap"><span style="display:inline-block;width:10px;height:10px;border-radius:5px;background:{ {"VERDE":"#00996A","AMARILLO":"#F59E0B","ROJO":"#DC2626"}.get(sem,"#9A9A9E") };margin-right:6px"></span><b>{n}. {nombre}</b></td><td style="padding:3px 0;color:#3D3D40">{lectura}</td></tr>' for n, nombre, lectura, sem in m.get("radiografia", []))}</table>
<p style="font-size:13px;margin:0 0 14px"><b>Decisión:</b> {m.get("decision", "")}</p>
<svg viewBox="0 0 {W} {H}" width="100%" style="max-width:{W}px;display:block">
<text x="10" y="22" font-size="14" font-weight="700">El embudo: cantidad por paso (barra), costo hoy vs techo (punto: verde dentro del objetivo, ámbar entre objetivo y techo, rojo por encima)</text>{rows}
<text x="10" y="{y+18}" font-size="14" font-weight="700">Qué palanca mueve más la ganancia (+10 % en cada una)</text>{srows}
<text x="10" y="{H-14}" font-size="10" fill="#6B6B70">{MARCA}</text></svg></body></html>'''
    open(path, "w", encoding="utf-8").write(doc)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--embudo", choices=list(SUPUESTOS), help="tipo de embudo (obligatorio si no hay --perfil)")
    ap.add_argument("--perfil", help="perfil/mi_embudo.json: embudo, supuestos, historico, testeo, proyeccion y tolerancia de la persona; con esto no hace falta nada más")
    ap.add_argument("--json", help="archivo JSON con supuestos (solo los que quieras cambiar)")
    ap.add_argument("--set", nargs="*", default=[], help="clave=valor (porcentajes como 0.15)")
    ap.add_argument("--html", help="escribe un gráfico HTML en esta ruta")
    ap.add_argument("--supuestos", action="store_true", help="lista los supuestos y sus valores de ejemplo")
    ap.add_argument("--testeo", nargs="*", default=None, help="datos de testeo: anuncios_nuevos=12 pct_testeo=0.10 dias_ganador=20 frecuencia=2.1")
    ap.add_argument("--historico", nargs="*", default=None, help="TUS promedios (mediana de las últimas 4 semanas o último mes de la campaña madre): cpu=1.10 gan_visita=0.40 conv_landing=0.21 show_vivo=0.14 cierre_pct=0.38 roas=2.8 anuncios_nuevos=15 frecuencia=2.0 reembolsos=0.05 …")
    ap.add_argument("--periodos", help="JSON con una lista de períodos (cada uno un objeto con las mismas claves); se usa la mediana de cada clave como histórico")
    ap.add_argument("--tolerancia", type=float, default=0.25, help="cuánto peor que tu promedio se tolera antes del rojo (0.20 a 0.30; default 0.25)")
    a = ap.parse_args(); perfil = {}
    if a.perfil:
        perfil = json.load(open(a.perfil, encoding="utf-8")); a.embudo = a.embudo or perfil.get("embudo")
    if not a.embudo:
        ap.error("falta --embudo (o un --perfil con la clave 'embudo')")
    s = dict(SUPUESTOS[a.embudo]); s.update({k: v for k, v in perfil.get("supuestos", {}).items() if k in s})
    if a.supuestos:
        for k, v in s.items(): print(f"{k} = {v}")
        return
    if a.json: s.update(json.load(open(a.json, encoding="utf-8")))
    for kv in a.set:
        k, v = kv.split("=")
        try: s[k] = float(v)
        except ValueError: s[k] = v
    testeo = dict(perfil.get("testeo", {})) or None
    if a.testeo is not None:
        testeo = dict(testeo or {})
        for kv in a.testeo:
            k, v = kv.split("="); testeo[k] = float(v)
    hist = dict(perfil.get("historico", {}))
    if a.periodos:
        import statistics
        try: filas_p = json.load(open(a.periodos, encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as ex: ap.error(f"--periodos espera un archivo JSON con una lista de objetos (una fila por semana, claves como en --historico): {ex}")
        if not isinstance(filas_p, list) or not all(isinstance(f, dict) for f in filas_p): ap.error("--periodos: el JSON tiene que ser una lista de objetos")
        claves = set().union(*[set(f) for f in filas_p]) if filas_p else set()
        for k in claves:
            vals = []
            for f in filas_p:
                try: vals.append(float(f[k]))
                except (KeyError, TypeError, ValueError): pass
            if vals: hist[k] = statistics.median(vals)
    if a.historico:
        for kv in a.historico:
            k, v = kv.split("="); hist[k] = float(v)
    conocidas = set(SUPUESTOS[a.embudo]) | HIST_EXTRA
    for k in list(hist):
        if k not in conocidas: print(f"aviso: clave de histórico desconocida y sin efecto: {k}"); hist.pop(k)
    tol = perfil.get("tolerancia", a.tolerancia)
    texto, m, sens = reporte(a.embudo, s, testeo, hist or None, tol, perfil.get("proyeccion"), perfil.get("nombre")); print(texto)
    if a.html:
        html(a.embudo, s, m, sens, a.html); print(f"gráfico: {a.html}")

if __name__ == "__main__":
    main()
