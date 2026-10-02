#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generador de los Excel de MÉTRICAS DIARIAS por embudo (mastermind): uno por embudo, con el mismo
lenguaje que los modelos financieros. Hojas: Inicio · Config · Diario (una fila por día; amarillo = entrada,
azul = cálculo) · Semanal (comparativo semanal con promedio, mediana, mejor, peor y el bloque "contra tu
promedio": mediana de las 4 semanas anteriores y semáforo con tolerancia) · Resumen (KPIs de la semana
elegida contra la anterior, la mediana previa y tu meta).

Uso:  python3 md_build.py [carpeta_salida] [--dias N]
Solo funciones básicas (IF, IFERROR, SUMIFS, COUNT, MEDIAN, AVERAGE, MIN, MAX, INDEX, INT, OR) para que
funcione igual en Excel, Google Sheets y Numbers.
"""
import os, re, sys, random, datetime, argparse
import openpyxl
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Font
from openpyxl.worksheet.datavalidation import DataValidation

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "modelos_financieros")); sys.path.insert(0, os.path.join(HERE, ".."))
from mf_core import (FILL_IN, FILL_OUT, FILL_HDR, FILL_SEC, FILL_OK, FILL_WARN, FILL_BAD, FONT_HDR, FONT_B, FONT_TITLE,
                     FONT_NOTE, BORDER, WRAP, CENTER, FMT, col)
from mf_comun import MARCA, VERSION

DEFAULT_OUT = os.path.normpath(os.path.join(HERE, "..", "..", "excel", "metricas-diarias"))
INICIO = datetime.date(2026, 9, 7)        # un lunes
SEMANAS = 26
FMT = dict(FMT); FMT["fecha"] = "dd/mm/yyyy"

# ------------------------------------------------------------ piezas comunes a los cuatro embudos
ADS_INPUTS = [
    ("inversion", "Inversión en publicidad (USD)", "money0", "Lo que gastaste ese día en todas las campañas de este embudo."),
    ("impresiones", "Impresiones", "int", "Del administrador de anuncios."),
    ("alcance", "Alcance (personas únicas)", "int", "Para calcular la frecuencia."),
    ("clics_enlace", "Clics en el enlace", "int", "Los clics que van a tu página (no los clics totales)."),
    ("visitas", "Visitas a la página", "int", "Del pixel o de tu página. Nunca es igual a los clics."),
]
ADS_CALC = [
    ("cpm", "CPM", "{inversion}/{impresiones}*1000", "money", "menor"),
    ("frecuencia", "Frecuencia", "{impresiones}/{alcance}", "num", "menor"),
    ("ctr", "CTR al enlace", "{clics_enlace}/{impresiones}", "pct2", "mayor"),
    ("cpc", "CPC (por clic en el enlace)", "{inversion}/{clics_enlace}", "money", "menor"),
    ("clic_visita", "% clic → visita", "{visitas}/{clics_enlace}", "pct", "mayor"),
    ("costo_visita", "Costo por visita", "{inversion}/{visitas}", "money", "menor"),
    ("visitas_mil", "Visitas por cada 1.000 impresiones", "{visitas}/{impresiones}*1000", "num1", "mayor"),
]
def RESULTADO(unidad_key, unidad_label):
    return [
        ("cash_neto", "Cash neto (después de comisiones y reembolsos)", "{facturado}*(1-{cfg:pasarela}-{cfg:closers}-{cfg:reembolsos})", "money0", "mayor"),
        ("ganancia", "Ganancia (cash neto − pauta − fijos)", "{cash_neto}-{inversion}-{fijos_periodo}", "money0", "mayor"),
        ("roas", "ROAS sobre cash neto", "{cash_neto}/{inversion}", "ratio", "mayor"),
        ("gan_visita", "Ganancia por visita (la métrica más valiosa)", "{ganancia}/{visitas}", "money", "mayor"),
        ("margen_visita", "Margen por visita (ganancia por visita ÷ costo por visita)", "{gan_visita}/{costo_visita}", "ratio", "mayor"),
        ("gan_unidad", f"Ganancia por {unidad_label}", "{ganancia}/{" + unidad_key + "}", "money", "mayor"),
    ]
CFG_COMUN = [
    ("pasarela", "Comisión de la pasarela de pago", 0.10, "pct", "Lo que se queda la plataforma de cobro."),
    ("closers", "Comisión del equipo de ventas", 0.0, "pct", "Si vendés por llamada: lo que cobra el closer sobre lo cobrado."),
    ("reembolsos", "Reembolsos y contracargos", 0.05, "pct", "Promedio histórico. 5 % es normal en productos digitales."),
    ("fijos_dia", "Costos fijos por día (USD)", 50, "money0", "Equipo, herramientas, edición: lo que pagás aunque no vendas, dividido por 30."),
    ("roas_obj", "ROAS objetivo sobre cash neto", 2.0, "ratio", "El retorno mínimo que querés por cada dólar, ya neto."),
    ("tolerancia", "Tolerancia del semáforo contra tu promedio", 0.25, "pct", "Igual o mejor que tu mediana = verde; hasta esta distancia peor = amarillo; más = rojo. 20 a 30 %."),
]

SPECS = {
 "low_ticket": dict(
    archivo="01_Metricas_Diarias_Embudo_Low_Ticket.xlsx", titulo="Métricas diarias · Embudo low-ticket con VSL, bumps y OTOs",
    unidad=("comprador", "compradores"), unidad_key="ventas_front",
    config=[("p_front", "Precio del producto principal", 37, "money", ""), ("p_bump1", "Precio del bump 1", 17, "money", ""), ("p_bump2", "Precio del bump 2", 17, "money", ""),
            ("p_oto1", "Precio de la OTO 1", 47, "money", ""), ("p_oto2", "Precio de la OTO 2", 17, "money", ""), ("p_oto3", "Precio de la OTO 3", 97, "money", ""),
            ("p_oto4", "Precio de la OTO 4", 27, "money", ""), ("p_asc", "Precio del programa (ascensión)", 297, "money", "")] + CFG_COMUN,
    inputs=ADS_INPUTS + [("checkouts", "Inician el checkout", "int", "Del checkout o del pixel (iniciar pago)."), ("ventas_front", "Compran el producto principal", "int", ""),
            ("bump1", "Toman el bump 1", "int", ""), ("bump2", "Toman el bump 2", "int", ""), ("oto1", "Toman la OTO 1", "int", ""), ("oto2", "Toman la OTO 2", "int", ""),
            ("oto3", "Toman la OTO 3", "int", ""), ("oto4", "Toman la OTO 4", "int", ""), ("ascension", "Ascienden al programa", "int", "")],
    calc=ADS_CALC + [("conv_checkout", "% visita → checkout", "{checkouts}/{visitas}", "pct", "mayor"), ("conv_venta", "% checkout → compra", "{ventas_front}/{checkouts}", "pct", "mayor"),
            ("conv_visita_venta", "% visita → compra", "{ventas_front}/{visitas}", "pct2", "mayor"), ("cpa", "CPA (costo por comprador)", "{inversion}/{ventas_front}", "money", "menor"),
            ("pct_bump1", "% toman el bump 1", "{bump1}/{ventas_front}", "pct", "mayor"), ("pct_bump2", "% toman el bump 2", "{bump2}/{ventas_front}", "pct", "mayor"),
            ("pct_oto1", "% toman la OTO 1", "{oto1}/{ventas_front}", "pct", "mayor"), ("pct_asc", "% ascienden", "{ascension}/{ventas_front}", "pct", "mayor"),
            ("facturado", "Facturado (toda la escalera)", "{ventas_front}*{cfg:p_front}+{bump1}*{cfg:p_bump1}+{bump2}*{cfg:p_bump2}+{oto1}*{cfg:p_oto1}+{oto2}*{cfg:p_oto2}+{oto3}*{cfg:p_oto3}+{oto4}*{cfg:p_oto4}+{ascension}*{cfg:p_asc}", "money0", "mayor"),
            ("aov", "Order value (facturado por comprador)", "{facturado}/{ventas_front}", "money", "mayor")]
         + RESULTADO("ventas_front", "comprador") + [("aov_neto_cpa", "AOV neto − CPA (lo que queda por comprador)", "{cash_neto}/{ventas_front}-{cpa}", "money", "mayor")],
    grupos=[("1. Anuncios", ["inversion", "impresiones", "alcance", "clics_enlace", "visitas", "cpm", "frecuencia", "ctr", "cpc", "clic_visita", "costo_visita", "visitas_mil"]),
            ("2. Página de ventas y compra", ["checkouts", "ventas_front", "conv_checkout", "conv_venta", "conv_visita_venta", "cpa"]),
            ("3. Escalera", ["bump1", "bump2", "oto1", "oto2", "oto3", "oto4", "ascension", "pct_bump1", "pct_bump2", "pct_oto1", "pct_asc", "aov"]),
            ("4. Resultado", ["facturado", "cash_neto", "ganancia", "roas", "gan_visita", "margen_visita", "gan_unidad", "aov_neto_cpa"])],
    clave=["gan_visita", "costo_visita", "conv_checkout", "conv_venta", "cpa", "aov", "roas", "cpm", "ctr", "frecuencia"],
    resumen=["inversion", "visitas", "costo_visita", "ventas_front", "cpa", "conv_checkout", "conv_venta", "aov", "facturado", "cash_neto", "ganancia", "gan_visita", "roas", "cpm", "ctr"],
    norte="AOV neto contra CPA: cada comprador tiene que dejar más de lo que costó traerlo."),
 "webinar_gratuito": dict(
    archivo="02_Metricas_Diarias_Embudo_Webinar_Gratuito.xlsx", titulo="Métricas diarias · Embudo de webinar gratuito",
    unidad=("registro", "registros"), unidad_key="registros",
    config=[("p_oferta", "Precio de la oferta del webinar", 297, "money", ""), ("p_bump", "Precio del bump", 47, "money", ""), ("p_backend", "Precio del programa superior", 997, "money", "")]
           + [c if c[0] != "fijos_dia" else ("fijos_dia", "Costos fijos por día (USD)", 170, "money0", "Lo que pagás aunque no vendas, dividido por los días del período.") for c in CFG_COMUN],
    inputs=ADS_INPUTS + [("registros", "Registros (leads)", "int", "Todos los que dejaron sus datos."), ("registros_calif", "Registros calificados", "int", "Si el formulario califica; si no, dejá vacío."),
            ("grupo", "Entran al grupo de WhatsApp", "int", ""), ("en_vivo", "Asistentes en vivo", "int", "El día del webinar."), ("replay", "Ven el replay", "int", ""),
            ("solicitudes", "Solicitudes (formulario de compra, aplicación o vendedor)", "int", "Lo que hace el asistente cuando presentás la oferta."),
            ("ventas_front", "Compran la oferta", "int", ""), ("bump", "Toman el bump", "int", ""), ("backend", "Pasan al programa superior", "int", "")],
    calc=ADS_CALC + [("conv_landing", "% visita → registro (conversión de la landing)", "{registros}/{visitas}", "pct", "mayor"), ("cpl", "CPL (costo por registro)", "{inversion}/{registros}", "money", "menor"),
            ("cpl_calif", "CPL calificado", "{inversion}/{registros_calif}", "money", "menor"), ("cpl_cpm", "CPL como % del CPM (el umbral depende del nicho)", "{cpl}/{cpm}", "pct", "menor"),
            ("registros_mil", "Registros por cada 1.000 impresiones", "{registros}/{impresiones}*1000", "num1", "mayor"),
            ("pct_grupo", "% registro → grupo", "{grupo}/{registros}", "pct", "mayor"), ("costo_grupo", "Costo por persona en el grupo", "{inversion}/{grupo}", "money", "menor"),
            ("pct_vivo", "% registro → en vivo", "{en_vivo}/{registros}", "pct", "mayor"), ("pct_replay", "% registro → replay", "{replay}/{registros}", "pct", "mayor"),
            ("costo_asistente", "Costo por asistente en vivo", "{inversion}/{en_vivo}", "money", "menor"), ("pct_solic", "% en vivo → solicitud", "{solicitudes}/{en_vivo}", "pct", "mayor"),
            ("costo_solicitud", "Costo por solicitud", "{inversion}/{solicitudes}", "money", "menor"), ("cierre", "% solicitud → compra", "{ventas_front}/{solicitudes}", "pct", "mayor"),
            ("conv_lead_venta", "% registro → compra", "{ventas_front}/{registros}", "pct2", "mayor"), ("cpa", "CPA (costo por comprador)", "{inversion}/{ventas_front}", "money", "menor"),
            ("pct_bump", "% toman el bump", "{bump}/{ventas_front}", "pct", "mayor"), ("pct_backend", "% pasan al programa", "{backend}/{ventas_front}", "pct", "mayor"),
            ("facturado", "Facturado (oferta + bump + programa)", "{ventas_front}*{cfg:p_oferta}+{bump}*{cfg:p_bump}+{backend}*{cfg:p_backend}", "money0", "mayor"),
            ("aov", "Order value (facturado por comprador)", "{facturado}/{ventas_front}", "money", "mayor")] + RESULTADO("registros", "registro"),
    grupos=[("1. Anuncios", ["inversion", "impresiones", "alcance", "clics_enlace", "visitas", "cpm", "frecuencia", "ctr", "cpc", "clic_visita", "costo_visita", "visitas_mil"]),
            ("2. Landing y registros", ["registros", "registros_calif", "conv_landing", "cpl", "cpl_calif", "cpl_cpm", "registros_mil"]),
            ("3. Grupo y webinar", ["grupo", "en_vivo", "replay", "pct_grupo", "costo_grupo", "pct_vivo", "pct_replay", "costo_asistente"]),
            ("4. Oferta y ventas", ["solicitudes", "ventas_front", "bump", "backend", "pct_solic", "costo_solicitud", "cierre", "conv_lead_venta", "cpa", "pct_bump", "pct_backend", "aov"]),
            ("5. Resultado", ["facturado", "cash_neto", "ganancia", "roas", "gan_visita", "margen_visita", "gan_unidad"])],
    clave=["gan_visita", "costo_visita", "cpl", "cpl_cpm", "conv_landing", "cpm", "ctr", "frecuencia", "pct_vivo", "pct_solic", "cierre", "roas"],
    resumen=["inversion", "visitas", "costo_visita", "registros", "cpl", "cpl_cpm", "conv_landing", "en_vivo", "pct_vivo", "solicitudes", "pct_solic", "ventas_front", "cierre", "cpa", "facturado", "cash_neto", "ganancia", "gan_visita", "roas", "cpm", "ctr"],
    norte="Lo que vale un registro contra lo que te cuesta, y el CPL leído contra tu CPM: con CPM de 3 un CPL de 1 y con CPM de 25 un CPL de 10 son el mismo embudo."),
 "llamada": dict(
    archivo="03_Metricas_Diarias_Embudo_de_Llamada.xlsx", titulo="Métricas diarias · Embudo de llamada (high ticket)",
    unidad=("lead", "leads"), unidad_key="leads",
    config=[("ticket", "Precio del programa (ticket)", 1500, "money", "A precio de lista; las cuotas van en el cash cobrado."), ("p_ds", "Precio del downsell", 497, "money", ""),
            ("cobro_m1", "% del facturado que entra el primer mes (si no cargás el cash cobrado)", 0.60, "pct", "Se usa solo cuando la columna de cash cobrado está vacía.")]
           + [("pasarela", "Comisión de la pasarela de pago", 0.05, "pct", ""), ("closers", "Comisión del equipo de ventas", 0.10, "pct", "Sobre lo cobrado."),
              ("reembolsos", "Reembolsos y contracargos", 0.05, "pct", ""), ("fijos_dia", "Costos fijos por día (USD)", 83, "money0", "2.500 por mes ÷ 30."),
              ("roas_obj", "ROAS objetivo sobre cash neto", 2.5, "ratio", "En llamada, 2,5 a 3 por la varianza."), CFG_COMUN[-1]],
    inputs=ADS_INPUTS + [("leads", "Leads", "int", "Los que dejaron sus datos."), ("aplicaciones", "Completan la aplicación", "int", ""), ("calificados", "Califican", "int", ""),
            ("agendas", "Agendan la llamada", "int", ""), ("llamadas", "Llamadas realizadas (show)", "int", "Las que ocurren, no las agendadas."),
            ("ventas", "Compran el programa", "int", ""), ("downsell", "Toman el downsell", "int", ""),
            ("cash_cobrado", "Cash cobrado ese día (USD)", "money0", "Lo que entró de verdad (anticipos, cuotas). Si lo dejás vacío se estima con el % del primer mes de Config.")],
    calc=ADS_CALC + [("conv_landing", "% visita → lead (conversión de la página)", "{leads}/{visitas}", "pct", "mayor"), ("cpl", "CPL (costo por lead)", "{inversion}/{leads}", "money", "menor"),
            ("cpl_cpm", "CPL como % del CPM (el umbral depende del nicho)", "{cpl}/{cpm}", "pct", "menor"), ("leads_mil", "Leads por cada 1.000 impresiones", "{leads}/{impresiones}*1000", "num1", "mayor"),
            ("pct_aplic", "% lead → aplicación", "{aplicaciones}/{leads}", "pct", "mayor"), ("pct_calif", "% aplicación → calificado", "{calificados}/{aplicaciones}", "pct", "mayor"),
            ("pct_agenda", "% calificado → agenda", "{agendas}/{calificados}", "pct", "mayor"), ("costo_agenda", "Costo por agenda", "{inversion}/{agendas}", "money", "menor"),
            ("show", "% agenda → llamada (show)", "{llamadas}/{agendas}", "pct", "mayor"), ("cierre", "% llamada → venta (cierre)", "{ventas}/{llamadas}", "pct", "mayor"),
            ("conv_lead_venta", "% lead → venta", "{ventas}/{leads}", "pct2", "mayor"), ("cac", "CAC (costo por venta)", "{inversion}/{ventas}", "money", "menor"),
            ("facturado", "Facturado a precio de lista", "{ventas}*{cfg:ticket}+{downsell}*{cfg:p_ds}", "money0", "mayor"),
            ("cash_base", "Cash cobrado (real, o estimado con el % del primer mes)", "IF({cash_cobrado}>0,{cash_cobrado},{facturado}*{cfg:cobro_m1})", "money0", "mayor"),
            ("cash_neto", "Cash neto (después de comisiones, closers y reembolsos)", "{cash_base}*(1-{cfg:pasarela}-{cfg:closers}-{cfg:reembolsos})", "money0", "mayor"),
            ("ganancia", "Ganancia de caja (cash neto − pauta − fijos)", "{cash_neto}-{inversion}-{fijos_periodo}", "money0", "mayor"),
            ("roas", "ROAS sobre cash neto", "{cash_neto}/{inversion}", "ratio", "mayor"), ("roas_fact", "ROAS sobre facturado (no decidas con este)", "{facturado}/{inversion}", "ratio", "mayor"),
            ("gan_visita", "Ganancia por visita (la métrica más valiosa)", "{ganancia}/{visitas}", "money", "mayor"),
            ("margen_visita", "Margen por visita (ganancia por visita ÷ costo por visita)", "{gan_visita}/{costo_visita}", "ratio", "mayor"),
            ("gan_unidad", "Ganancia por lead", "{ganancia}/{leads}", "money", "mayor")],
    grupos=[("1. Anuncios", ["inversion", "impresiones", "alcance", "clics_enlace", "visitas", "cpm", "frecuencia", "ctr", "cpc", "clic_visita", "costo_visita", "visitas_mil"]),
            ("2. Página y leads", ["leads", "conv_landing", "cpl", "cpl_cpm", "leads_mil"]),
            ("3. Aplicación, agenda y llamada", ["aplicaciones", "calificados", "agendas", "llamadas", "pct_aplic", "pct_calif", "pct_agenda", "costo_agenda", "show"]),
            ("4. Ventas y cobranza", ["ventas", "downsell", "cierre", "conv_lead_venta", "cac", "facturado", "cash_cobrado", "cash_base"]),
            ("5. Resultado", ["cash_neto", "ganancia", "roas", "roas_fact", "gan_visita", "margen_visita", "gan_unidad"])],
    clave=["gan_visita", "costo_visita", "cpl", "cpl_cpm", "conv_landing", "cpm", "ctr", "frecuencia", "pct_aplic", "costo_agenda", "show", "cierre", "roas"],
    resumen=["inversion", "visitas", "costo_visita", "leads", "cpl", "cpl_cpm", "conv_landing", "aplicaciones", "agendas", "costo_agenda", "llamadas", "show", "ventas", "cierre", "cac", "facturado", "cash_base", "cash_neto", "ganancia", "gan_visita", "roas", "cpm", "ctr"],
    norte="Costo por agenda contra lo que vale una agenda, y el cierre juzgado con 3 o 4 eventos, nunca con uno. Cash cobrado, no facturado."),
 "webinar_pago": dict(
    archivo="04_Metricas_Diarias_Embudo_Webinar_Pago.xlsx", titulo="Métricas diarias · Embudo de webinar pago",
    unidad=("entrada", "entradas"), unidad_key="entradas",
    config=[("p_entrada", "Precio promedio de la entrada", 9, "money", "Si es escalonado, el promedio cobrado."), ("p_bump_e", "Precio del bump de la entrada", 27, "money", ""),
            ("p_oferta", "Precio de la oferta del evento", 497, "money", ""), ("p_backend", "Precio del programa superior", 1997, "money", "")]
           + [("pasarela", "Comisión de la pasarela de pago", 0.08, "pct", ""), CFG_COMUN[1], CFG_COMUN[2], ("fijos_dia", "Costos fijos por día (USD)", 115, "money0", "800 por semana ÷ 7."), CFG_COMUN[4], CFG_COMUN[5]],
    inputs=ADS_INPUTS + [("entradas", "Compran la entrada", "int", "Tus leads: ya son compradores."), ("bump_entrada", "Toman el bump de la entrada", "int", ""),
            ("grupo", "Entran al grupo de WhatsApp", "int", ""), ("en_vivo", "Asistentes en vivo", "int", ""), ("replay", "Ven el replay", "int", ""),
            ("solicitudes", "Solicitudes (formulario de compra, aplicación o vendedor)", "int", ""), ("ventas_front", "Compran la oferta", "int", ""), ("backend", "Pasan al programa superior", "int", "")],
    calc=ADS_CALC + [("conv_entrada", "% visita → entrada (conversión de la página)", "{entradas}/{visitas}", "pct2", "mayor"), ("costo_entrada", "Costo por entrada", "{inversion}/{entradas}", "money", "menor"),
            ("entrada_cpm", "Costo por entrada en veces el CPM", "{costo_entrada}/{cpm}", "ratio", "menor"),
            ("fact_front", "Facturado del front (entradas + bump)", "{entradas}*{cfg:p_entrada}+{bump_entrada}*{cfg:p_bump_e}", "money0", "mayor"),
            ("roas_front", "ROAS del front (qué parte de la pauta recupera la entrada)", "{fact_front}/{inversion}", "ratio", "mayor"),
            ("pct_grupo", "% entrada → grupo", "{grupo}/{entradas}", "pct", "mayor"), ("pct_vivo", "% entrada → en vivo", "{en_vivo}/{entradas}", "pct", "mayor"),
            ("pct_replay", "% entrada → replay", "{replay}/{entradas}", "pct", "mayor"), ("costo_asistente", "Costo por asistente en vivo", "{inversion}/{en_vivo}", "money", "menor"),
            ("pct_solic", "% en vivo → solicitud", "{solicitudes}/{en_vivo}", "pct", "mayor"), ("cierre", "% solicitud → compra", "{ventas_front}/{solicitudes}", "pct", "mayor"),
            ("cpa", "CPA (costo por comprador de la oferta)", "{inversion}/{ventas_front}", "money", "menor"), ("pct_backend", "% pasan al programa", "{backend}/{ventas_front}", "pct", "mayor"),
            ("facturado", "Facturado total", "{fact_front}+{ventas_front}*{cfg:p_oferta}+{backend}*{cfg:p_backend}", "money0", "mayor")] + RESULTADO("entradas", "entrada"),
    grupos=[("1. Anuncios", ["inversion", "impresiones", "alcance", "clics_enlace", "visitas", "cpm", "frecuencia", "ctr", "cpc", "clic_visita", "costo_visita", "visitas_mil"]),
            ("2. Entradas (el front)", ["entradas", "bump_entrada", "conv_entrada", "costo_entrada", "entrada_cpm", "fact_front", "roas_front"]),
            ("3. Grupo y evento", ["grupo", "en_vivo", "replay", "pct_grupo", "pct_vivo", "pct_replay", "costo_asistente"]),
            ("4. Oferta y ventas", ["solicitudes", "ventas_front", "backend", "pct_solic", "cierre", "cpa", "pct_backend"]),
            ("5. Resultado", ["facturado", "cash_neto", "ganancia", "roas", "gan_visita", "margen_visita", "gan_unidad"])],
    clave=["gan_visita", "costo_visita", "costo_entrada", "conv_entrada", "roas_front", "cpm", "ctr", "frecuencia", "pct_vivo", "pct_solic", "cierre", "roas"],
    resumen=["inversion", "visitas", "costo_visita", "entradas", "costo_entrada", "conv_entrada", "roas_front", "en_vivo", "pct_vivo", "solicitudes", "pct_solic", "ventas_front", "cierre", "facturado", "cash_neto", "ganancia", "gan_visita", "roas", "cpm", "ctr"],
    norte="Primero el ROAS del front (cerca de 1, el evento se paga solo); después la oferta."),
}

# ------------------------------------------------------------ datos de ejemplo (4 semanas, con ruido)
def ejemplo(e, dias):
    rnd = random.Random(11); filas = []
    def n(x, s=0.12): return x * (1 + rnd.uniform(-s, s))
    def ri(x): return int(round(max(0, x)))
    for i in range(dias):
        if i >= 28: filas.append({}); continue
        d = {}; dow = i % 7
        if e == "low_ticket":
            inv = n(300); imp = inv / n(4.2) * 1000; alc = imp / n(1.6); clk = imp * n(0.0155); vis = clk * n(0.90)
            ck = vis * n(0.035); v = ck * n(0.26)
            d.update(inversion=round(inv), impresiones=ri(imp), alcance=ri(alc), clics_enlace=ri(clk), visitas=ri(vis), checkouts=ri(ck), ventas_front=ri(v),
                     bump1=ri(v * 0.25), bump2=ri(v * 0.18), oto1=ri(v * 0.10), oto2=ri(v * 0.06), oto3=ri(v * 0.03), oto4=ri(v * 0.04), ascension=ri(v * 0.02))
        elif e == "webinar_gratuito":
            inv = n(857); imp = inv / n(4.5) * 1000; alc = imp / n(1.5); clk = imp * n(0.022); vis = clk * n(0.90); reg = vis * n(0.23)
            d.update(inversion=round(inv), impresiones=ri(imp), alcance=ri(alc), clics_enlace=ri(clk), visitas=ri(vis), registros=ri(reg), registros_calif=ri(reg * 0.60), grupo=ri(reg * 0.67))
            sem_reg = 6000 * n(1.0, 0.06)  # registros de la semana (el webinar es el jueves)
            if dow == 3:
                av = sem_reg * n(0.15, 0.08); so = av * n(0.10, 0.1); d.update(en_vivo=ri(av), replay=ri(sem_reg * 0.20), solicitudes=ri(so), ventas_front=ri(so * 0.40))
            elif dow == 4:
                so = sem_reg * 0.25 * n(0.06, 0.15); d.update(replay=ri(sem_reg * 0.25), solicitudes=ri(so), ventas_front=ri(so * 0.40))
            elif dow == 5:
                so = sem_reg * 0.10 * n(0.055, 0.15); d.update(replay=ri(sem_reg * 0.10), solicitudes=ri(so), ventas_front=ri(so * 0.40))
            vf = d.get("ventas_front")
            if vf is not None: d.update(bump=ri(vf * 0.20), backend=(ri(vf * 0.05) if dow in (4, 5) else 0))
        elif e == "llamada":
            inv = n(150); imp = inv / n(10) * 1000; alc = imp / n(1.4); clk = imp * n(0.015); vis = clk * n(0.85); ld = vis * n(0.28)
            ap = ld * n(0.10, 0.3); ca = ap * 0.6; ag = ca * 0.6; ll = ag * 0.7
            vt = 1 if rnd.random() < 0.34 else 0; ds = 1 if (vt == 0 and rnd.random() < 0.10) else 0
            d.update(inversion=round(inv), impresiones=ri(imp), alcance=ri(alc), clics_enlace=ri(clk), visitas=ri(vis), leads=ri(ld), aplicaciones=ri(ap), calificados=ri(ca),
                     agendas=ri(ag), llamadas=ri(ll), ventas=vt, downsell=ds, cash_cobrado=round(vt * 1500 * 0.6 + ds * 497 + (300 if rnd.random() < 0.3 else 0)))
        else:
            inv = n(430); imp = inv / n(5) * 1000; alc = imp / n(1.5); clk = imp * n(0.02); vis = clk * n(0.88); en = vis * n(0.025)
            d.update(inversion=round(inv), impresiones=ri(imp), alcance=ri(alc), clics_enlace=ri(clk), visitas=ri(vis), entradas=ri(en), bump_entrada=ri(en * 0.20), grupo=ri(en * 0.85))
            sem_en = 214 * n(1.0, 0.06)
            if dow == 3:
                av = sem_en * n(0.55, 0.08); so = av * n(0.16, 0.1); d.update(en_vivo=ri(av), replay=ri(sem_en * 0.10), solicitudes=ri(so), ventas_front=ri(so * 0.5), backend=1)
            elif dow == 4:
                d.update(replay=ri(sem_en * 0.15), solicitudes=ri(2), ventas_front=ri(1), backend=0)
        filas.append(d)
    return filas

# ------------------------------------------------------------ construcción
KEY_RE = re.compile(r"\{([\w:]+)\}")

class Libro:
    def __init__(self, e, spec, dias):
        self.e, self.s, self.dias = e, spec, dias
        self.wb = openpyxl.Workbook(); self.wb.remove(self.wb.active)
        self.cfg_row = {}; self.dcol = {}; self.drow0 = 6; self.drow1 = 6 + dias - 1
        self.wrow = {}; self.wmed = {}; self.wsem = {}
        self.dir = {k: d for (k, _, _, _, d) in spec["calc"]}
        self.label = {k: lab for (k, lab, *_r) in spec["inputs"]}; self.label.update({k: lab for (k, lab, _, _, _) in spec["calc"]})
        self.fmt = {k: f for (k, _, f, _) in spec["inputs"]}; self.fmt.update({k: f for (k, _, _, f, _) in spec["calc"]})

    # --- estilos
    def put(self, ws, r, c, value, fmt=None, kind=None, bold=False, wrap=False):
        cell = ws.cell(r, c, value)
        if fmt: cell.number_format = FMT[fmt]
        if kind == "in": cell.fill = FILL_IN
        elif kind == "out": cell.fill = FILL_OUT
        if kind: cell.border = BORDER
        if bold: cell.font = FONT_B
        if wrap: cell.alignment = WRAP
        return cell

    def header(self, ws, r, cols, start=1):
        for j, t in enumerate(cols):
            c = ws.cell(r, start + j, t); c.fill = FILL_HDR; c.font = FONT_HDR; c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center"); c.border = BORDER

    def seccion(self, ws, r, text, ncols):
        c = ws.cell(r, 1, text); c.font = FONT_B; c.fill = FILL_SEC
        for j in range(2, ncols + 1): ws.cell(r, j).fill = FILL_SEC

    def pie(self, ws, r):
        ws.cell(r, 1, MARCA + " · " + VERSION).font = FONT_NOTE

    def cfg(self, key): return f"Config!$C${self.cfg_row[key]}"

    def render(self, tpl, ref):
        return KEY_RE.sub(lambda m: self.cfg(m.group(1)[4:]) if m.group(1).startswith("cfg:") else ref(m.group(1)), tpl)

    # --- hojas
    def build_config(self):
        ws = self.wb.create_sheet("Config"); ws.column_dimensions["A"].width = 3; ws.column_dimensions["B"].width = 58; ws.column_dimensions["C"].width = 16; ws.column_dimensions["D"].width = 70
        ws.cell(2, 2, "Config: tus precios, comisiones y la fecha de inicio").font = FONT_TITLE
        ws.cell(3, 2, "Amarillo = podés cambiarlo. Todo lo demás del libro se calcula con esto.").font = FONT_NOTE
        self.header(ws, 5, ["", "Dato", "Valor", "Nota"])
        r = 6
        self.put(ws, r, 2, "Fecha de inicio del registro (un lunes)"); c = self.put(ws, r, 3, INICIO, "fecha", "in"); self.put(ws, r, 4, "Desde este día se numeran las semanas en Diario y Semanal. Elegí un lunes.", wrap=True)
        self.cfg_row["inicio"] = r; r += 1
        for key, lab, val, fmt, nota in self.s["config"]:
            self.put(ws, r, 2, lab); self.put(ws, r, 3, val, fmt, "in"); self.put(ws, r, 4, nota, wrap=True); self.cfg_row[key] = r; r += 1
        self.pie(ws, r + 2)

    def build_diario(self):
        s = self.s; ws = self.wb.create_sheet("Diario")
        ins, calc = s["inputs"], s["calc"]
        ws.cell(2, 1, "Diario: una fila por día. Amarillo = lo que cargás; azul = lo que calcula el libro").font = FONT_TITLE
        ws.cell(3, 1, "Cargá cada día lo que hubo (vacío si no hubo). Los porcentajes de un solo día pueden ser raros en embudos con evento semanal: la lectura buena está en Semanal.").font = FONT_NOTE
        cols = ["Fecha", "Semana"] + [lab for (_, lab, _, _) in ins] + [lab for (_, lab, _, _, _) in calc]
        self.header(ws, 5, cols)
        self.dcol["fecha"] = "A"; self.dcol["semana"] = "B"
        c = 3
        for key, *_ in ins: self.dcol[key] = col(c); c += 1
        first_in, last_in = col(3), col(2 + len(ins))
        for key, *_ in calc: self.dcol[key] = col(c); c += 1
        ncols = c - 1
        datos = ejemplo(self.e, self.dias)
        for i in range(self.dias):
            r = self.drow0 + i
            self.put(ws, r, 1, f"={self.cfg('inicio')}+{i}", "fecha", "out")
            self.put(ws, r, 2, f"=INT((A{r}-{self.cfg('inicio')})/7)+1", "int", "out")
            for key, lab, fmt, nota in ins:
                v = datos[i].get(key) if i < len(datos) else None
                self.put(ws, r, openpyxl.utils.column_index_from_string(self.dcol[key]), v, fmt, "in")
            ref = lambda k, r=r: (self.cfg("fijos_dia") if k == "fijos_periodo" else f"{self.dcol[k]}{r}")
            for key, lab, tpl, fmt, d in calc:
                f = f'=IF(COUNT({first_in}{r}:{last_in}{r})=0,"",IFERROR({self.render(tpl, ref)},0))'
                self.put(ws, r, openpyxl.utils.column_index_from_string(self.dcol[key]), f, fmt, "out")
        ws.freeze_panes = "C6"; ws.column_dimensions["A"].width = 12; ws.column_dimensions["B"].width = 8
        for j in range(3, ncols + 1): ws.column_dimensions[col(j)].width = 14
        ws.row_dimensions[5].height = 60
        self.pie(ws, self.drow1 + 3)

    def build_semanal(self):
        s = self.s; ws = self.wb.create_sheet("Semanal"); W = SEMANAS; c0 = 3; c1 = c0 + W - 1
        cP, cM, cB, cW = c1 + 1, c1 + 2, c1 + 3, c1 + 4
        ws.cell(2, 1, "Semanal: el comparativo semana a semana, calculado solo desde Diario").font = FONT_TITLE
        ws.cell(3, 1, "Promedio, mediana, mejor y peor de tus semanas con datos. Abajo, el bloque «contra tu promedio»: cada semana contra la mediana de tus 4 semanas anteriores, con la tolerancia de Config. Ese es el umbral: tu promedio, no un número de mercado.").font = FONT_NOTE
        self.put(ws, 4, 2, "Lunes de la semana", bold=True)
        for k in range(W):
            self.put(ws, 4, c0 + k, f"={self.cfg('inicio')}+{k * 7}", "fecha", "out")
        self.header(ws, 5, ["Categoría", "Métrica"] + [f"SEM {k + 1}" for k in range(W)] + ["Promedio", "Mediana", "Mejor", "Peor"])
        for k in range(W): ws.cell(5, c0 + k, k + 1).number_format = '"SEM "0'
        ins_keys = {k for (k, *_) in s["inputs"]}; calc = {k: (lab, tpl, fmt, d) for (k, lab, tpl, fmt, d) in s["calc"]}
        D0, D1 = self.drow0, self.drow1
        rng = lambda key: f"Diario!${self.dcol[key]}${D0}:${self.dcol[key]}${D1}"
        semrng = f"Diario!$B${D0}:$B${D1}"
        r = 6
        # fila auxiliar: semana con datos
        self.row_activa = r
        self.put(ws, r, 1, "Semana con datos (1 = sí)"); 
        for k in range(W):
            cc = col(c0 + k)
            self.put(ws, r, c0 + k, f"=IF(SUMIFS({rng('inversion')},{semrng},{cc}$5)+SUMIFS({rng(s['unidad_key'])},{semrng},{cc}$5)>0,1,0)", "int", "out")
        r += 1
        self.row_numsem = r; self.put(ws, r, 1, "Número de semana si tiene datos")
        for k in range(W):
            cc = col(c0 + k); self.put(ws, r, c0 + k, f"=IF({cc}{self.row_activa}=1,{cc}$5,0)", "int", "out")
        r += 2
        # primero las filas de todas las claves (las fórmulas semanales se referencian entre sí sin importar el orden)
        rr0 = r
        for titulo, keys in s["grupos"]:
            rr0 += 1
            for key in keys: self.wrow[key] = rr0; rr0 += 1
            rr0 += 1
        for titulo, keys in s["grupos"]:
            self.seccion(ws, r, titulo, cW); r += 1
            for key in keys:
                assert self.wrow[key] == r; lab = self.label[key]; fmt = self.fmt[key]
                self.put(ws, r, 1, titulo.split(". ", 1)[1] if ". " in titulo else titulo); self.put(ws, r, 2, lab, bold=key in s["clave"], wrap=True)
                for k in range(W):
                    cc = col(c0 + k)
                    if key in ins_keys:
                        f = f'=IF({cc}{self.row_activa}=0,"",SUMIFS({rng(key)},{semrng},{cc}$5))'
                    else:
                        tpl = calc[key][1]
                        ref = lambda kk, cc=cc: (f"{self.cfg('fijos_dia')}*7" if kk == "fijos_periodo" else f"{cc}{self.wrow[kk]}")
                        f = f'=IF({cc}{self.row_activa}=0,"",IFERROR({self.render(tpl, ref)},0))'
                    self.put(ws, r, c0 + k, f, fmt, "out")
                rr = f"{col(c0)}{r}:{col(c1)}{r}"; d = self.dir.get(key, "mayor")
                self.put(ws, r, cP, f'=IFERROR(AVERAGE({rr}),"")', fmt, "out"); self.put(ws, r, cM, f'=IFERROR(MEDIAN({rr}),"")', fmt, "out")
                self.put(ws, r, cB, f'=IFERROR({"MIN" if d == "menor" else "MAX"}({rr}),"")', fmt, "out"); self.put(ws, r, cW, f'=IFERROR({"MAX" if d == "menor" else "MIN"}({rr}),"")', fmt, "out")
                r += 1
            r += 1
        # bloque contra tu promedio
        self.seccion(ws, r, "6. Contra tu promedio: cada semana contra la mediana de tus 4 semanas anteriores (tolerancia en Config). Igual o mejor = VERDE · hasta la tolerancia peor = AMARILLO · más = ROJO", cW); r += 1
        tol = self.cfg("tolerancia")
        for key in s["clave"]:
            rv = self.wrow[key]; d = self.dir.get(key, "mayor")
            self.wmed[key] = r; self.put(ws, r, 1, "Mediana 4 semanas anteriores"); self.put(ws, r, 2, self.label[key], wrap=True)
            for k in range(W):
                if k == 0: self.put(ws, r, c0 + k, "", None, "out"); continue
                a, b = col(c0 + max(0, k - 4)), col(c0 + k - 1)
                self.put(ws, r, c0 + k, f'=IFERROR(MEDIAN({a}{rv}:{b}{rv}),"")', self.fmt[key], "out")
            r += 1
            self.wsem[key] = r; self.put(ws, r, 1, "Semáforo"); self.put(ws, r, 2, self.label[key], bold=True, wrap=True)
            for k in range(W):
                cc = col(c0 + k); v, m = f"{cc}{rv}", f"{cc}{self.wmed[key]}"
                if d == "menor": core = f'IF({v}<={m},"VERDE",IF({v}<={m}*(1+{tol}),"AMARILLO","ROJO"))'
                else: core = f'IF({v}>={m},"VERDE",IF({v}>={m}*(1-{tol}),"AMARILLO","ROJO"))'
                if key == "gan_visita": core = f'IF({v}<=0,"ROJO",{core})'
                if key == "roas": core = f'IF({v}<=1,"ROJO",{core})'
                self.put(ws, r, c0 + k, f'=IF(OR({v}="",{m}=""),"",{core})', "txt", "out", bold=True)
            self.semaforo_cf(ws, f"{col(c0)}{r}:{col(c1)}{r}"); r += 1
        self.pie(ws, r + 1)
        ws.freeze_panes = "C6"; ws.column_dimensions["A"].width = 24; ws.column_dimensions["B"].width = 44
        for j in range(c0, cW + 1): ws.column_dimensions[col(j)].width = 12
        ws.row_dimensions[5].height = 30
        self.W, self.c0, self.c1, self.cB = W, c0, c1, cB

    def semaforo_cf(self, ws, rng):
        ws.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=['"VERDE"'], fill=FILL_OK))
        ws.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=['"AMARILLO"'], fill=FILL_WARN))
        ws.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=['"ROJO"'], fill=FILL_BAD))

    def build_resumen(self):
        s = self.s; ws = self.wb.create_sheet("Resumen", 0 if False else None)
        ws.cell(2, 1, "Resumen: la semana elegida contra la anterior, contra tu mediana y contra tu meta").font = FONT_TITLE
        ws.cell(3, 1, "Las filas están en el orden en que miro un embudo. El semáforo compara con la mediana de tus 4 semanas anteriores, con la tolerancia de Config.").font = FONT_NOTE
        self.put(ws, 4, 1, "Semana a mostrar", bold=True)
        c0, c1 = self.c0, self.c1
        self.put(ws, 4, 2, f"=MAX(Semanal!${col(c0)}${self.row_numsem}:${col(c1)}${self.row_numsem})", "int", "in")
        ws.cell(4, 3, "← la última con datos; escribí otro número para ver otra semana").font = FONT_NOTE
        self.header(ws, 6, ["KPI", "Esta semana", "Semana anterior", "Variación", "Mediana 4 semanas previas", "Semáforo contra tu promedio", "Mejor semana", "Meta (tu objetivo)"])
        r = 7
        for key in s["resumen"]:
            rv = self.wrow[key]; fmt = self.fmt[key]; fila = f"Semanal!${col(c0)}${rv}:${col(c1)}${rv}"
            self.put(ws, r, 1, self.label[key], bold=key in s["clave"], wrap=True)
            self.put(ws, r, 2, f'=IFERROR(INDEX({fila},1,$B$4),"")', fmt, "out", bold=True)
            self.put(ws, r, 3, f'=IF($B$4<=1,"",IFERROR(INDEX({fila},1,$B$4-1),""))', fmt, "out")
            self.put(ws, r, 4, f'=IFERROR(IF(OR(B{r}="",C{r}=""),"",(B{r}-C{r})/C{r}),"")', "pct", "out")
            if key in s["clave"]:
                fm = f"Semanal!${col(c0)}${self.wmed[key]}:${col(c1)}${self.wmed[key]}"; fs = f"Semanal!${col(c0)}${self.wsem[key]}:${col(c1)}${self.wsem[key]}"
                self.put(ws, r, 5, f'=IFERROR(INDEX({fm},1,$B$4),"")', fmt, "out"); self.put(ws, r, 6, f'=IFERROR(INDEX({fs},1,$B$4),"")', "txt", "out", bold=True)
            else:
                self.put(ws, r, 5, "", None, "out"); self.put(ws, r, 6, "", None, "out")
            self.put(ws, r, 7, f"=Semanal!${col(self.cB)}${rv}", fmt, "out"); self.put(ws, r, 8, None, fmt, "in")
            r += 1
        self.semaforo_cf(ws, f"F7:F{r - 1}")
        r += 1
        self.put(ws, r, 1, "Cómo se lee", bold=True); r += 1
        for t in ["Se mira de arriba hacia abajo y se para en el primer rojo: un rojo arriba (costo por visita, CPL) arrastra todo lo de abajo.",
                  "La ganancia por visita resume todo lo que pasa después de la página: si está en rojo con el costo por visita en verde, el problema no es el tráfico.",
                  "El CPL se lee también como % del CPM: el umbral de costo depende del nicho. Con CPM de 3 un CPL de 1 y con CPM de 25 un CPL de 10 son el mismo embudo.",
                  "Una decisión por semana, anotada, y a los 7 días mirar qué pasó. Nunca por un día. En llamada, 3 o 4 eventos.",
                  "La fila de la semana se copia a la hoja Seguimiento del modelo financiero de este embudo: ahí está el techo (hasta cuánto pagar) y el guardarraíl para subir o bajar."]:
            ws.cell(r, 1, "• " + t).alignment = Alignment(wrap_text=True, vertical="top"); ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=8); ws.row_dimensions[r].height = 30; r += 1
        self.pie(ws, r + 1)
        ws.column_dimensions["A"].width = 46
        for j, w in zip("BCDEFGH", [14, 14, 11, 16, 18, 13, 14]): ws.column_dimensions[j].width = w
        ws.row_dimensions[6].height = 44

    def build_inicio(self):
        s = self.s; ws = self.wb.create_sheet("Inicio", 0); ws.column_dimensions["A"].width = 3; ws.column_dimensions["B"].width = 120
        ws.cell(2, 2, s["titulo"]).font = FONT_TITLE
        ws.cell(3, 2, "Las métricas diarias de todo el embudo, para saber cómo estás con tus propios números. Acompaña al modelo financiero del mismo embudo.").font = FONT_NOTE
        lineas = [
            ("Qué es", "Un registro diario de cada paso del embudo (anuncios, página, unidades, etapas, ventas, cash) que se convierte solo en un comparativo semanal y en un resumen con semáforo. El semáforo no usa números de mercado: compara cada semana con la mediana de tus 4 semanas anteriores, con una tolerancia del 25 % (la cambiás en Config)."),
            ("1. Config", "Poné tus precios, comisiones, reembolsos, costos fijos por día y la fecha de inicio (un lunes). Todo lo demás se calcula con eso."),
            ("2. Diario (todos los días, 3 minutos)", "Una fila por día. Cargá las celdas amarillas con lo que hubo: inversión, impresiones, alcance, clics en el enlace, visitas y cada paso del embudo. Si un día no hubo evento, dejá vacío. Las celdas azules se calculan solas (CPM, CTR, costo por visita, CPL, conversiones, facturado, cash neto, ganancia, ROAS y la ganancia por visita)."),
            ("3. Semanal (los lunes, 10 minutos)", "No se carga nada: suma Diario por semana y calcula las conversiones y los costos de la semana, el promedio, la mediana, la mejor y la peor. Abajo, el bloque «contra tu promedio» marca en verde, amarillo o rojo cada métrica clave contra la mediana de tus 4 semanas anteriores."),
            ("4. Resumen", "La semana elegida (por defecto la última con datos) contra la anterior, contra tu mediana y contra la meta que vos escribas. Las filas van en el orden en que se mira un embudo: primero el tráfico y la ganancia por visita, después la página, después las etapas, después las ventas y la caja."),
            ("5. Decidir", "Una sola decisión por semana y a los 7 días mirar qué pasó. Se para en el primer rojo de arriba hacia abajo. Nunca se decide por un día, y en llamada se juzga con 3 o 4 eventos."),
            ("6. Conectar con el modelo financiero", "Copiá la fila semanal (inversión, cantidades por paso, ventas, facturado, cash cobrado) en la hoja Seguimiento del modelo financiero de este embudo: ahí está el techo (hasta cuánto pagar por cada unidad), el objetivo y el guardarraíl para subir o bajar la inversión."),
            ("Lo que manda en este embudo", s["norte"]),
            ("Regla de los umbrales", "Tu promedio es el umbral: igual o mejor, verde; hasta 25 % peor, amarillo; más, rojo. Y los costos dependen del nicho: el CPL se lee también como porcentaje del CPM. Los primeros 28 días del ejemplo están cargados para que veas cómo funciona: borralos y cargá los tuyos."),
            ("Compatibilidad", "Funciona en Excel, Google Sheets y Numbers (solo funciones básicas). Si lo subís a Drive, abrilo con Google Sheets: las fórmulas se conservan."),
        ]
        r = 5
        for t, body in lineas:
            ws.cell(r, 2, t).font = FONT_B; r += 1
            c = ws.cell(r, 2, body); c.alignment = Alignment(wrap_text=True, vertical="top"); ws.row_dimensions[r].height = 15 * (1 + len(body) // 115); r += 2
        ws.cell(r, 2, "Autor y versión").font = FONT_B; ws.cell(r + 1, 2, MARCA + " · " + VERSION).font = FONT_NOTE

    def build(self, out_dir):
        self.build_config(); self.build_diario(); self.build_semanal(); self.build_resumen(); self.build_inicio()
        self.wb.properties.creator = "Jesús Tassarolo · TooAudience"; self.wb.properties.title = self.s["titulo"]; self.wb.properties.description = MARCA
        os.makedirs(out_dir, exist_ok=True); path = os.path.join(out_dir, self.s["archivo"]); self.wb.save(path); return path


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("salida", nargs="?", default=DEFAULT_OUT); ap.add_argument("--dias", type=int, default=366)
    ap.add_argument("--solo", help="generar un solo embudo (clave de SPECS)")
    a = ap.parse_args()
    for e, spec in SPECS.items():
        if a.solo and e != a.solo: continue
        p = Libro(e, spec, a.dias).build(a.salida); print("OK", p)


if __name__ == "__main__":
    main()
