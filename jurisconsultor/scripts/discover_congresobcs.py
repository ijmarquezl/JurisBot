#!/usr/bin/env python3
"""
Discovery para el sitio de leyes del Congreso de Baja California Sur (BCS).

El sitio (https://www.cbcs.gob.mx/index.php/trabajos-legislativos/leyes) es
Joomla: la lista contiene ~220 leyes con enlaces de detalle
    /index.php/trabajos-legislativos/leyes?layout=edit&id=<ID>
y cada página de detalle tiene el archivo de la ley (normalmente .doc legacy):
    /LEYES-BCS/<ARCHIVO>.doc   (también puede haber .pdf o .docx)

Este script hace un crawl de 2 niveles:
  1. Lista -> (id, nombre de la ley)
  2. Detalle -> URL del archivo (prefiere .pdf/.docx; cae a .doc)

Siembra fuentes con `pdf_direct_url` para que run_scraper() las ingiera.

Uso:
  python scripts/discover_congresobcs.py [--limit N] [--only "cadena"]
"""
import argparse
import logging
import os
import re
import sys
import time

import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from urllib.parse import urljoin

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

PAGE_URL = "https://www.cbcs.gob.mx/index.php/trabajos-legislativos/leyes"
SOURCES_COLLECTION = "scraping_sources"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}


def slugify(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", name).strip("_").lower()
    return s[:120] or "ley"


def _clean_name(text: str) -> str:
    """Normaliza el nombre: colapsa espacios y arregla 'C ÓDIGO' -> 'CÓDIGO'.
    Se conserva el texto original del sitio (no se cambia a título)."""
    name = re.sub(r"\s+", " ", text).strip()
    # Quita espacios raros dentro de palabras en mayúsculas (ej. "C ÓDIGO" -> "CÓDIGO")
    name = re.sub(r"\b([A-ZÁÉÍÓÚÑ])\s(?=[A-ZÁÉÍÓÚÑ]{2,})", r"\1", name)
    return name


def _find_file_url(detail_url: str):
    """En la página de detalle, encuentra el enlace al archivo de la ley (no reglamentos)."""
    try:
        resp = requests.get(detail_url, timeout=30, headers=HEADERS, verify=False)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        best = None
        for a in soup.find_all("a", href=True):
            href = a["href"].lower()
            if not (href.endswith(".pdf") or href.endswith(".doc") or href.endswith(".docx")):
                continue
            abs_url = urljoin(detail_url, a["href"])
            # Preferir archivos dentro de /LEYES-BCS/ (el reglamento está en /REGLAMENTOS/)
            if "leyes-bcs" in href:
                return abs_url
            if best is None:
                best = abs_url
        return best
    except Exception as e:
        logger.warning(f"  error en detalle {detail_url}: {e}")
        return None


def scrape_congresobcs(page_url: str = PAGE_URL, max_details: int = None):
    """Devuelve lista de dicts: {id, name, file_url}"""
    logger.info(f"Descargando lista {page_url}...")
    resp = requests.get(page_url, timeout=60, headers=HEADERS, verify=False)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    laws = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        m = re.search(r"[?&]id=(\d+)", href)
        if not m or "layout=edit" not in href:
            continue
        law_id = m.group(1)
        name = _clean_name(a.get_text(" ", strip=True))
        if not name or len(name) < 5:
            continue
        laws.append({"id": law_id, "name": name, "file_url": None})

    # Dedupe por id
    seen, unique = set(), []
    for l in laws:
        if l["id"] not in seen:
            seen.add(l["id"])
            unique.append(l)
    logger.info(f"Encontradas {len(unique)} leyes en la lista.")

    # Nivel 2: resolver el archivo en cada detalle (con pausa para no saturar al sitio)
    for i, law in enumerate(unique):
        detail = f"{page_url}?layout=edit&id={law['id']}"
        url = _find_file_url(detail)
        law["file_url"] = url
        if i % 25 == 0:
            logger.info(f"  resueltas {i}/{len(unique)}...")
        if max_details and i + 1 >= max_details:
            break
        time.sleep(0.4)
    ok = sum(1 for l in unique if l["file_url"])
    logger.info(f"Archivos resueltos: {ok}/{len(unique)}")
    return unique


def seed_sources(laws, mongo_uri, db_name, only=None, limit=None):
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=10000)
    db = client[db_name]
    col = db[SOURCES_COLLECTION]
    seeded = 0
    for law in laws:
        if only and only.lower() not in law["name"].lower():
            continue
        if not law["file_url"]:
            logger.info(f"  (sin archivo) {law['name'][:60]}")
            continue
        ext = os.path.splitext(law["file_url"].split("?")[0])[1].lower() or ".pdf"
        local_filename = f"bcs_{slugify(law['name'])}{ext}"
        col.update_one(
            {"name": law["name"], "url": PAGE_URL},
            {"$set": {
                "name": law["name"],
                "url": PAGE_URL,
                "pdf_direct_url": law["file_url"],
                "local_filename": local_filename,
                "scraper_type": "generic_html",
                "status": "active",
                "error_message": None,
            }},
            upsert=True,
        )
        seeded += 1
        logger.info(f"  [{seeded}] {law['name'][:60]} -> {local_filename}")
        if limit and seeded >= limit:
            break
    client.close()
    logger.info(f"Total sembradas/actualizadas: {seeded} fuentes en '{db_name}.{SOURCES_COLLECTION}'.")
    return seeded


def main():
    parser = argparse.ArgumentParser(description="Discovery de leyes de BCS")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--only", type=str, default=None)
    parser.add_argument("--max-details", type=int, default=None, help="Limita el crawl de detalles (pruebas)")
    args = parser.parse_args()

    mongo_uri = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017")
    db_name = os.getenv("MONGO_DB_NAME", "jurisbot_demo")

    laws = scrape_congresobcs(max_details=args.max_details)
    seeded = seed_sources(laws, mongo_uri, db_name, only=args.only, limit=args.limit)
    if seeded == 0:
        logger.warning("No se sembró ninguna fuente; revisa --only / --limit.")


if __name__ == "__main__":
    main()
