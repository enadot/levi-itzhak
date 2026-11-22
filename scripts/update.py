# -*- coding: utf-8 -*-
"""
עדכון אוטומטי של המאגר: מושך סרטונים חדשים מהערוץ, מעדכן את הקטלוג
ומוריד רק את מה שחסר. מיועד להרצה מתוזמנת (למשל פעם ביום).

    python scripts/update.py

כל הפלט נכתב גם ל-logs/update_YYYY-MM-DD.log.
"""

import json
import sys
from datetime import datetime

from gilyon_common import CATALOG_PATH, REPO_ROOT, UNMATCHED_KEY, log
import gilyon_common
import build_catalog
import download_parsha
import fetch_channel

LOG_DIR = REPO_ROOT / "logs"


def catalog_ids() -> set[str]:
    if not CATALOG_PATH.exists():
        return set()
    cat = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    return {it["id"] for items in cat["parshiot"].values() for it in items}


def setup_file_log() -> None:
    """מכפיל את הלוג גם לקובץ, כדי שאפשר יהיה לבדוק הרצות מתוזמנות."""
    LOG_DIR.mkdir(exist_ok=True)
    log_file = (LOG_DIR / f"update_{datetime.now():%Y-%m-%d}.log").open(
        "a", encoding="utf-8")
    original = gilyon_common.log

    def tee(msg: str) -> None:
        original(msg)
        log_file.write(f"[{datetime.now():%H:%M:%S}] {msg}\n")
        log_file.flush()

    for module in (gilyon_common, build_catalog, download_parsha, fetch_channel,
                   sys.modules[__name__]):
        module.log = tee


def main() -> int:
    setup_file_log()
    from gilyon_common import log  # הגרסה שכותבת גם לקובץ
    log(f"\n===== עדכון מאגר {datetime.now():%Y-%m-%d %H:%M} =====")

    before = catalog_ids()

    if fetch_channel.fetch_all(refresh=True) is None:
        log("❌ משיכת רשימת הסרטונים נכשלה — העדכון הופסק")
        return 1

    catalog = build_catalog.build_catalog()
    new_ids = catalog_ids() - before

    if not new_ids:
        log("✅ אין שיעורים חדשים")
    else:
        log(f"🆕 {len(new_ids)} שיעורים חדשים:")
        for name, items in catalog["parshiot"].items():
            for it in items:
                if it["id"] in new_ids:
                    log(f"     {name}: {it['title']}")

    # מורידים רק פרשות שיש בהן משהו חדש או חסר
    failures = 0
    for name, items in catalog["parshiot"].items():
        if name == UNMATCHED_KEY:
            continue
        dest = download_parsha.DOWNLOAD_ROOT / name
        index_path = dest / "index.json"
        indexed = set()
        if index_path.exists():
            idx = json.loads(index_path.read_text(encoding="utf-8"))
            indexed = {it["video_id"] for it in idx["items"]}
        if {it["id"] for it in items} - indexed:
            failures += download_parsha.download_parsha(name, items)

    if failures:
        log(f"⚠️ הסתיים עם {failures} כשלונות — ינוסו שוב בהרצה הבאה")
        return 2
    log("🏁 העדכון הושלם")
    return 0


if __name__ == "__main__":
    sys.exit(main())
