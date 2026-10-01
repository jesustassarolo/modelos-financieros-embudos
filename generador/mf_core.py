#!/usr/bin/env python3
"""Núcleo del generador de modelos financieros de embudos (Excel / Google Sheets).

Una especificación (ver mf_specs.py) describe un embudo: supuestos, cadena de cálculo,
tablas de escenarios, palancas, proyección, seguimiento, benchmarks y textos. Este módulo
la convierte en un libro .xlsx con fórmulas vivas, compatible con Google Sheets.

Convención de colores (la de TooAudience): amarillo = entrada editable, azul = resultado.
Fórmulas: solo funciones básicas (IF, SUM, MIN, MAX, MEDIAN, COUNT, ABS, RANK) para que
funcionen igual en Excel, Google Sheets y Numbers.
"""
import re
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import CellIsRule, FormulaRule

FILL_IN = PatternFill("solid", fgColor="FFF2CC")
FILL_OUT = PatternFill("solid", fgColor="DDEBF7")
FILL_HDR = PatternFill("solid", fgColor="1F3864")
FILL_SEC = PatternFill("solid", fgColor="D9E1F2")
FILL_OK = PatternFill("solid", fgColor="C6EFCE")
FILL_WARN = PatternFill("solid", fgColor="FFEB9C")
FILL_BAD = PatternFill("solid", fgColor="FFC7CE")
FONT_HDR = Font(bold=True, color="FFFFFF")
FONT_B = Font(bold=True)
FONT_TITLE = Font(bold=True, size=14)
FONT_NOTE = Font(italic=True, color="595959")
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical="top")
CENTER = Alignment(horizontal="center", vertical="center")
FMT = {"money": '"$"#,##0.00', "money0": '"$"#,##0', "pct": "0.0%", "pct2": "0.00%",
       "int": "#,##0", "ratio": '0.00"x"', "num": "0.00", "txt": "@", "num1": "0.0"}
MESES = ["Mes 1", "Mes 2", "Mes 3", "Mes 4", "Mes 5", "Mes 6", "Mes 7", "Mes 8", "Mes 9", "Mes 10", "Mes 11", "Mes 12"]
KEY_RE = re.compile(r"\{(\w+)\}")

DIV_PATTERNS = [
    (re.compile(r"^\{(\w+)\}/\{(\w+)\}$"), lambda m: f"IF({{{m.group(2)}}}=0,0,{{{m.group(1)}}}/{{{m.group(2)}}})"),
    (re.compile(r"^\(\{(\w+)\}-\{(\w+)\}\)/\{(\w+)\}$"), lambda m: f"IF({{{m.group(3)}}}=0,0,({{{m.group(1)}}}-{{{m.group(2)}}})/{{{m.group(3)}}})"),
    (re.compile(r"^\{(\w+)\}\*\{(\w+)\}/\{(\w+)\}$"), lambda m: f"IF({{{m.group(3)}}}=0,0,{{{m.group(1)}}}*{{{m.group(2)}}}/{{{m.group(3)}}})"),
    (re.compile(r"^\{(\w+)\}/\{(\w+)\}\*\{(\w+)\}$"), lambda m: f"IF({{{m.group(2)}}}=0,0,{{{m.group(1)}}}/{{{m.group(2)}}}*{{{m.group(3)}}})"),
]


def guard_div(tpl):
    """Envuelve divisiones simples en IF(denominador=0,0,...) para que un 0 en Supuestos no rompa el libro."""
    for pat, fn in DIV_PATTERNS:
        m = pat.match(tpl)
        if m:
            return fn(m)
    return tpl


def col(c):
    return get_column_letter(c)


def aref(sheet, c, r):
    return f"'{sheet}'!${col(c)}${r}"


class Builder:
    def __init__(self, spec):
        self.s = spec
        self.wb = openpyxl.Workbook()
        self.wb.remove(self.wb.active)
        self.ref = {}      # key -> referencia absoluta
        self.tpl = {}      # key de cálculo -> plantilla con {claves}
        self.base = set()  # claves de supuestos
        self.fmt = {}      # key -> formato
        self.label = {}    # key -> etiqueta

    # ---------- motor de expresiones ----------
    def expr(self, key, overrides=None, depth=0):
        """Expresión de `key` en función de los supuestos (con overrides por clave)."""
        overrides = overrides or {}
        if depth > 60:
            raise RecursionError(f"ciclo en {key}")
        if key in overrides:
            return overrides[key]
        if key in self.base:
            return self.ref[key]
        if key not in self.tpl:
            raise KeyError(f"clave desconocida: {key}")
        return "(" + KEY_RE.sub(lambda m: self.expr(m.group(1), overrides, depth + 1), self.tpl[key]) + ")"

    def formula(self, template, overrides=None):
        """Fórmula que referencia celdas ya escritas (sin inlinear), con overrides opcionales."""
        overrides = overrides or {}

        def rep(m):
            k = m.group(1)
            if k in overrides:
                return overrides[k]
            if k not in self.ref:
                raise KeyError(f"la clave {k} se usa antes de definirse")
            return self.ref[k]
        return "=" + KEY_RE.sub(rep, template)

    # ---------- utilidades de hoja ----------
    def sheet(self, name, widths):
        ws = self.wb.create_sheet(name)
        for i, w in enumerate(widths, start=1):
            ws.column_dimensions[col(i)].width = w
        ws.sheet_view.showGridLines = False
        # marca de agua: pie de página de impresión en cada hoja
        try:
            from mf_comun import MARCA
            ws.oddFooter.center.text = MARCA
            ws.oddFooter.center.size = 7
            ws.evenFooter.center.text = MARCA
            ws.evenFooter.center.size = 7
        except Exception:
            pass
        return ws

    def title(self, ws, r, text, sub=None):
        ws.cell(r, 2, text).font = FONT_TITLE
        if sub:
            ws.cell(r + 1, 2, sub).font = FONT_NOTE
        return r + (3 if sub else 2)

    def header(self, ws, r, cols, start=2):
        for i, t in enumerate(cols):
            c = ws.cell(r, start + i, t)
            c.fill, c.font, c.alignment, c.border = FILL_HDR, FONT_HDR, CENTER, BORDER
        return r + 1

    def section(self, ws, r, text, ncols=7, start=2):
        for i in range(ncols):
            c = ws.cell(r, start + i)
            c.fill = FILL_SEC
        ws.cell(r, start, text).font = FONT_B
        return r + 1

    def put(self, ws, r, c, value, fmt=None, kind=None, bold=False, wrap=False):
        cell = ws.cell(r, c, value)
        if fmt:
            cell.number_format = FMT[fmt]
        if kind == "in":
            cell.fill = FILL_IN
        elif kind == "out":
            cell.fill = FILL_OUT
        if bold:
            cell.font = FONT_B
        if wrap:
            cell.alignment = WRAP
        if kind:
            cell.border = BORDER
        return cell

    def semaforo_cf(self, ws, rng):
        ws.conditional_formatting.add(rng, FormulaRule(formula=[f'LEFT({rng.split(":")[0]},5)="VERDE"'], fill=FILL_OK))
        ws.conditional_formatting.add(rng, FormulaRule(formula=[f'LEFT({rng.split(":")[0]},8)="AMARILLO"'], fill=FILL_WARN))
        ws.conditional_formatting.add(rng, FormulaRule(formula=[f'LEFT({rng.split(":")[0]},4)="ROJO"'], fill=FILL_BAD))

    def profit_cf(self, ws, rng, umbral_ref):
        ws.conditional_formatting.add(rng, CellIsRule(operator="lessThan", formula=["0"], fill=FILL_BAD))
        ws.conditional_formatting.add(rng, CellIsRule(operator="between", formula=["0", umbral_ref], fill=FILL_WARN))
        ws.conditional_formatting.add(rng, CellIsRule(operator="greaterThanOrEqual", formula=[umbral_ref], fill=FILL_OK))

    # ---------- hojas ----------
    def build_inicio(self):
        ws = self.sheet("Inicio", [2, 118])
        r = self.title(ws, 2, self.s["titulo"], self.s.get("subtitulo"))
        for bloque in self.s["inicio"]:
            if isinstance(bloque, tuple):
                ws.cell(r, 2, bloque[0]).font = FONT_B
                r += 1
                for linea in bloque[1]:
                    c = ws.cell(r, 2, linea)
                    c.alignment = WRAP
                    ws.row_dimensions[r].height = max(15, 15 * (1 + len(linea) // 115))
                    r += 1
                r += 1
        return ws

    def build_supuestos(self):
        ws = self.sheet("Supuestos", [2, 58, 16, 14, 14, 14, 12, 70])
        r = self.title(ws, 2, "Supuestos", "Celdas amarillas = las editás vos. Celdas azules = se calculan solas. Cada fila dice en qué unidad va y de dónde sale el valor del ejemplo.")
        r = self.header(ws, r, ["Supuesto", "Valor en uso", "Conservador", "Base", "Optimista", "Unidad", "Nota / fuente del ejemplo"])
        # selector de escenario
        self.put(ws, r, 2, "Escenario en uso (1 = conservador · 2 = base · 3 = optimista)", bold=True)
        self.put(ws, r, 3, self.s.get("escenario_inicial", 2), "int", "in")
        self.put(ws, r, 7, "1 / 2 / 3")
        self.put(ws, r, 8, "Cambia todas las filas que tienen tres valores. Si una fila no tiene tres valores, se usa el de 'Valor en uso'.", wrap=True)
        self.ref["escenario"] = aref("Supuestos", 3, r)
        self.base.add("escenario")
        esc = self.ref["escenario"]
        r += 1
        for grupo in self.s["supuestos"]:
            r = self.section(ws, r, grupo["grupo"])
            for it in grupo["items"]:
                k, fmt = it["key"], it["fmt"]
                self.put(ws, r, 2, it["label"])
                if "esc" in it:
                    cons, base, opt = it["esc"]
                    self.put(ws, r, 4, cons, fmt, "in")
                    self.put(ws, r, 5, base, fmt, "in")
                    self.put(ws, r, 6, opt, fmt, "in")
                    self.put(ws, r, 3, f"=IF({esc}=1,D{r},IF({esc}=2,E{r},F{r}))", fmt, "out")
                else:
                    self.put(ws, r, 3, it["val"], fmt, "in")
                self.put(ws, r, 7, it.get("unidad", ""))
                self.put(ws, r, 8, it.get("nota", ""), wrap=True)
                self.ref[k] = aref("Supuestos", 3, r)
                self.base.add(k)
                self.fmt[k] = fmt
                self.label[k] = it["label"]
                r += 1
            r += 1
        ws.freeze_panes = "C5"
        return ws

    def build_modelo(self):
        ws = self.sheet("Modelo", [2, 60, 18, 72])
        r = self.title(ws, 2, "Modelo: la cadena completa del embudo", "Cada fila es una etapa o un resultado. No se edita: todo sale de Supuestos. La columna de la derecha dice cómo se calcula.")
        r = self.header(ws, r, ["Etapa / resultado", "Valor", "Cómo se calcula"])
        for it in self.s["calculo"]:
            if "seccion" in it:
                r = self.section(ws, r, it["seccion"], ncols=3)
                continue
            k = it["key"]
            self.tpl[k] = guard_div(it["f"])
            self.fmt[k] = it["fmt"]
            self.label[k] = it["label"]
            self.put(ws, r, 2, it["label"], bold=it.get("bold", False))
            self.put(ws, r, 3, self.formula(self.tpl[k]), it["fmt"], "out", bold=it.get("bold", False))
            self.put(ws, r, 4, it.get("como", ""), wrap=True)
            self.ref[k] = aref("Modelo", 3, r)
            r += 1
        # Las dos caras de cada número: costo por paso (ya está arriba) y ganancia por paso
        r = self.section(ws, r, "Ganancia por paso (las dos caras de cada número: costo por X y ganancia por X)", ncols=3)
        prof = self.ref["profit"]
        if "aov_neto" not in self.ref:
            self.put(ws, r, 2, "Cash neto por comprador (AOV neto)", bold=True)
            self.put(ws, r, 3, f"=IF({self.ref['ventas_front']}=0,0,({self.ref['neto']}-{self.ref['semivar']})/{self.ref['ventas_front']})", "money", "out", bold=True)
            self.put(ws, r, 4, "Lo que deja cada comprador del principal después de comisiones, reembolsos y costos por unidad. Su par es el CPA.", wrap=True)
            self.ref["aov_neto"] = aref("Modelo", 3, r); self.fmt["aov_neto"] = "money"; self.label["aov_neto"] = "Cash neto por comprador (AOV neto)"
            r += 1
        for g in self.s.get("ganancia", []):
            k, nombre = g["key"], g["nombre"]
            key = f"gan_{k}"
            self.put(ws, r, 2, f"Ganancia por {nombre}", bold=g.get("bold", False))
            self.put(ws, r, 3, f"=IF({self.ref[k]}=0,0,{prof}/{self.ref[k]})", "money", "out", bold=g.get("bold", False))
            self.put(ws, r, 4, g.get("como", f"Ganancia del período ÷ {nombre}s. Su par es el costo por {nombre}."), wrap=True)
            self.ref[key] = aref("Modelo", 3, r); self.fmt[key] = "money"; self.label[key] = f"Ganancia por {nombre}"
            r += 1
        rng = f"C5:C{r}"
        self.semaforo_cf(ws, rng)
        ws.freeze_panes = "C5"
        return ws

    def build_embudo(self):
        """El embudo como tabla: cada paso con cantidad, % que pasa, % que se pierde, % acumulado, costo y techo por paso."""
        ws = self.sheet("Embudo", [2, 46, 13, 13, 13, 13, 14, 14, 15, 50])
        r = self.title(ws, 2, "Embudo: todos los pasos, cuántos, qué porcentaje pasa y cuánto cuesta cada uno",
                       "Cada fila es un paso del embudo en orden. '% que pasa' compara con el paso anterior (o con el que dice la nota). El costo por paso es inversión ÷ cantidad; el techo por paso es lo máximo que podrías pagar por él si lo demás se mantiene. Los pasos sin costo propio ya se pagaron con el CPA: mejoran el AOV.")
        r = self.header(ws, r, ["Paso", "Cantidad", "% que pasa", "% que se pierde", "% acumulado", "Costo por paso", "Techo por paso", "Ganancia por paso", "Qué se paga acá / cómo se lee"])
        prev = None
        inv, uni, vpu, prof = self.ref["inversion"], self.ref["unidades"], self.ref["vpu"], self.ref["profit"]
        antes_unidad = True
        for st in self.s["embudo"]:
            k = st["key"]; ref = self.ref[k]
            if k == "unidades":
                antes_unidad = False
            self.put(ws, r, 2, st.get("label", self.label.get(k, k)), bold=st.get("bold", False))
            self.put(ws, r, 3, f"={ref}", "int" if self.fmt.get(k) in ("int", "num1") else self.fmt.get(k, "int"), "out")
            vs = st.get("vs", prev)
            if vs:
                vref = self.ref[vs]
                self.put(ws, r, 4, f"=IF({vref}=0,0,{ref}/{vref})", "pct", "out")
                self.put(ws, r, 5, f"=IF({vref}=0,0,1-{ref}/{vref})", "pct", "out")
            else:
                self.put(ws, r, 4, "—"); self.put(ws, r, 5, "—")
            if antes_unidad:
                self.put(ws, r, 6, "—")
            else:
                self.put(ws, r, 6, f"=IF({uni}=0,0,{ref}/{uni})", "pct2", "out")
            mult = st.get("mult", 1)
            if st.get("costo", True):
                self.put(ws, r, 7, f"=IF({ref}=0,0,{inv}*{mult}/{ref})", "money", "out", bold=True)
            else:
                self.put(ws, r, 7, "sin costo propio")
            if st.get("techo", True):
                self.put(ws, r, 8, f"=IF({ref}=0,0,{vpu}*{uni}*{mult}/{ref})", "money", "out")
            else:
                self.put(ws, r, 8, "—")
            if st.get("costo", True) or k == "ventas_front":
                self.put(ws, r, 9, f"=IF({ref}=0,0,{prof}*{mult}/{ref})", "money", "out", bold=True)
            else:
                self.put(ws, r, 9, "—")
            self.put(ws, r, 10, st.get("nota", ""), wrap=True)
            prev = k
            r += 1
        r += 1
        self.put(ws, r, 2, "Cómo se lee", bold=True)
        for linea in ["Cantidad: cuántas acciones o personas hubo en ese paso con los supuestos del escenario en uso.",
                      "% que pasa: de los que estaban en el paso anterior (o en el paso que indica la nota), cuántos llegan a este. % que se pierde es el complemento.",
                      "% acumulado: cuántos llegan a este paso por cada 100 unidades que compra la pauta.",
                      "Costo por paso: inversión ÷ cantidad. Es lo que te está costando hoy cada persona que llega a ese paso.",
                      "Techo por paso: lo máximo que podrías pagar por ese paso sin perder plata, si lo demás se mantiene. Comparalo con el costo por paso: si el costo está por encima del techo, ese paso está caro.",
                      "Ganancia por paso: la ganancia del período dividida por la cantidad de ese paso. Es la otra cara del costo: cuánto te queda por cada visita, por cada lead, por cada comprador. La ganancia por visita es la métrica más valiosa del embudo: resume todo lo que pasa después.",
                      "Los bumps, las OTOs y la ascensión no tienen costo propio: se pagan con el CPA del comprador principal y se miden por lo que suman al AOV."]:
            r += 1
            self.put(ws, r, 2, linea, wrap=True)
            ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=10)
            ws.row_dimensions[r].height = 26
        ws.freeze_panes = "C5"
        return ws

    def build_resumen(self):
        ws = self.sheet("Resumen", [2, 52, 18, 60])
        r = self.title(ws, 2, "Resumen: lo que hay que mirar", "Todo sale de Modelo con los supuestos del escenario en uso. Cambiá Supuestos y esto se actualiza.")
        r = self.header(ws, r, ["Indicador", "Valor", "Qué significa"])
        for it in self.s["resumen"]:
            if "seccion" in it:
                r = self.section(ws, r, it["seccion"], ncols=3)
                continue
            self.put(ws, r, 2, self.label.get(it["key"], it.get("label", it["key"])) if "label" not in it else it["label"])
            self.put(ws, r, 3, f"={self.ref[it['key']]}", self.fmt[it["key"]], "out", bold=True)
            self.put(ws, r, 4, it.get("que", ""), wrap=True)
            r += 1
        r += 1
        self.put(ws, r, 2, "Recomendación según el semáforo", bold=True)
        sem = self.ref["semaforo"]
        self.put(ws, r, 3, f'=IF({sem}="VERDE","Sostener o subir un escalón (+25 %) y medir 7 días",IF({sem}="AMARILLO","No subir. Si el costo está bien, el ROAS no llega al objetivo: mirá Sensibilidad. Si no, revisar en orden: CPM, creativo, página",IF({sem}="ROJO","Bajar un escalón (−25 %) y arreglar antes de volver a subir","")))', None, "out")
        ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=4)
        ws.cell(r, 3).alignment = WRAP
        ws.row_dimensions[r].height = 32
        self.semaforo_cf(ws, f"C5:C{r}")
        return ws

    def build_escenarios(self):
        ws = self.sheet("Escenarios", [2, 24] + [15] * 9)
        r = self.title(ws, 2, "Escenarios: qué pasa si cambian el precio, la conversión o el costo",
                       "Las celdas amarillas de cada tabla (fila y columna) se pueden cambiar. Verde = ganancia, amarillo = cerca del cero, rojo = pérdida. Todo lo demás queda como en Supuestos.")
        self.put(ws, r, 2, "Umbral de 'cerca del cero' (inversión × margen de seguridad)")
        self.put(ws, r, 3, f"={self.ref['inversion']}*{self.ref['margen_seg']}", "money0", "out")
        umbral = f"$C${r}"
        r += 2
        for t in self.s["tablas"]:
            ws.cell(r, 2, t["titulo"]).font = FONT_B
            ws.cell(r + 1, 2, t["nota"]).font = FONT_NOTE
            r += 2
            hdr = r
            self.put(ws, hdr, 2, f"{t['fila_label']} ↓  /  {t['col_label']} →", bold=True)
            for j, v in enumerate(t["cols"]):
                self.put(ws, hdr, 3 + j, v, t["col_fmt"], "in", bold=True)
            for i, v in enumerate(t["filas"]):
                rr = hdr + 1 + i
                self.put(ws, rr, 2, v, t["fila_fmt"], "in", bold=True)
                for j in range(len(t["cols"])):
                    ov = {t["fila_key"]: f"$B{rr}", t["col_key"]: f"{col(3 + j)}${hdr}"}
                    self.put(ws, rr, 3 + j, "=" + self.expr(t["salida"], ov), t["salida_fmt"], "out")
            rng = f"C{hdr + 1}:{col(2 + len(t['cols']))}{hdr + len(t['filas'])}"
            if t.get("semaforo", True):
                self.profit_cf(ws, rng, umbral)
            r = hdr + len(t["filas"]) + 3
        # tabla de inversión por ROAS objetivo
        t = self.s["tabla_roas"]
        ws.cell(r, 2, t["titulo"]).font = FONT_B
        ws.cell(r + 1, 2, t["nota"]).font = FONT_NOTE
        r += 2
        hdr = r
        self.put(ws, hdr, 2, "Facturación objetivo ↓ / ROAS objetivo →", bold=True)
        for j, v in enumerate(t["roas"]):
            self.put(ws, hdr, 3 + j, v, "ratio", "in", bold=True)
        for i, v in enumerate(t["facturacion"]):
            rr = hdr + 1 + i
            self.put(ws, rr, 2, v, "money0", "in", bold=True)
            for j in range(len(t["roas"])):
                self.put(ws, rr, 3 + j, f"=$B{rr}/{col(3 + j)}${hdr}", "money0", "out")
        r = hdr + len(t["facturacion"]) + 1
        self.put(ws, r, 2, f"Cantidad de {t['unidad_label'].lower()} necesaria para esa facturación", bold=True)
        fpu = self.ref['fact_por_unidad']
        for i, v in enumerate(t["facturacion"]):
            self.put(ws, r + 1 + i, 2, f"=$B{hdr + 1 + i}", "money0")
            self.put(ws, r + 1 + i, 3, f'=IF({fpu}=0,"inalcanzable",$B{hdr + 1 + i}/{fpu})', "int", "out")
        r += len(t["facturacion"]) + 2
        self.put(ws, r, 2, f"Costo máximo por {t['unidad_singular']} para cumplir cada ROAS (sobre facturado)", bold=True)
        for j, v in enumerate(t["roas"]):
            self.put(ws, r + 1, 3 + j, v, "ratio", bold=True)
            self.put(ws, r + 2, 3 + j, f"=IF({col(3 + j)}{r + 1}=0,0,{fpu}/{col(3 + j)}{r + 1})", "money", "out")
        self.put(ws, r + 2, 2, "Costo máximo (facturado por unidad ÷ ROAS)")
        self.put(ws, r + 3, 2, "Sobre cash neto, el techo real está en Modelo (ya descuenta comisiones y reembolsos).").font = FONT_NOTE
        # guardarraíl: ROAS mínimo por nivel de inversión
        r += 6
        ws.cell(r, 2, "Guardarraíl: el ROAS mínimo que tiene que dar cada nivel de inversión para que subir valga la pena").font = FONT_B
        ws.cell(r + 1, 2, "Parte de tu inversión y tu ROAS actuales. Cada dólar extra tiene que devolver al menos 1,3 neto. Si al subir un escalón el ROAS real queda por debajo del mínimo de esa fila, volvé al escalón anterior.").font = FONT_NOTE
        r += 2
        r = self.header(ws, r, ["Nivel de inversión", "Inversión del período", "ROAS mínimo (cash neto)", "Ganancia mínima"])
        S0, R0 = self.ref["inversion"], self.ref["roas_cash"]
        for mult in [1.0, 1.25, 1.5, 2.0, 3.0]:
            self.put(ws, r, 2, "actual" if mult == 1 else f"× {mult:g}")
            self.put(ws, r, 3, f"={S0}*{mult}", "money0", "out")
            self.put(ws, r, 4, f"=IF(C{r}=0,0,({S0}*{R0}+1.3*(C{r}-{S0}))/C{r})", "ratio", "out")
            self.put(ws, r, 5, f"=C{r}*(D{r}-1)", "money0", "out")
            r += 1
        return ws

    def build_sensibilidad(self):
        ws = self.sheet("Sensibilidad", [2, 54, 14, 18, 18, 12, 10])
        r = self.title(ws, 2, "Sensibilidad: qué palanca mueve más la ganancia",
                       "Cada fila mejora una sola variable un 10 % (o baja un costo un 10 %) y recalcula la ganancia del período. El ranking dice qué conviene trabajar primero.")
        r = self.header(ws, r, ["Palanca", "Cambio", "Ganancia nueva", "Diferencia", "Dif. %", "Ranking"])
        base_ref = self.ref["profit"]
        self.put(ws, r, 2, "Ganancia del período con los supuestos actuales", bold=True)
        self.put(ws, r, 4, f"={base_ref}", "money0", "out", bold=True)
        base_row = r
        r += 1
        first = r
        for p in self.s["palancas"]:
            k, mult = p["key"], p["mult"]
            self.put(ws, r, 2, p["label"])
            self.put(ws, r, 3, "+10 %" if mult > 1 else "−10 %")
            ov = {k: f"({self.ref[k]}*{mult})"}
            self.put(ws, r, 4, "=" + self.expr("profit", ov), "money0", "out")
            self.put(ws, r, 5, f"=D{r}-$D${base_row}", "money0", "out")
            self.put(ws, r, 6, f"=IF($D${base_row}=0,0,E{r}/ABS($D${base_row}))", "pct", "out")
            r += 1
        last = r - 1
        for rr in range(first, last + 1):
            self.put(ws, rr, 7, f"=RANK(E{rr},$E${first}:$E${last})", "int", "out")
        return ws

    def build_proyeccion(self):
        ws = self.sheet("Proyección 12 meses", [2, 46] + [13] * 12 + [15])
        lm = self.ref.get("lanz_mes", "1")
        nota_lm = " Cada mes multiplica inversión, costos fijos y ventas por los lanzamientos por mes de Supuestos." if lm != "1" else ""
        r = self.title(ws, 2, "Proyección a 12 meses y caja",
                       "La inversión crece cada mes según el supuesto de crecimiento. El cash entra según la curva de cobranza (mes 1 / 2 / 3). La ganancia acumulada muestra cuánto dinero hace falta para sostener la pauta." + nota_lm)
        r = self.header(ws, r, ["Concepto"] + MESES + ["Total"])
        rows = {}

        def row(key, label, fmt, fn, total=True, bold=False):
            nonlocal r
            rows[key] = r
            self.put(ws, r, 2, label, bold=bold)
            for m in range(12):
                c = 3 + m
                self.put(ws, r, c, fn(m, c), fmt, "out", bold=bold)
            if total:
                self.put(ws, r, 15, f"=SUM(C{r}:N{r})", fmt, "out", bold=True)
            r += 1
        R = self.ref
        row("inv", "Inversión en publicidad del mes", "money0",
            lambda m, c: f"={R['inversion']}*{lm}" if m == 0 else f"={col(c - 1)}{rows['inv']}*(1+{R['crecimiento']})")
        row("uni", self.s["unidad_plural"].capitalize() + " compradas", "int",
            lambda m, c: f"=IF({R['cpu']}=0,0,{col(c)}{rows['inv']}/{R['cpu']})")
        row("ven", "Ventas del producto principal", "num1",
            lambda m, c: f"={col(c)}{rows['uni']}*{R['ventas_por_unidad']}")
        row("fac", "Facturado (todos los productos)", "money0",
            lambda m, c: f"={col(c)}{rows['uni']}*{R['fact_por_unidad']}")

        def cash(m, c):
            parts = [f"{col(c)}{rows['fac']}*{R['cobro_m1']}"]
            if m >= 1:
                parts.append(f"{col(c - 1)}{rows['fac']}*{R['cobro_m2']}")
            if m >= 2:
                parts.append(f"{col(c - 2)}{rows['fac']}*{R['cobro_m3']}")
            return "=" + "+".join(parts)
        row("cash", "Cash cobrado en el mes", "money0", cash)
        row("com", "Comisiones y reembolsos", "money0",
            lambda m, c: f"={col(c)}{rows['cash']}*({R['pasarela']}+{R['closers']}+{R['reembolsos']})")
        row("semi", "Costos por unidad (herramientas, WhatsApp, IA)", "money0",
            lambda m, c: f"={col(c)}{rows['uni']}*{R['costo_semivar']}")
        row("fij", "Costos fijos del mes", "money0", lambda m, c: f"={R['fijos']}*{lm}")
        row("prof", "Ganancia de caja del mes", "money0",
            lambda m, c: f"={col(c)}{rows['cash']}-{col(c)}{rows['com']}-{col(c)}{rows['semi']}-{col(c)}{rows['fij']}-{col(c)}{rows['inv']}", bold=True)
        row("acum", "Ganancia de caja acumulada (desde cero)", "money0",
            lambda m, c: f"={col(c)}{rows['prof']}" if m == 0 else f"={col(c - 1)}{rows['acum']}+{col(c)}{rows['prof']}",
            total=False, bold=True)
        row("caja", "Saldo de caja (caja inicial + ganancia acumulada)", "money0",
            lambda m, c: f"={R['caja_inicial']}+{col(c)}{rows['acum']}", total=False)
        r += 1
        self.put(ws, r, 2, "Caja necesaria para no frenar la pauta (el peor momento de la ganancia acumulada)", bold=True)
        self.put(ws, r, 3, f"=MAX(0,-MIN(C{rows['acum']}:N{rows['acum']}))", "money0", "out", bold=True)
        self.ref["caja_necesaria"] = aref("Proyección 12 meses", 3, r)
        self.fmt["caja_necesaria"] = "money0"
        r += 1
        self.put(ws, r, 2, "Saldo mínimo de caja con tu caja inicial", bold=True)
        self.put(ws, r, 3, f"=MIN(C{rows['caja']}:N{rows['caja']})", "money0", "out", bold=True)
        self.ref["caja_minima"] = aref("Proyección 12 meses", 3, r)
        self.fmt["caja_minima"] = "money0"
        r += 1
        self.put(ws, r, 2, "Ganancia de caja acumulada en 12 meses", bold=True)
        self.put(ws, r, 3, f"=O{rows['prof']}", "money0", "out", bold=True)
        self.ref["profit_12m"] = aref("Proyección 12 meses", 3, r)
        self.fmt["profit_12m"] = "money0"
        self.profit_cf(ws, f"C{rows['prof']}:N{rows['prof']}", "0.0001")
        ws.freeze_panes = "C5"
        return ws

    def build_seguimiento(self):
        sg = self.s["seguimiento"]
        n = 12
        ws = self.sheet("Seguimiento", [2, 52] + [13] * n + [13, 13, 13])
        r = self.title(ws, 2, f"Seguimiento: una columna por {sg['periodo']}",
                       f"Cargá los datos reales en las celdas amarillas. El semáforo compara tu costo real por {self.s['unidad_singular']} con el techo móvil (lo que rindieron tus últimas 4 columnas) y con el techo del modelo.")
        r = self.header(ws, r, ["Dato"] + [f"{sg['periodo'].capitalize()} {i + 1}" for i in range(n)] + ["Promedio", "Máximo", "Mínimo"])
        rows = {}
        first_in = None
        last_in = None
        n_in = sum(1 for it in sg["filas"] if it.get("tipo") == "in")
        for it in sg["filas"]:
            if "seccion" in it:
                r = self.section(ws, r, it["seccion"], ncols=n + 1)
                continue
            k = it["key"]
            rows[k] = r
            self.put(ws, r, 2, it["label"], bold=it.get("bold", False))
            if it["tipo"] == "in":
                if first_in is None:
                    first_in = r
                last_in = r
                ej = it.get("ejemplo", [])
                for i in range(n):
                    self.put(ws, r, 3 + i, ej[i] if i < len(ej) else None, it["fmt"], "in")
            else:
                for i in range(n):
                    c = 3 + i
                    L = col(c)
                    if it["tipo"] == "f":
                        body = KEY_RE.sub(lambda m: f"{L}{rows[m.group(1)]}" if m.group(1) in rows else self.ref[m.group(1)], guard_div(it["f"]))
                    elif it["tipo"] == "techo_movil":
                        src = rows[it["src"]]
                        lo = max(3, c - 4)
                        prev = f"{col(lo)}{src}:{col(c - 1)}{src}" if c > 3 else None
                        body = f"IF(COUNT({prev})>0,MEDIAN({prev}),{self.ref['techo_cpu']})" if prev else self.ref["techo_cpu"]
                    elif it["tipo"] == "semaforo":
                        cpu, techo, roas = f"{L}{rows[it['cpu']]}", f"{L}{rows[it['techo']]}", f"{L}{rows[it['roas']]}"
                        body = f'IF({cpu}>{techo},"ROJO",IF(AND({cpu}<={techo}/(1+{self.ref["margen_seg"]}),{roas}>={self.ref["roas_obj"]}),"VERDE","AMARILLO"))'
                    self.put(ws, r, c, f'=IF(COUNT({L}{first_in}:{L}{last_in})<{n_in},"",{body})', it["fmt"], "out", bold=it.get("bold", False))
            if it["tipo"] in ("in", "f", "techo_movil"):
                rng = f"C{r}:{col(2 + n)}{r}"
                for j, fn in enumerate(["AVERAGE", "MAX", "MIN"]):
                    self.put(ws, r, 3 + n + j, f'=IF(COUNT({rng})=0,"",{fn}({rng}))', it["fmt"], "out")
            r += 1
        self.semaforo_cf(ws, f"C5:{col(2 + n)}{r}")
        ws.freeze_panes = "C5"
        return ws

    def build_benchmarks(self):
        ws = self.sheet("Benchmarks", [2, 40, 14, 14, 14, 14, 16, 60])
        r = self.title(ws, 2, "Benchmarks: contra qué comparar tus números",
                       "Valores de referencia para tráfico frío en español. Son orden de magnitud, no objetivo: tus propios datos de Seguimiento mandan.")
        r = self.header(ws, r, ["Métrica", "Malo", "Aceptable", "Bueno", "Ganador", "Tu valor (Modelo)", "Fuente / nota"])
        for b in self.s["benchmarks"]:
            self.put(ws, r, 2, b["metrica"])
            for j, v in enumerate(b["niveles"]):
                self.put(ws, r, 3 + j, v)
            if b.get("key"):
                self.put(ws, r, 7, f"={self.ref[b['key']]}", self.fmt[b["key"]], "out")
            self.put(ws, r, 8, b.get("fuente", ""), wrap=True)
            r += 1
        return ws

    def build_glosario(self):
        ws = self.sheet("Glosario", [2, 30, 90, 26])
        r = self.title(ws, 2, "Glosario", "Los términos que usa este modelo, en el orden del embudo.")
        r = self.header(ws, r, ["Término", "Qué es", "Dónde aparece"])
        for g in self.s["glosario"]:
            self.put(ws, r, 2, g[0], bold=True)
            self.put(ws, r, 3, g[1], wrap=True)
            self.put(ws, r, 4, g[2])
            ws.row_dimensions[r].height = max(15, 15 * (1 + len(g[1]) // 85))
            r += 1
        return ws

    def build_chequeos(self):
        ws = self.sheet("Chequeos", [2, 70, 14, 60])
        r = self.title(ws, 2, "Chequeos: el modelo se revisa solo", "Si alguna fila dice REVISAR, hay un supuesto fuera de rango o un dato inconsistente.")
        r = self.header(ws, r, ["Chequeo", "Estado", "Qué revisar"])
        first = r
        for hoja, rng in [("Modelo", "C5:C160"), ("Embudo", "C5:I60"), ("Resumen", "C5:C60"), ("Proyección 12 meses", "C5:O40"), ("Escenarios", "C5:L120"), ("Seguimiento", "C5:Q80")]:
            self.put(ws, r, 2, f"Ninguna celda con error en {hoja}")
            self.put(ws, r, 3, f"=IF(ISERROR(SUM('{hoja}'!{rng})),\"REVISAR\",\"OK\")", None, "out")
            self.put(ws, r, 4, "Si dice REVISAR, hay un #DIV/0! o #REF!: casi siempre un supuesto en 0 o una fila borrada.", wrap=True)
            r += 1
        for ch in self.s["chequeos"]:
            self.put(ws, r, 2, ch["label"])
            cond = KEY_RE.sub(lambda m: self.ref[m.group(1)], ch["cond"])
            self.put(ws, r, 3, f'=IF({cond},"OK","REVISAR")', None, "out")
            self.put(ws, r, 4, ch.get("ayuda", ""), wrap=True)
            r += 1
        last = r - 1
        r += 1
        self.put(ws, r, 2, "Estado general del modelo", bold=True)
        self.put(ws, r, 3, f'=IF(COUNTIF(C{first}:C{last},"REVISAR")=0,"OK","REVISAR")', None, "out", bold=True)
        ws.conditional_formatting.add(f"C{first}:C{r}", CellIsRule(operator="equal", formula=['"OK"'], fill=FILL_OK))
        ws.conditional_formatting.add(f"C{first}:C{r}", CellIsRule(operator="equal", formula=['"REVISAR"'], fill=FILL_BAD))
        return ws

    def build(self, path):
        self.build_inicio()
        self.build_supuestos()
        self.build_modelo()
        self.build_embudo()
        self.build_proyeccion()
        self.build_resumen()
        self.build_escenarios()
        self.build_sensibilidad()
        self.build_seguimiento()
        self.build_benchmarks()
        self.build_glosario()
        self.build_chequeos()
        order = ["Inicio", "Resumen", "Embudo", "Supuestos", "Modelo", "Escenarios", "Sensibilidad",
                 "Proyección 12 meses", "Seguimiento", "Benchmarks", "Glosario", "Chequeos"]
        self.wb._sheets = [self.wb[n] for n in order]
        self.wb.active = 0
        # marca de agua: propiedades del archivo y una línea al pie de Resumen
        from mf_comun import MARCA, AUTOR, VERSION
        self.wb.properties.creator = AUTOR
        self.wb.properties.lastModifiedBy = AUTOR
        self.wb.properties.title = self.s["titulo"]
        self.wb.properties.subject = MARCA
        self.wb.properties.description = MARCA + " · " + VERSION
        self.wb.properties.keywords = "modelo financiero, embudo, TooAudience, " + AUTOR
        ws = self.wb["Resumen"]
        r = ws.max_row + 2
        ws.cell(r, 2, MARCA + " · " + VERSION).font = FONT_NOTE
        self.wb.save(path)
        return path
