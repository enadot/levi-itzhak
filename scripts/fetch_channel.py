# -*- coding: utf-8 -*-
"""
שלב 2: משיכת רשימת כל הסרטונים מהערוץ (flat-playlist) ושמירה ל-videos_all.json.

הרצה חוזרת לא מושכת שוב אם הקובץ קיים — אלא אם מועבר --refresh.
"""

import argparse
import json
import sys

import yt_dlp

from gilyon_common import CHANNEL_TABS, VIDEOS_ALL_PATH, log


def fetch_tab(url: str) -> list[dict]:
    """מושך רשימה שטוחה של סרטונים מלשונית אחת של הערוץ."""
    opts = {
        "extract_flat": "in_playlist",
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
    }
    log(f"📥 מושך רשימת סרטונים מ: {url}")
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    entries = [e for e in (info.get("entries") or []) if e]
    log(f"   נמצאו {len(entries)} סרטונים בלשונית זו")
    return entries


def fetch_all(refresh: bool = False) -> list[dict] | None:
    """
    מושך את רשימת הסרטונים וממזג עם videos_all.json הקיים:
    סרטונים קיימים שומרים את התאריכים שהושלמו, כותרות מתעדכנות, סרטונים חדשים נוספים.
    מחזיר את הרשימה המלאה, או None אם המשיכה נכשלה.
    """
    existing: list[dict] = []
    if VIDEOS_ALL_PATH.exists():
        existing = json.loads(VIDEOS_ALL_PATH.read_text(encoding="utf-8"))
        if not refresh:
            log(f"✅ {VIDEOS_ALL_PATH.name} כבר קיים ({len(existing)} סרטונים). "
                f"להרצה מחדש הוסף --refresh")
            return existing

    by_id: dict[str, dict] = {v["id"]: dict(v) for v in existing if v.get("id")}
    fetched_any = False
    new_count = 0
    for tab_url in CHANNEL_TABS:
        try:
            entries = fetch_tab(tab_url)
        except Exception as exc:
            log(f"⚠️ שגיאה במשיכת {tab_url}: {exc}")
            continue
        fetched_any = fetched_any or bool(entries)
        for e in entries:
            vid = e.get("id")
            if not vid:
                continue
            record = {
                "id": vid,
                "title": e.get("title"),
                "url": e.get("url") or f"https://www.youtube.com/watch?v={vid}",
                "duration": e.get("duration"),
                "upload_date": e.get("upload_date"),
                "timestamp": e.get("timestamp"),
            }
            if vid not in by_id:
                by_id[vid] = record
                new_count += 1
                continue
            current = by_id[vid]
            if record["title"]:
                current["title"] = record["title"]
            for k, v in record.items():
                if current.get(k) is None and v is not None:
                    current[k] = v

    if not fetched_any:
        log("❌ לא נמשכו סרטונים כלל — כנראה בעיית רשת מול יוטיוב. הקובץ לא שונה.")
        return None

    videos = list(by_id.values())
    VIDEOS_ALL_PATH.write_text(
        json.dumps(videos, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log(f"💾 {VIDEOS_ALL_PATH.name}: {len(videos)} סרטונים ({new_count} חדשים)")
    return videos


def main() -> int:
    parser = argparse.ArgumentParser(description="משיכת רשימת הסרטונים מהערוץ")
    parser.add_argument("--refresh", action="store_true",
                        help="משיכה מחדש ומיזוג סרטונים חדשים לקובץ הקיים")
    args = parser.parse_args()
    return 0 if fetch_all(args.refresh) is not None else 1


if __name__ == "__main__":
    sys.exit(main())
