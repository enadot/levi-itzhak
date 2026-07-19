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


def main() -> int:
    parser = argparse.ArgumentParser(description="משיכת רשימת הסרטונים מהערוץ")
    parser.add_argument("--refresh", action="store_true",
                        help="משיכה מחדש גם אם videos_all.json קיים")
    args = parser.parse_args()

    if VIDEOS_ALL_PATH.exists() and not args.refresh:
        existing = json.loads(VIDEOS_ALL_PATH.read_text(encoding="utf-8"))
        log(f"✅ {VIDEOS_ALL_PATH.name} כבר קיים ({len(existing)} סרטונים). "
            f"להרצה מחדש הוסף --refresh")
        return 0

    by_id: dict[str, dict] = {}
    for tab_url in CHANNEL_TABS:
        try:
            entries = fetch_tab(tab_url)
        except Exception as exc:
            log(f"⚠️ שגיאה במשיכת {tab_url}: {exc}")
            continue
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
            # שידור שמופיע בשתי לשוניות — משלימים שדות חסרים בלבד
            if vid in by_id:
                for k, v in record.items():
                    by_id[vid].setdefault(k, v)
                    if by_id[vid][k] is None and v is not None:
                        by_id[vid][k] = v
            else:
                by_id[vid] = record

    videos = list(by_id.values())
    if not videos:
        log("❌ לא נמשכו סרטונים כלל — כנראה בעיית רשת מול יוטיוב. לא שומר קובץ.")
        return 1

    VIDEOS_ALL_PATH.write_text(
        json.dumps(videos, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log(f"💾 נשמרו {len(videos)} סרטונים ייחודיים אל {VIDEOS_ALL_PATH.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
