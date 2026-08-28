#!/usr/bin/env python3
"""
Discovery para el sitio de leyes del Congreso de Baja California.

El sitio (https://www.congresobc.gob.mx/TrabajoLegislativo/Leyes) lista las
leyes del estado en filas con enlaces directos a archivos PDF/DOC organizados
por TOMOS:
    ../Documentos/ProcesoParlamentario/Leyes/TOMO_X/<ARCHIVO>.PDF

Formato de fila: "NOMBRE DE LA LEY DD/MM/YYYY VIGENTE TOMO_X"

Este script:
  1. Descarga la página y extrae (nombre -> URL del PDF).
  2. Crea/actualiza registros en `scraping_sources` con `pdf_direct_url`,
     de modo que `run_scraper()` (web_downloader) los descargue e ingiera.

Uso:
  python scripts/discover_congresobc.py [--limit N] [--only "cadena"]
"""
import argparse
import logging
import os
import re
import sys

import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from urllib.parse import urljoin

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

PAGE_URL = "https://www.congresobc.gob.mx/TrabajoLegislativo/Leyes"
SOURCES_COLLECTION = "scraping_sources"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}
# La fila termina con una fecha (AGS: DD/MM/YYYY; BC: YYYY/MM/DD) + "VIGENTE TOMO_X";
# el nombre es todo lo anterior a la fecha. Patrón flexible para ambos formatos.
DATE_RE = re.compile(r"^\s*(.*?)\s+(\d{1,4}/\d{1,2}/\d{1,4})\s+", re.IGNORECASE)


def slugify(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", name).strip("_").lower()
    return s[:120] or "ley"


def scrape_congresobc(page_url: str = PAGE_URL):
    """Devuelve lista de dicts: {name, pdf_url, doc_url, tomo}"""
    logger.info(f"Descargando {page_url}...")
    resp = requests.get(page_url, timeout=60, headers=HEADERS, verify=False)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    laws = []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        lower = href.lower()
        if not (lower.endswith(".pdf") or lower.endswith(".doc") or lower.endswith(".docx")):
            continue
        if "procesoparlamentario/leyes" not in lower and "leyes/" not in lower:
            continue
        pdf_url = urljoin(page_url, href)
        # Preferir el PDF sobre el DOC del mismo nombre
        if lower.endswith(".doc"):
            continue
        # Nombre desde el texto de la fila (sube hasta 3 niveles)
        name = None
        node = a
        for _ in range(3):
            node = node.parent
            if node is None:
                break
            row_text = node.get_text(" ", strip=True)
            m = DATE_RE.match(row_text)
            if m and len(m.group(1).strip()) > 5:
                name = m.group(1).strip()
                break
        if not name:
            name = os.path.splitext(os.path.basename(href))[0]
        key = name.upper()
        if key in seen:
            continue
        seen.add(key)
        tomo = re.search(r"TOMO_[A-Z]+", href, re.IGNORECASE)
        laws.append({
            "name": name,
            "pdf_url": pdf_url,
            "tomo": tomo.group(0).upper() if tomo else "",
        })
    logger.info(f"Encontradas {len(laws)} leyes.")
    return laws


def seed_sources(laws, mongo_uri, db_name, only=None, limit=None):
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=10000)
    db = client[db_name]
    col = db[SOURCES_COLLECTION]
    seeded = 0
    for law in laws:
        if only and only.lower() not in law["name"].lower():
            continue
        local_filename = f"bc_{slugify(law['name'])}.pdf"
        col.update_one(
            {"name": law["name"], "url": PAGE_URL},
            {"$set": {
                "name": law["name"],
                "url": PAGE_URL,
                "pdf_direct_url": law["pdf_url"],
                "local_filename": local_filename,
                "scraper_type": "generic_html",
                "status": "active",
                "error_message": None,
                "tomo": law.get("tomo"),
            }},
            upsert=True,
        )
        seeded += 1
        logger.info(f"  [{seeded}] {law['name'][:70]} -> {local_filename}")
        if limit and seeded >= limit:
            break
    client.close()
    logger.info(f"Total sembradas/actualizadas: {seeded} fuentes en '{db_name}.{SOURCES_COLLECTION}'.")
    return seeded


def main():
    parser = argparse.ArgumentParser(description="Discovery de leyes de Baja California")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--only", type=str, default=None)
    args = parser.parse_args()

    mongo_uri = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017")
    db_name = os.getenv("MONGO_DB_NAME", "jurisbot_demo")

    laws = scrape_congresobc()
    seeded = seed_sources(laws, mongo_uri, db_name, only=args.only, limit=args.limit)
    if seeded == 0:
        logger.warning("No se sembró ninguna fuente; revisa --only / --limit.")


if __name__ == "__main__":
    main()
