# -*- coding: utf-8 -*-
"""
שלבים 5–6: הורדת השיעורים כ-MP3 לפי הקטלוג ובניית index.json לכל פרשה.

    python scripts/download_parsha.py --parsha נשא     # פרשה אחת
    python scripts/download_parsha.py --all             # כל הפרשות

idempotent: קובץ MP3 שכבר קיים (ולא ריק) לא יורד שוב.
"""

import argparse
import json
import shutil
import sys

import yt_dlp

from gilyon_common import (
    CATALOG_PATH, DOWNLOAD_ROOT, INDEXES_DIR, UNMATCHED_KEY,
    log, sanitize_filename,
)


def download_item(item: dict, dest_dir, order: int) -> dict | None:
    """מוריד שיעור אחד כ-MP3. מחזיר רשומת אינדקס, או None בכישלון."""
    base_name = f"{order:02d}_{sanitize_filename(item['title'])}"
    mp3_path = dest_dir / f"{base_name}.mp3"

    record = {
        "order": order,
        "title": item["title"],
        "video_id": item["id"],
        "url": f"https://www.youtube.com/watch?v={item['id']}",
        "mp3_file": mp3_path.name,
        "duration_seconds": item.get("duration"),
        "part_label": item.get("part_label"),
        "upload_date": item.get("upload_date"),
    }

    if mp3_path.exists() and mp3_path.stat().st_size > 0:
        log(f"   ⏭️  קיים, מדלג: {mp3_path.name}")
        return record

    opts = {
        "format": "bestaudio/best",
        "outtmpl": str(dest_dir / f"{base_name}.%(ext)s"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "128",
        }],
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "download_archive": str(dest_dir / ".downloaded.txt"),
    }
    log(f"   ⬇️  מוריד: {item['title']}")
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(record["url"], download=True)
        if info and info.get("duration"):
            record["duration_seconds"] = info["duration"]
    except Exception as exc:
        log(f"   ❌ נכשלה הורדת {item['id']}: {exc}")
        return None

    if not (mp3_path.exists() and mp3_path.stat().st_size > 0):
        log(f"   ❌ הקובץ {mp3_path.name} לא נוצר כמצופה")
        return None
    log(f"   ✅ הושלם: {mp3_path.name}")
    return record


def download_parsha(name: str, items: list[dict]) -> None:
    log(f"\n📖 פרשת {name} — {len(items)} שיעורים")
    dest_dir = DOWNLOAD_ROOT / name
    dest_dir.mkdir(parents=True, exist_ok=True)

    index_items = []
    failures = 0
    for item in items:
        record = download_item(item, dest_dir, item["order"])
        if record:
            index_items.append(record)
        else:
            failures += 1

    index = {"parsha": name, "items": index_items}
    index_path = dest_dir / "index.json"
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2),
                          encoding="utf-8")
    # עותק תחת indexes/ שנשמר ב-git גם כשתיקיית ה-MP3 לא נדחפת
    INDEXES_DIR.mkdir(exist_ok=True)
    shutil.copy(index_path, INDEXES_DIR / f"{name}.json")
    log(f"🗂️  index.json נכתב לפרשת {name} "
        f"({len(index_items)} שיעורים" + (f", {failures} כשלונות" if failures else "") + ")")


def main() -> int:
    parser = argparse.ArgumentParser(description="הורדת שיעורי ביאור הגליון כ-MP3")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--parsha", metavar="שם", help="הורדת פרשה בודדת")
    group.add_argument("--all", action="store_true", help="הורדת כל הפרשות")
    args = parser.parse_args()

    if not CATALOG_PATH.exists():
        log(f"❌ {CATALOG_PATH.name} לא קיים — הרץ קודם את scripts/build_catalog.py")
        return 1
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    parshiot = catalog["parshiot"]

    if args.parsha:
        if args.parsha not in parshiot:
            log(f"❌ פרשה \"{args.parsha}\" לא נמצאה בקטלוג. קיימות: "
                + ", ".join(parshiot.keys()))
            return 1
        targets = {args.parsha: parshiot[args.parsha]}
    else:
        targets = {n: it for n, it in parshiot.items() if n != UNMATCHED_KEY}
        skipped = len(parshiot) - len(targets)
        if skipped:
            log(f"ℹ️ מדלג על קבוצת \"{UNMATCHED_KEY}\" — יש לשייך ידנית")

    for name, items in targets.items():
        download_parsha(name, items)

    log("\n🏁 סיום.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
