#!/usr/bin/env python3
"""Genera los cuatro modelos financieros de embudos (.xlsx) en la carpeta de entregables.

Uso:  python3 build.py [carpeta_salida]
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mf_core import Builder
from mf_specs_a import LOW_TICKET, WEBINAR_GRATUITO
from mf_specs_b import LLAMADA, WEBINAR_PAGO

SPECS = [LOW_TICKET, WEBINAR_GRATUITO, LLAMADA, WEBINAR_PAGO]
DEFAULT_OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "excel"))


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUT
    os.makedirs(out, exist_ok=True)
    for spec in SPECS:
        path = os.path.join(out, spec["archivo"])
        Builder(spec).build(path)
        print("OK", path, f"{os.path.getsize(path)//1024} KB")


if __name__ == "__main__":
    main()
