#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sella un PDF con la autoría de Jesús Tassarolo: marca de agua diagonal y pie en TODAS las páginas (estampado con pypdf)
y metadatos (autor, título, asunto, palabras clave, creador). El sello se dibuja con Chrome headless sobre fondo transparente.

Uso:  python3 sellar_pdf.py entrada.pdf [salida.pdf] [--titulo "..."] [--sin-diagonal]
"""
import os, sys, subprocess, tempfile, argparse
from pathlib import Path
from pypdf import PdfReader, PdfWriter
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "modelos_financieros")); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mf_comun import MARCA, AUTOR, VERSION, LICENCIA, MARCA_YOUTUBE, MARCA_INSTAGRAM

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def sello_pdf(w_pt, h_pt, diagonal=True):
    """Genera un PDF de una página, del tamaño dado, con fondo transparente, la marca diagonal y el pie."""
    wmm, hmm = w_pt * 25.4 / 72, h_pt * 25.4 / 72
    diag = (f'<div style="position:absolute;top:44%;left:-15%;width:130%;text-align:center;transform:rotate(-30deg);'
            f'font-size:44pt;font-weight:900;color:rgba(10,10,11,.055);letter-spacing:.02em">{AUTOR} · TooAudience</div>') if diagonal else ""
    html = f'''<!doctype html><html><head><meta charset="utf-8"><style>
@page {{ size: {wmm:.3f}mm {hmm:.3f}mm; margin: 0; }} html, body {{ margin: 0; padding: 0; background: transparent; }}
.pag {{ position: relative; width: {wmm:.3f}mm; height: {hmm:.3f}mm; overflow: hidden; font-family: Inter, -apple-system, Helvetica, Arial, sans-serif; }}
.pie {{ position: absolute; left: 17mm; right: 17mm; bottom: 7mm; font-family: "JetBrains Mono", Menlo, monospace; font-size: 6.8pt; color: #8C8C90; letter-spacing: .05em; text-transform: uppercase; display: flex; justify-content: space-between; gap: 6mm; }}
</style></head><body><div class="pag">{diag}<div class="pie"><span>{MARCA}</span><span>{VERSION}</span></div></div></body></html>'''
    d = tempfile.mkdtemp(); hp = os.path.join(d, "sello.html"); pp = os.path.join(d, "sello.pdf")
    open(hp, "w", encoding="utf-8").write(html)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-pdf-header-footer", "--default-background-color=00000000",
                    f"--print-to-pdf={pp}", Path(hp).resolve().as_uri()], check=True, capture_output=True)
    return pp


def sellar(entrada, salida=None, titulo=None, diagonal=True):
    salida = salida or entrada
    reader = PdfReader(entrada)
    writer = PdfWriter(clone_from=reader)   # clona el documento entero: conserva enlaces internos, destinos e índice
    sellos = {}
    for page in writer.pages:
        w, h = float(page.mediabox.width), float(page.mediabox.height)
        key = (round(w), round(h))
        if key not in sellos:
            sellos[key] = PdfReader(sello_pdf(w, h, diagonal)).pages[0]
        page.merge_page(sellos[key])
    meta = {"/Author": AUTOR, "/Creator": AUTOR + " · TooAudience", "/Producer": "TooAudience · " + VERSION,
            "/Subject": MARCA + " · " + LICENCIA, "/Keywords": AUTOR + ", TooAudience, modelo financiero, embudos, mastermind" + ((", Instagram " + MARCA_INSTAGRAM) if MARCA_INSTAGRAM else ""),
            "/Title": titulo or (reader.metadata.title if reader.metadata and reader.metadata.title else "Modelos financieros de embudos")}
    writer.add_metadata(meta)
    tmp = salida + ".tmp"
    with open(tmp, "wb") as f: writer.write(f)
    os.replace(tmp, salida)
    return salida, len(reader.pages)


def enlaces_internos(path):
    """Cuenta los enlaces internos (índice) y cuántos resuelven a una página."""
    r = PdfReader(path); total = ok = 0
    for i, page in enumerate(r.pages):
        for a in page.get("/Annots") or []:
            a = a.get_object()
            if a.get("/Subtype") != "/Link":
                continue
            dest = a.get("/Dest")
            if dest is None and a.get("/A") is not None:
                act = a["/A"].get_object()
                if act.get("/S") == "/GoTo": dest = act.get("/D")
            if dest is None:
                continue
            total += 1
            try:
                if isinstance(dest, str):
                    dest = r.named_destinations[dest]
                d = dest.get_object() if hasattr(dest, "get_object") else dest
                pg = d["/Page"] if hasattr(d, "keys") and "/Page" in d else d[0]
                if r.get_page_number(pg.get_object() if hasattr(pg, "get_object") else pg) >= 0: ok += 1
            except Exception:
                pass
    return total, ok


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("entrada"); ap.add_argument("salida", nargs="?"); ap.add_argument("--titulo"); ap.add_argument("--sin-diagonal", action="store_true")
    a = ap.parse_args(); antes = enlaces_internos(a.entrada); out, n = sellar(a.entrada, a.salida, a.titulo, not a.sin_diagonal); despues = enlaces_internos(out)
    print(f"sellado: {out} ({n} páginas) · enlaces internos: {antes[1]}/{antes[0]} antes, {despues[1]}/{despues[0]} después")
