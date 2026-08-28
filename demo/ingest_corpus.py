#!/usr/bin/env python3
"""
Ingests the public legal corpus into the demo RAG database (PostgreSQL public).
Processes documents in priority order so the most useful laws are available
first; runs with low priority (nice) to avoid starving the host.
"""
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "jurisconsultor", "app"))
sys.path.insert(0, os.path.join(ROOT, "jurisconsultor"))

from scripts.legal_scraper import process_single_document  # noqa: E402

LAWS_DIR = os.path.join(ROOT, "jurisconsultor", "documentos_legales")

# Priority order: constitutional rights first, then the most consulted codes.
ORDER = [
    "CPEUM.pdf",
    "CPEUM_REFORMA_15-04-2025.pdf",
    "codigo_civil_federal.pdf",
    "codigo_penal_federal.pdf",
    "codigo_fiscal_federal.pdf",
    "codigo_comercio_federal.pdf",
    "codigo_nacional_proc_civiles_y_familiares.pdf",
    "codigo_proc_civiles_federal.pdf",
    "codigo_proc_penales.pdf",
    "ley_migracion.pdf",
    "ley_Nacionalidad.pdf",
    "ley_proteccion_propiedad_industrial.pdf",
]


def main():
    start_all = time.time()
    for i, fname in enumerate(ORDER, 1):
        path = os.path.join(LAWS_DIR, fname)
        if not os.path.exists(path):
            print(f"[ingest] SKIP (not found): {fname}", flush=True)
            continue
        t0 = time.time()
        try:
            process_single_document(path, "public")
            print(f"[ingest] DONE ({i}/{len(ORDER)}): {fname} in {time.time()-t0:.0f}s", flush=True)
        except Exception as e:
            print(f"[ingest] ERROR on {fname}: {e}", flush=True)
    print(f"[ingest] ALL DONE in {time.time()-start_all:.0f}s", flush=True)


if __name__ == "__main__":
    main()
