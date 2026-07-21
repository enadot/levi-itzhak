# -*- coding: utf-8 -*-
"""
שלבים 3–4: סינון סרטוני "ביאור הגליון" מתוך videos_all.json,
קיבוץ לפי פרשה, מיון חלקים (חלק קדמי / אות א / אות ב / אות ב-ג...) ושמירה ל-catalog.json.

הצגת פרשה בודדת (למשל לפיילוט): python scripts/build_catalog.py --show נשא
"""

import argparse
import json
import sys

import yt_dlp

from gilyon_common import (
    CATALOG_PATH, TORAH_ORDER, UNMATCHED_KEY, VIDEOS_ALL_PATH,
    detect_parsha, is_gilyon_title, item_sort_key, log, parse_part,
    ydl_network_opts,
)


def enrich_dates(gilyon: list[dict], all_videos: list[dict]) -> None:
    """
    משלים תאריכים לסרטונים המסוננים בלבד (ב-flat-playlist אין תאריכים).
    התוצאה נשמרת חזרה ל-videos_all.json כמטמון קבוע — לא יימשך שוב בהרצה הבאה.
    """
    need = [v for v in gilyon if not v.get("timestamp") and not v.get("upload_date")]
    if not need:
        return
    log(f"🕐 משלים תאריכים ל-{len(need)} סרטונים (משיכת מטא-דאטה פרטנית)...")
    opts = {"quiet": True, "no_warnings": True, **ydl_network_opts()}
    done = 0
    with yt_dlp.YoutubeDL(opts) as ydl:
        for v in need:
            url = f"https://www.youtube.com/watch?v={v['id']}"
            try:
                info = ydl.extract_info(url, download=False)
            except Exception as exc:
                log(f"   ⚠️ לא נמשך תאריך עבור {v['id']}: {exc}")
                continue
            v["timestamp"] = info.get("release_timestamp") or info.get("timestamp")
            v["upload_date"] = info.get("upload_date")
            if info.get("duration"):
                v["duration"] = info["duration"]
            done += 1
    VIDEOS_ALL_PATH.write_text(
        json.dumps(all_videos, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log(f"   הושלמו תאריכים ל-{done}/{len(need)} ונשמרו ל-{VIDEOS_ALL_PATH.name}")


def build_catalog() -> dict:
    if not VIDEOS_ALL_PATH.exists():
        log(f"❌ {VIDEOS_ALL_PATH.name} לא קיים — הרץ קודם את scripts/fetch_channel.py")
        raise SystemExit(1)

    videos = json.loads(VIDEOS_ALL_PATH.read_text(encoding="utf-8"))
    log(f"📚 נטענו {len(videos)} סרטונים מ-{VIDEOS_ALL_PATH.name}")

    gilyon = [v for v in videos if is_gilyon_title(v.get("title", ""))]
    log(f"🔎 זוהו {len(gilyon)} סרטוני \"ביאור הגליון\" (על כל הווריאציות)")

    enrich_dates(gilyon, videos)

    parshiot: dict[str, list[dict]] = {}
    for v in gilyon:
        title = v.get("title", "")
        parsha = detect_parsha(title) or UNMATCHED_KEY
        part_key, part_label = parse_part(title)
        item = dict(v)
        item["part_key"] = list(part_key)
        item["part_label"] = part_label
        parshiot.setdefault(parsha, []).append(item)

    for parsha, items in parshiot.items():
        items.sort(key=item_sort_key)
        for i, item in enumerate(items, start=1):
            item["order"] = i

    unmatched = parshiot.get(UNMATCHED_KEY, [])
    if unmatched:
        log(f"⚠️ {len(unmatched)} סרטוני ביאור הגליון ללא פרשה מזוהה "
            f"(נשמרים תחת \"{UNMATCHED_KEY}\"):")
        for item in unmatched:
            log(f"     - {item['title']}")

    def parsha_order(name: str) -> tuple:
        if name == UNMATCHED_KEY:
            return (999,)
        first = name.split("-")[0]
        return (TORAH_ORDER.index(first) if first in TORAH_ORDER else 998,)

    catalog = {
        "channel_total_videos": len(videos),
        "gilyon_total": len(gilyon),
        "parshiot": {name: parshiot[name] for name in sorted(parshiot, key=parsha_order)},
    }
    CATALOG_PATH.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log(f"💾 הקטלוג נשמר אל {CATALOG_PATH.name} "
        f"({len(parshiot) - (1 if unmatched else 0)} פרשות)")
    return catalog


def show_parsha(catalog: dict, name: str) -> None:
    items = catalog["parshiot"].get(name)
    if not items:
        log(f"❌ לא נמצאה פרשה בשם \"{name}\" בקטלוג. פרשות קיימות:")
        log("   " + ", ".join(catalog["parshiot"].keys()))
        return
    print(f"\n=== פרשת {name} — {len(items)} שיעורים בסדר הבא ===")
    for item in items:
        dur = item.get("duration")
        dur_str = f"{int(dur // 60)} דק'" if dur else "?"
        print(f"{item['order']:>3}. [{item['part_label']}] {item['title']}"
              f"  ({item['id']}, {dur_str})")


def main() -> int:
    parser = argparse.ArgumentParser(description="בניית קטלוג ביאור הגליון")
    parser.add_argument("--show", metavar="פרשה",
                        help="הצגת הרשימה הממוינת של פרשה מסוימת")
    args = parser.parse_args()

    catalog = build_catalog()

    if args.show:
        show_parsha(catalog, args.show)
    else:
        print("\n=== סיכום פרשות ===")
        for name, items in catalog["parshiot"].items():
            print(f"  {name}: {len(items)} שיעורים")
    return 0


if __name__ == "__main__":
    sys.exit(main())
