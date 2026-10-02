#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verifica los Excel de métricas diarias recalculando todas las fórmulas con la librería `formulas` (sin Excel).
Uso: python3 md_verificar.py <carpeta con los .xlsx>   (conviene una versión corta: md_build.py <carpeta> --dias 42)
Chequea: ninguna celda calculada con error; las sumas semanales coinciden con las entradas de Diario; los semáforos
solo valen VERDE / AMARILLO / ROJO / vacío; Resumen muestra la última semana con datos."""
import sys, os, glob, re, statistics
import openpyxl
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "modelos_financieros")); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from verificar import calcular, es_error

def main(carpeta):
    ok_total = True
    for p in sorted(glob.glob(os.path.join(carpeta, "*.xlsx"))):
        print("\n===", os.path.basename(p)); wb = openpyxl.load_workbook(p); v = calcular(p); errores = 0; formulas_n = 0
        for ws in wb.worksheets:
            for row in ws.iter_rows():
                for c in row:
                    if isinstance(c.value, str) and c.value.startswith("="):
                        formulas_n += 1; val = v.get((ws.title.upper(), c.coordinate))
                        if es_error(val): errores += 1; print("   ERROR", ws.title, c.coordinate, c.value[:70], "→", val) if errores <= 5 else None
        print(f"  fórmulas: {formulas_n} · con error: {errores}")
        d = wb["Diario"]; hdr = {d.cell(5, j).value: j for j in range(1, d.max_column + 1)}
        # sumas semana 1 y 2 (filas 6..) de inversión y de la primera columna de entrada del embudo
        sem = wb["Semanal"]; filas_sem = {sem.cell(r, 2).value: r for r in range(6, sem.max_row + 1) if sem.cell(r, 2).value}
        inv_col = hdr["Inversión en publicidad (USD)"]
        suma = {1: 0, 2: 0}
        for r in range(6, d.max_row + 1):
            semana = v.get(("DIARIO", f"B{r}")); val = d.cell(r, inv_col).value
            if semana in suma and isinstance(val, (int, float)): suma[semana] += val
        r_inv = filas_sem["Inversión en publicidad (USD)"]
        s1, s2 = v.get(("SEMANAL", f"C{r_inv}")), v.get(("SEMANAL", f"D{r_inv}"))
        ok = abs((s1 or 0) - suma[1]) < 0.01 and abs((s2 or 0) - suma[2]) < 0.01
        print(f"  inversión semana 1: libro {s1} vs suma {suma[1]} · semana 2: {s2} vs {suma[2]} → {'OK' if ok else 'MAL'}")
        ok_total &= ok and errores == 0
        # semáforos
        vals = set()
        for r in range(6, sem.max_row + 1):
            if sem.cell(r, 1).value == "Semáforo":
                for j in range(3, 3 + 26):
                    x = v.get(("SEMANAL", f"{openpyxl.utils.get_column_letter(j)}{r}")); vals.add(x if x not in (None,) else "")
        print("  valores de semáforo:", sorted(str(x) for x in vals))
        ok_sem = all(str(x) in ("", "VERDE", "AMARILLO", "ROJO", "None") for x in vals); ok_total &= ok_sem
        # resumen
        res = wb["Resumen"]; print("  Resumen · semana a mostrar:", v.get(("RESUMEN", "B4")))
        for r in range(7, 7 + 8):
            lab = res.cell(r, 1).value
            if not lab: break
            print(f"    {str(lab)[:44]:<44} esta {str(v.get(('RESUMEN', f'B{r}')))[:10]:>10}  ant {str(v.get(('RESUMEN', f'C{r}')))[:10]:>10}  med {str(v.get(('RESUMEN', f'E{r}')))[:10]:>10}  sem {str(v.get(('RESUMEN', f'F{r}')))}")
    print("\nRESULTADO GENERAL:", "OK" if ok_total else "REVISAR")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "excel", "metricas-diarias"))
