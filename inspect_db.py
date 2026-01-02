"""Quick script to inspect scraped data in SQLite."""
from __future__ import annotations

import json
import os
import sqlite3
import sys
from typing import Iterable

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "data", "51ca.db")

TABLE_CONFIG = {
    "news_articles": {
        "label": "News Articles",
        "columns": ["id", "title", "category", "url", "scraped_at"],
    },
    "house_listings": {
        "label": "House Listings",
        "columns": ["id", "title", "price", "location", "url"],
    },
    "job_listings": {
        "label": "Job Listings",
        "columns": ["id", "title", "company", "location", "url"],
    },
    "service_posts": {
        "label": "Service Posts",
        "columns": ["id", "title", "category", "location", "url"],
    },
    "service_merchants": {
        "label": "Service Merchants",
        "columns": ["id", "name", "category", "phone", "url"],
    },
    "market_posts": {
        "label": "Market Posts",
        "columns": ["id", "title", "price", "location", "url"],
    },
    "auto_listings": {
        "label": "Auto Listings",
        "columns": ["id", "title", "price", "mileage", "url"],
    },
}


def safe_text(value: object) -> str:
    """Return console-safe text."""
    text = "" if value is None else str(value)
    encoding = sys.stdout.encoding or "utf-8"
    return text.encode(encoding, errors="replace").decode(encoding, errors="replace")


def pretty_print_rows(rows: Iterable[sqlite3.Row], columns: list[str]) -> None:
    for row in rows:
        print("-" * 40)
        for column in columns:
            value = row[column]
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            print(f"{column:>12}: {safe_text(value)}")
    if not rows:
        print("(no rows)")


def main() -> None:
    if not os.path.exists(DB_PATH):
        raise SystemExit(f"Database not found at {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("=" * 60)
    print("SQLite snapshot for 51.ca scraper")
    print("DB:", DB_PATH)
    print("=" * 60)

    for table, cfg in TABLE_CONFIG.items():
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print()
        print(f"[{cfg['label']}] total rows: {count}")
        cursor.execute(
            f"SELECT {', '.join(cfg['columns'])} FROM {table} ORDER BY id DESC LIMIT 3"
        )
        rows = cursor.fetchall()
        pretty_print_rows(rows, cfg["columns"])

    print()
    print("URL queue status:")
    cursor.execute("SELECT COUNT(*) FROM url_queue WHERE visited = 0")
    pending = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM url_queue WHERE visited = 1")
    visited = cursor.fetchone()[0]
    print(f" pending: {pending}")
    print(f" visited: {visited}")

    conn.close()


if __name__ == "__main__":
    main()
