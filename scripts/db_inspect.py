#!/usr/bin/env python
"""
DB inspection utility.

Usage:
    python scripts/db_inspect.py          # özet
    python scripts/db_inspect.py users    # tüm kullanıcılar
    python scripts/db_inspect.py interactions  # tüm puanlamalar
"""

import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "app.db"


def main() -> None:
    if not DB_PATH.exists():
        print(f"DB bulunamadı: {DB_PATH}")
        print("Backend'i bir kez çalıştır: uvicorn app.main:app --reload")
        return

    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    mode = sys.argv[1] if len(sys.argv) > 1 else "summary"

    if mode == "users":
        rows = cur.execute(
            "SELECT id, email, skin_type, skin_tone, undertone, created_at FROM users"
        ).fetchall()
        if not rows:
            print("Henüz kayıtlı kullanıcı yok.")
        for r in rows:
            print(dict(r))

    elif mode == "interactions":
        rows = cur.execute(
            "SELECT i.id, u.email, i.product_id, i.rating, i.created_at "
            "FROM interactions i JOIN users u ON u.id = i.user_id "
            "ORDER BY i.created_at DESC LIMIT 50"
        ).fetchall()
        if not rows:
            print("Henüz puanlama yok.")
        for r in rows:
            print(dict(r))

    else:
        # Özet
        print(f"\n{'='*50}")
        print(f"  DB: {DB_PATH}")
        print(f"{'='*50}")

        tables = cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        for (table,) in tables:
            count = cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            cols = [
                row[1]
                for row in cur.execute(f"PRAGMA table_info({table})").fetchall()
            ]
            print(f"\n  {table}  ({count} satır)")
            print(f"    sütunlar: {', '.join(cols)}")

        print(f"\n  Erişim için:")
        print(f"    sqlite3 {DB_PATH}")
        print(f"    veya: DB Browser for SQLite (GUI) — https://sqlitebrowser.org/")
        print()

    con.close()


if __name__ == "__main__":
    main()
