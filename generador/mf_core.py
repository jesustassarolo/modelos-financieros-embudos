#!/usr/bin/env python3
"""Núcleo del generador de modelos financieros de embudos (Excel / Google Sheets).

Una especificación (ver mf_specs.py) describe un embudo: supuestos, cadena de cálculo,
tablas de escenarios, palancas, proyección, seguimiento, benchmarks y textos. Este módulo
la convierte en un libro .xlsx con fórmulas vivas, compatible con Google Sheets.

Convención de colores (la de TooAudience): amarillo = entrada editable, azul = resultado.
Fórmulas: solo funciones básicas (IF, SUM, MIN, MAX, MEDIAN, COUNT, ABS, RANK) para que
funcionen igual en Excel, Google Sheets y Numbers.
"""
import os
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

    def build_simulador(self):
        """La hoja Modelo, pero editable en orden de embudo: cada supuesto aparece justo antes del primer paso que lo usa,
        con tu número (amarillo) al lado de la base; cada resultado se calcula con tus números y se compara con el Modelo."""
        ws = self.sheet("Simulador", [2, 56, 17, 17, 19, 19, 15, 62])
        r = self.title(ws, 2, "Simulador: movés un número y ves cómo se mueve todo el embudo",
                       "Amarillo = tu número: arranca igual a Supuestos; escribí encima para probar (CPM, CTR, conversiones, precios, costos). "
                       "Al lado, la base. 'Con tus números' se recalcula al instante y se compara con el Modelo. Para volver a la base, "
                       "borrá la celda amarilla y escribí =D seguido del número de fila (por ejemplo =D9).")
        r = self.header(ws, r, ["Paso / métrica", "Tu número (editable)", "Base (Supuestos)", "Con tus números", "Base (Modelo)", "Diferencia", "Cómo se calcula", "Rango"])
        ws.column_dimensions[col(9)].width = 11
        first = r
        sim = {}        # clave -> celda del simulador (supuestos: columna C; cálculos: columna E)
        filas_in = []   # filas de supuestos
        sem_rows = []
        from openpyxl.worksheet.datavalidation import DataValidation
        dv_pct = DataValidation(type="decimal", operator="between", formula1="0", formula2="1", allow_blank=False, showErrorMessage=True,
                                errorTitle="Porcentaje fuera de rango", error="Escribí el porcentaje como fracción entre 0 y 1 (15 % = 0,15).")
        dv_pos = DataValidation(type="decimal", operator="greaterThanOrEqual", formula1="0", allow_blank=False, showErrorMessage=True,
                                errorTitle="Valor inválido", error="Tiene que ser un número mayor o igual a 0.")
        ws.add_data_validation(dv_pct); ws.add_data_validation(dv_pos)

        def fila_supuesto(dep, r):
            fmt = self.fmt.get(dep)
            self.put(ws, r, 2, self.label.get(dep, dep))
            self.put(ws, r, 3, "=" + self.ref[dep], fmt, "in")
            self.put(ws, r, 4, "=" + self.ref[dep], fmt, "out")
            self.put(ws, r, 7, f'=IF(C{r}<>D{r},"← cambiado","")')
            self.put(ws, r, 8, "Supuesto. Escribí encima para probar; la base queda al lado.", wrap=True)
            if fmt in ("pct", "pct2"):
                self.put(ws, r, 9, f'=IF(AND(ISNUMBER(C{r}),C{r}>=0,C{r}<=1),"OK","REVISAR")', None, "out"); dv_pct.add(f"C{r}")
            else:
                self.put(ws, r, 9, f'=IF(AND(ISNUMBER(C{r}),C{r}>=0),"OK","REVISAR")', None, "out"); dv_pos.add(f"C{r}")
            sim[dep] = f"$C${r}"; filas_in.append(r)

        for it in self.s["calculo"]:
            if "seccion" in it:
                r = self.section(ws, r, it["seccion"], ncols=7)
                continue
            k = it["key"]; tpl = self.tpl[k]
            for dep in KEY_RE.findall(tpl):
                if dep in self.base and dep not in sim and dep != "escenario":
                    fila_supuesto(dep, r); r += 1
            faltan = [d for d in KEY_RE.findall(tpl) if d not in sim]
            if faltan:
                raise KeyError(f"Simulador: {k} usa {faltan} antes de definirse")
            self.put(ws, r, 2, it["label"], bold=it.get("bold", False))
            self.put(ws, r, 5, self.formula(tpl, overrides=sim), it["fmt"], "out", bold=it.get("bold", False))
            self.put(ws, r, 6, "=" + self.ref[k], it["fmt"], "out")
            if it["fmt"] == "txt":
                self.put(ws, r, 7, f'=IF(E{r}=F{r},"","≠ base")'); sem_rows.append(r)
            else:
                self.put(ws, r, 7, f'=IF(AND(ISNUMBER(E{r}),ISNUMBER(F{r})),E{r}-F{r},"")', it["fmt"], "out")
            self.put(ws, r, 8, it.get("como", ""), wrap=True)
            sim[k] = f"$E${r}"; r += 1
        # ganancia por paso, con los números del simulador
        r = self.section(ws, r, "Ganancia por paso (las dos caras de cada número)", ncols=7)
        self.put(ws, r, 2, "Cash neto por comprador (AOV neto)", bold=True)
        self.put(ws, r, 5, f"=IF({sim['ventas_front']}=0,0,({sim['neto']}-{sim['semivar']})/{sim['ventas_front']})", "money", "out", bold=True)
        self.put(ws, r, 6, "=" + self.ref["aov_neto"], "money", "out"); self.put(ws, r, 7, f'=IF(AND(ISNUMBER(E{r}),ISNUMBER(F{r})),E{r}-F{r},"")', "money", "out")
        self.put(ws, r, 8, "Lo que deja cada comprador después de comisiones, reembolsos y costos por unidad. Su par es el CPA.", wrap=True); r += 1
        for g in self.s.get("ganancia", []):
            k, nombre = g["key"], g["nombre"]
            self.put(ws, r, 2, f"Ganancia por {nombre}", bold=g.get("bold", False))
            self.put(ws, r, 5, f"=IF({sim[k]}=0,0,{sim['profit']}/{sim[k]})", "money", "out", bold=g.get("bold", False))
            self.put(ws, r, 6, "=" + self.ref[f"gan_{k}"], "money", "out"); self.put(ws, r, 7, f'=IF(AND(ISNUMBER(E{r}),ISNUMBER(F{r})),E{r}-F{r},"")', "money", "out")
            self.put(ws, r, 8, g.get("como", f"Ganancia del período ÷ {nombre}s. Su par es el costo por {nombre}."), wrap=True); r += 1
        last = r - 1
        self.sim = sim; self.sim_rango = f"'Simulador'!$I${first}:$I${last}"
        self.sim_abs = {k: "'Simulador'!" + v for k, v in sim.items()}   # para referenciar el Simulador desde otras hojas
        ws.conditional_formatting.add(f"I{first}:I{last}", CellIsRule(operator="equal", formula=['"REVISAR"'], fill=FILL_BAD))
        # formatos condicionales: supuesto cambiado en naranja; semáforos con color
        ws.conditional_formatting.add(f"C{first}:C{last}", FormulaRule(formula=[f"AND(ISNUMBER(C{first}),C{first}<>D{first})"], fill=PatternFill("solid", fgColor="F8CBAD")))
        for rr in sem_rows:
            self.semaforo_cf(ws, f"E{rr}:F{rr}")
        r += 1
        for linea in ["Cómo se lee: cambiá una celda amarilla (por ejemplo el CPM, el CTR, la conversión de la landing, el show, el cierre o el precio) y mirá cómo se mueven la cantidad de cada paso, el costo por paso, el facturado, el cash neto, la ganancia, el ROAS, el techo y el semáforo.",
                      "Una variable por vez: si cambiás tres cosas no sabés cuál movió el resultado. La columna Diferencia te muestra exactamente cuánto cambió cada número contra la base.",
                      "El Simulador no modifica Supuestos ni Modelo: es tu mesa de pruebas. Cuando una prueba te convence, pasá ese número a Supuestos.",
                      "La columna Rango avisa si escribiste algo imposible (un porcentaje fuera de 0 a 1, un negativo, texto) y Chequeos repite los chequeos del modelo con tus números del Simulador."]:
            c = ws.cell(r, 2, linea); c.alignment = WRAP; ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=8); ws.row_dimensions[r].height = 30; r += 1
        ws.freeze_panes = "C5"
        return ws

    def build_simulacion(self, path):
        """Excel APARTE por embudo: la hoja Modelo, idéntica (etapa · valor · cómo se calcula), pero con todos los supuestos
        como números editables intercalados en su lugar de la cadena. Sin vínculos con ningún otro archivo: se cambia un
        número y todo lo que depende se recalcula."""
        from openpyxl.worksheet.datavalidation import DataValidation
        from mf_comun import aplicar_marca, MARCA, VERSION
        if not self.tpl:
            self.build_supuestos(); self.build_modelo()
        base_val, nota, unidad = {}, {}, {}
        for grupo in self.s["supuestos"]:
            for it in grupo["items"]:
                base_val[it["key"]] = it["esc"][1] if "esc" in it else it["val"]
                nota[it["key"]] = it.get("nota", ""); unidad[it["key"]] = it.get("unidad", "")
        wb2 = openpyxl.Workbook(); wb2.remove(wb2.active)
        wb_modelo, self.wb = self.wb, wb2
        ws = self.sheet("Simulación", [2, 60, 18, 72])
        self.wb = wb_modelo
        titulo = self.s["titulo"].replace("Modelo financiero", "Simulación")
        r = self.title(ws, 2, "Simulación: la cadena completa del embudo, con todos los números para jugar",
                       "Amarillo = supuesto: cambialo y todo lo que depende se recalcula al instante. Azul = resultado. Mismo orden y mismas fórmulas que la hoja Modelo del modelo financiero. Este archivo no se conecta con ningún otro: es tu mesa de pruebas.")
        self.put(ws, 4, 2, "Estado de tus números", bold=True)
        r = self.header(ws, r, ["Etapa / resultado", "Valor", "Cómo se calcula"])
        dv_pct = DataValidation(type="decimal", operator="between", formula1="0", formula2="1", allow_blank=False, showErrorMessage=True,
                                errorTitle="Porcentaje fuera de rango", error="Escribí el porcentaje como fracción entre 0 y 1 (15 % = 0,15).")
        dv_pos = DataValidation(type="decimal", operator="greaterThanOrEqual", formula1="0", allow_blank=False, showErrorMessage=True,
                                errorTitle="Valor inválido", error="Tiene que ser un número mayor o igual a 0.")
        ws.add_data_validation(dv_pct); ws.add_data_validation(dv_pos)
        sim, entradas, sem_rows = {}, [], []

        def fila_supuesto(dep, r):
            fmt = self.fmt.get(dep)
            self.put(ws, r, 2, self.label.get(dep, dep))
            self.put(ws, r, 3, base_val[dep], fmt, "in")
            texto = "Supuesto" + (f" ({unidad[dep]})" if unidad.get(dep) else "") + (". " + nota[dep] if nota.get(dep) else ". Cambialo para probar.")
            self.put(ws, r, 4, texto, wrap=True)
            if fmt in ("pct", "pct2"): dv_pct.add(f"C{r}")
            else: dv_pos.add(f"C{r}")
            sim[dep] = f"$C${r}"; entradas.append((r, fmt))

        for it in self.s["calculo"]:
            if "seccion" in it:
                r = self.section(ws, r, it["seccion"], ncols=3); continue
            k = it["key"]; tpl = self.tpl[k]
            for dep in KEY_RE.findall(tpl):
                if dep in self.base and dep not in sim and dep != "escenario":
                    fila_supuesto(dep, r); r += 1
            faltan = [d for d in KEY_RE.findall(tpl) if d not in sim]
            if faltan:
                raise KeyError(f"Simulación: {k} usa {faltan} antes de definirse")
            self.put(ws, r, 2, it["label"], bold=it.get("bold", False))
            self.put(ws, r, 3, self.formula(tpl, overrides=sim), it["fmt"], "out", bold=it.get("bold", False))
            self.put(ws, r, 4, it.get("como", ""), wrap=True)
            if it["fmt"] == "txt": sem_rows.append(r)
            sim[k] = f"$C${r}"; r += 1
        r = self.section(ws, r, "Ganancia por paso (las dos caras de cada número: costo por X y ganancia por X)", ncols=3)
        self.put(ws, r, 2, "Cash neto por comprador (AOV neto)", bold=True)
        self.put(ws, r, 3, f"=IF({sim['ventas_front']}=0,0,({sim['neto']}-{sim['semivar']})/{sim['ventas_front']})", "money", "out", bold=True)
        self.put(ws, r, 4, "Lo que deja cada comprador del principal después de comisiones, reembolsos y costos por unidad. Su par es el CPA.", wrap=True); r += 1
        for g in self.s.get("ganancia", []):
            k, nombre = g["key"], g["nombre"]
            self.put(ws, r, 2, f"Ganancia por {nombre}", bold=g.get("bold", False))
            self.put(ws, r, 3, f"=IF({sim[k]}=0,0,{sim['profit']}/{sim[k]})", "money", "out", bold=g.get("bold", False))
            self.put(ws, r, 4, g.get("como", f"Ganancia del período ÷ {nombre}s. Su par es el costo por {nombre}."), wrap=True); r += 1
        # estado de los supuestos (fila 4) y colores
        conds = []
        for rr, fmt in entradas:
            conds.append(f"ISNUMBER(C{rr}),C{rr}>=0" + (f",C{rr}<=1" if fmt in ("pct", "pct2") else ""))
        self.put(ws, 4, 3, f'=IF(AND({",".join(conds)}),"OK","REVISAR")', None, "out", bold=True)
        self.put(ws, 4, 4, "OK = todos los supuestos tienen sentido. REVISAR = hay un porcentaje fuera de 0 a 1, un negativo o un texto donde va un número.", wrap=True)
        ws.conditional_formatting.add("C4", CellIsRule(operator="equal", formula=['"OK"'], fill=FILL_OK))
        ws.conditional_formatting.add("C4", CellIsRule(operator="equal", formula=['"REVISAR"'], fill=FILL_BAD))
        for rr in sem_rows:
            self.semaforo_cf(ws, f"C{rr}:C{rr}")
        r += 1
        for linea in ["Cómo se usa: cambiá cualquier celda amarilla (inversión, CPM, CTR, conversión de la landing, show, solicitudes, cierre, precios, comisiones, costos, cobranza, meta) y mirá cómo se mueven todas las celdas azules de abajo: cantidades, costos por paso, facturado, cash neto, ganancia, ROAS, el techo y el objetivo, el semáforo y la inversión para tu meta.",
                      "Una variable por vez. Si querés comparar dos ideas, duplicá la hoja (clic derecho en la pestaña → Duplicar) y cambiá en cada copia una sola cosa.",
                      "Para volver al ejemplo, el valor original de cada supuesto está en la hoja Inicio."]:
            c = ws.cell(r, 2, linea); c.alignment = WRAP; ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=4); ws.row_dimensions[r].height = 32; r += 1
        ws.freeze_panes = "C6"
        # Inicio corto con los valores del ejemplo
        ws0 = wb2.create_sheet("Inicio", 0); ws0.column_dimensions["A"].width = 2; ws0.column_dimensions["B"].width = 70; ws0.column_dimensions["C"].width = 16
        ws0.cell(2, 2, titulo).font = FONT_TITLE
        ws0.cell(3, 2, "Un solo Excel para simular: la cadena completa del embudo con todos los números editables. No se conecta con el modelo financiero ni con las métricas diarias.").font = FONT_NOTE
        rr = 5
        for t, body in [("Qué es", "La hoja Modelo del modelo financiero de este embudo, idéntica, pero con cada supuesto como número editable en su lugar de la cadena (inversión, CPM, CTR, visitas, conversión, asistencia, solicitudes, cierre, precios, comisiones, costos, cobranza, meta). Cambiás uno y se recalcula todo lo que depende."),
                        ("Cómo se usa", "Abrí la hoja Simulación. Las celdas amarillas se editan; las azules se calculan. Movés un número y mirás cómo cambian cantidades, costos por paso, facturado, cash neto, ganancia, ROAS, techo, objetivo y semáforo. La fila 'Estado de tus números' avisa si escribiste algo imposible."),
                        ("Para qué", "Para contestar antes de invertir: ¿qué pasa si el CPM sube un 30 %? ¿Y si el show baja al 10 %? ¿Y si subo el precio y el cierre cae? ¿Hasta qué CPL aguanta este embudo? Cuando una prueba te convence, pasá ese número a Supuestos del modelo financiero."),
                        ("Regla", "Una variable por vez. Para comparar ideas, duplicá la hoja y cambiá una sola cosa en cada copia.")]:
            ws0.cell(rr, 2, t).font = FONT_B; rr += 1
            c = ws0.cell(rr, 2, body); c.alignment = WRAP; ws0.row_dimensions[rr].height = 15 * (1 + len(body) // 90); rr += 2
        ws0.cell(rr, 2, "Valores del ejemplo (por si querés volver)").font = FONT_B; rr += 1
        for grupo in self.s["supuestos"]:
            for it in grupo["items"]:
                if it["key"] in sim:
                    ws0.cell(rr, 2, it["label"]); c = ws0.cell(rr, 3, base_val[it["key"]]); c.number_format = FMT[it["fmt"]]; rr += 1
        rr += 1
        ws0.cell(rr, 2, MARCA + " · " + VERSION).font = FONT_NOTE
        aplicar_marca(wb2, titulo, "Simulación · " + VERSION)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        wb2.save(path)
        return path

    def build_embudo(self):
        """El embudo como tabla: cada paso con cantidad, % que pasa, % acumulado, costo, ganancia y techo por paso."""
        ws = self.sheet("Embudo", [2, 46, 13, 13, 13, 15, 15, 15, 50])
        r = self.title(ws, 2, "Embudo: todos los pasos, cuántos pasan y, por cada uno, qué pagás, qué te queda y hasta cuánto podrías pagar",
                       "Cada fila es un paso del embudo en orden. '% que pasa' compara con el paso anterior (o con el que dice la nota). Tres números por paso: lo que pagás hoy por cada uno (inversión ÷ cantidad), lo que te queda por cada uno (ganancia ÷ cantidad) y lo máximo que podrías pagar (el techo: lo que cada uno genera en cash neto). Techo = costo + ganancia + fijos repartidos.")
        r = self.header(ws, r, ["Paso", "Cantidad", "% que pasa", "% acumulado", "Costo por paso (pagás hoy)", "Ganancia por paso (te queda)", "Techo por paso (máximo a pagar)", "Qué se paga acá / cómo se lee"])
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
            else:
                self.put(ws, r, 4, "—")
            if antes_unidad:
                self.put(ws, r, 5, "—")
            else:
                self.put(ws, r, 5, f"=IF({uni}=0,0,{ref}/{uni})", "pct2", "out")
            mult = st.get("mult", 1)
            con_costo = st.get("costo", True)
            if con_costo:
                self.put(ws, r, 6, f"=IF({ref}=0,0,{inv}*{mult}/{ref})", "money", "out", bold=True)
            else:
                self.put(ws, r, 6, "sin costo propio")
            if con_costo or k == "ventas_front":
                self.put(ws, r, 7, f"=IF({ref}=0,0,{prof}*{mult}/{ref})", "money", "out", bold=True)
            else:
                self.put(ws, r, 7, "—")
            if st.get("techo", True) and con_costo:
                self.put(ws, r, 8, f"=IF({ref}=0,0,{vpu}*{uni}*{mult}/{ref})", "money", "out", bold=True)
            else:
                self.put(ws, r, 8, "—")
            self.put(ws, r, 9, st.get("nota", ""), wrap=True)
            if k == "unidades":
                fila_unidad = r
            prev = k
            r += 1
        r += 1
        self.put(ws, r, 2, "Comprobalo con la fila de la unidad: costo + ganancia + fijos repartidos = techo", bold=True)
        self.put(ws, r, 6, f"=F{fila_unidad}", "money", "out")
        self.put(ws, r, 7, f"=G{fila_unidad}", "money", "out")
        self.put(ws, r, 8, f"=F{fila_unidad}+G{fila_unidad}+{self.ref['fijos']}/{uni}", "money", "out", bold=True)
        self.put(ws, r, 9, "Techo = costo + ganancia + fijos ÷ unidades. Lo que falta entre (costo + ganancia) y el techo son los costos fijos repartidos entre las unidades.", wrap=True)
        r += 1
        self.put(ws, r, 2, "Cómo se lee", bold=True)
        for linea in ["Cantidad: cuántas acciones o personas hubo en ese paso con los supuestos del escenario en uso.",
                      "% que pasa: de los que estaban en el paso anterior (o en el paso que indica la nota), cuántos llegan a este. % acumulado: cuántos llegan a este paso por cada 100 unidades que compra la pauta.",
                      "Costo por paso: inversión ÷ cantidad. Es lo que te está costando hoy cada persona que llega a ese paso.",
                      "Ganancia por paso: ganancia del período ÷ cantidad. Lo que te queda por cada persona de ese paso después de pagar la pauta, las comisiones, los reembolsos y los fijos. La ganancia por visita es la métrica más valiosa del embudo: resume todo lo que pasa después.",
                      "Techo por paso: lo que cada persona de ese paso genera en cash neto (cash neto menos costos por unidad, dividido por la cantidad). Es lo máximo que podrías pagar por ese paso antes de que la ganancia llegue a cero, si lo demás se mantiene. Por eso siempre es mayor que la ganancia: techo = costo + ganancia + fijos repartidos.",
                      "Los bumps, las OTOs y la ascensión no tienen costo propio: se pagan con el CPA del comprador principal y se miden por lo que suman al AOV."]:
            r += 1
            self.put(ws, r, 2, linea, wrap=True)
            ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=9)
            ws.row_dimensions[r].height = 28
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
        for hoja, rng in [("Modelo", "C5:C160")] + ([("Simulador", "C5:G220")] if getattr(self, "sim", None) else []) + [("Embudo", "C5:H60"), ("Resumen", "C5:C60"), ("Proyección 12 meses", "C5:O40"), ("Escenarios", "C5:L120"), ("Seguimiento", "C5:Q80")]:
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
        # los mismos chequeos, con los números que escribiste en el Simulador
        if getattr(self, "sim", None):
            r = self.section(ws, r, "Simulador: lo que escribiste en las celdas amarillas", ncols=3)
            self.put(ws, r, 2, "Ningún supuesto del Simulador fuera de rango (porcentajes entre 0 y 1, números no negativos)")
            self.put(ws, r, 3, f'=IF(COUNTIF({self.sim_rango},"REVISAR")=0,"OK","REVISAR")', None, "out")
            self.put(ws, r, 4, "La columna Rango del Simulador marca la fila con el problema.", wrap=True)
            r += 1
            for ch in self.s["chequeos"]:
                self.put(ws, r, 2, "Simulador: " + ch["label"])
                cond = KEY_RE.sub(lambda m: self.sim_abs.get(m.group(1), self.ref[m.group(1)]), ch["cond"])
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
        if self.s.get("simulador_en_modelo"):
            self.build_simulador()
        self.build_embudo()
        self.build_proyeccion()
        self.build_resumen()
        self.build_escenarios()
        self.build_sensibilidad()
        self.build_seguimiento()
        self.build_benchmarks()
        self.build_glosario()
        self.build_chequeos()
        order = ["Inicio", "Resumen", "Simulador", "Embudo", "Supuestos", "Modelo", "Escenarios", "Sensibilidad",
                 "Proyección 12 meses", "Seguimiento", "Benchmarks", "Glosario", "Chequeos"]
        order = [n for n in order if n in self.wb.sheetnames]
        self.wb._sheets = [self.wb[n] for n in order]
        self.wb.active = 0
        # marca de agua: propiedades del archivo y una línea al pie de Resumen
        from mf_comun import MARCA, AUTOR, VERSION, aplicar_marca
        aplicar_marca(self.wb, self.s["titulo"], VERSION)
        ws = self.wb["Resumen"]
        r = ws.max_row + 2
        ws.cell(r, 2, MARCA + " · " + VERSION).font = FONT_NOTE
        self.wb.save(path)
        return path
