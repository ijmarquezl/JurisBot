#!/usr/bin/env python3
"""
Discovery para el sitio de leyes del Congreso de Aguascalientes.

El sitio (https://congresoags.gob.mx/agenda_legislativa/leyes) lista las leyes
del estado en filas con enlaces de descarga directa:
    /agenda_legislativa/leyes/descargarPdf/<id>   -> PDF
    /agenda_legislativa/leyes/descargarDoc/<id>   -> DOCX (visor Office)

Este script:
  1. Descarga la página y extrae (id -> nombre de ley).
  2. Crea/actualiza registros en la colección `scraping_sources` con
     `pdf_direct_url` (el enlace descargarPdf), de modo que `run_scraper()`
     (web_downloader) los descargue e ingiera por el flujo estándar.

Uso:
  python scripts/discover_congresoags.py [--limit N] [--only "cadena de nombre"]
Ejemplos:
  python scripts/discover_congresoags.py --limit 3
  python scripts/discover_congresoags.py --only "constitucion"
  python scripts/discover_congresoags.py               # todas (178)
"""
import argparse
import logging
import os
import re
import sys

import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

PAGE_URL = "https://congresoags.gob.mx/agenda_legislativa/leyes"
SOURCES_COLLECTION = "scraping_sources"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

# Patrón de la fila: "N NOMBRE DE LA LEY DD/MM/YYYY DD/MM/YYYY"
ROW_PATTERN = re.compile(r"^\s*\d+\s+(.*?)\s+(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})\s*$", re.IGNORECASE)


def slugify(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", name).strip("_").lower()
    return s[:120] or "ley"


def scrape_congresoags(page_url: str = PAGE_URL):
    """Devuelve lista de dicts: {id, name, pdf_url, doc_url}"""
    logger.info(f"Descargando {page_url}...")
    resp = requests.get(page_url, timeout=60, headers=HEADERS, verify=False)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    laws = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        m = re.search(r"descargarPdf/(\d+)", href)
        if not m:
            continue
        law_id = m.group(1)
        # El nombre de la ley está en el texto de la fila (abuelo del enlace)
        name = None
        row = a.parent.parent if a.parent and a.parent.parent else None
        if row:
            row_text = row.get_text(" ", strip=True)
            rm = ROW_PATTERN.match(row_text)
            if rm:
                name = rm.group(1).strip()
        if not name:
            name = f"Ley AGUASCALIENTES {law_id}"
        laws.append({
            "id": law_id,
            "name": name,
            "pdf_url": f"https://congresoags.gob.mx/agenda_legislativa/leyes/descargarPdf/{law_id}",
            "doc_url": f"https://congresoags.gob.mx/agenda_legislativa/leyes/descargarDoc/{law_id}",
        })
    # Dedupe por id manteniendo orden
    seen = set()
    unique = []
    for law in laws:
        if law["id"] not in seen:
            seen.add(law["id"])
            unique.append(law)
    logger.info(f"Encontradas {len(unique)} leyes.")
    return unique


def seed_sources(laws, mongo_uri, db_name, only=None, limit=None):
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=10000)
    db = client[db_name]
    col = db[SOURCES_COLLECTION]
    seeded = 0
    for law in laws:
        if only and only.lower() not in law["name"].lower():
            continue
        local_filename = f"ags_{slugify(law['name'])}.pdf"
        result = col.update_one(
            {"name": law["name"], "url": PAGE_URL},
            {"$set": {
                "name": law["name"],
                "url": PAGE_URL,
                "pdf_direct_url": law["pdf_url"],
                "local_filename": local_filename,
                "scraper_type": "generic_html",
                "status": "active",
                "error_message": None,
            }},
            upsert=True,
        )
        seeded += 1
        logger.info(f"  [{seeded}] {law['name']} -> {local_filename}")
        if limit and seeded >= limit:
            break
    client.close()
    logger.info(f"Total sembradas/actualizadas: {seeded} fuentes en '{db_name}.{SOURCES_COLLECTION}'.")
    return seeded


def main():
    parser = argparse.ArgumentParser(description="Discovery de leyes de Aguascalientes")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--only", type=str, default=None)
    args = parser.parse_args()

    mongo_uri = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017")
    db_name = os.getenv("MONGO_DB_NAME", "jurisbot_demo")

    laws = scrape_congresoags()
    seeded = seed_sources(laws, mongo_uri, db_name, only=args.only, limit=args.limit)
    if seeded == 0:
        logger.warning("No se sembró ninguna fuente; revisa --only / --limit.")


if __name__ == "__main__":
    main()
