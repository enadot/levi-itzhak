# -*- coding: utf-8 -*-
"""
כלים משותפים לפרויקט מאגר "ביאור הגליון":
זיהוי כותרות, שמות פרשות, מיון חלקים, ניקוי שמות קבצים ולוגים בעברית.
"""

import re
import sys
import unicodedata
from pathlib import Path

CHANNEL_ID = "UCn70PgtpHOgCEbjWwuXz2-g"
CHANNEL_TABS = [
    f"https://www.youtube.com/channel/{CHANNEL_ID}/streams",
    f"https://www.youtube.com/channel/{CHANNEL_ID}/videos",
]

REPO_ROOT = Path(__file__).resolve().parent.parent
VIDEOS_ALL_PATH = REPO_ROOT / "videos_all.json"
CATALOG_PATH = REPO_ROOT / "catalog.json"
DOWNLOAD_ROOT = REPO_ROOT / "ביאור_הגליון"
INDEXES_DIR = REPO_ROOT / "indexes"

UNMATCHED_KEY = "_לא_משויך"


def log(msg: str) -> None:
    """לוג פשוט בעברית ל-stderr, עם flush מיידי."""
    print(msg, file=sys.stderr, flush=True)


# --- זיהוי סרטוני "ביאור הגליון" ---
# תופס: "ביאור הגליון", "ביאור גליון", "ביאור הגיליון" וכן וריאציות כתיב/מקף.
GILYON_RE = re.compile(r"ביאור[\s\-]+ה?גי{0,2}ל{1,2}יון")


def is_gilyon_title(title: str) -> bool:
    return bool(GILYON_RE.search(title or ""))


# --- שמות פרשות ---
# מיפוי וריאציית כתיב -> שם קנוני. הסדר הקנוני נקבע לפי TORAH_ORDER.
TORAH_ORDER = [
    "בראשית", "נח", "לך לך", "וירא", "חיי שרה", "תולדות", "ויצא", "וישלח",
    "וישב", "מקץ", "ויגש", "ויחי",
    "שמות", "וארא", "בא", "בשלח", "יתרו", "משפטים", "תרומה", "תצוה",
    "כי תשא", "ויקהל", "פקודי",
    "ויקרא", "צו", "שמיני", "תזריע", "מצורע", "אחרי מות", "קדושים", "אמור",
    "בהר", "בחוקותי",
    "במדבר", "נשא", "בהעלותך", "שלח", "קרח", "חוקת", "בלק", "פינחס",
    "מטות", "מסעי",
    "דברים", "ואתחנן", "עקב", "ראה", "שופטים", "כי תצא", "כי תבוא",
    "נצבים", "וילך", "האזינו", "וזאת הברכה",
]

PARSHA_VARIANTS = {
    "תולדת": "תולדות",
    "תצווה": "תצוה",
    "כי-תשא": "כי תשא",
    "תשא": "כי תשא",
    "מצרע": "מצורע",
    "אחרי-מות": "אחרי מות",
    "אחרי": "אחרי מות",
    "קדשים": "קדושים",
    "אמר": "אמור",
    "בחקתי": "בחוקותי",
    "בחוקתי": "בחוקותי",
    "בחקותי": "בחוקותי",
    "בהעלתך": "בהעלותך",
    "שלח לך": "שלח",
    "שלח-לך": "שלח",
    "קורח": "קרח",
    "חקת": "חוקת",
    "פנחס": "פינחס",
    "מטת": "מטות",
    "כי-תצא": "כי תצא",
    "כי תבא": "כי תבוא",
    "כי-תבוא": "כי תבוא",
    "ניצבים": "נצבים",
    "וזאת-הברכה": "וזאת הברכה",
    "לך-לך": "לך לך",
    "חיי-שרה": "חיי שרה",
}

# כל הווריאציות למעבר על כותרת: קנוני + חלופות
_ALL_VARIANTS = {name: name for name in TORAH_ORDER}
_ALL_VARIANTS.update(PARSHA_VARIANTS)

# ממויין מהארוך לקצר כדי ש"אחרי מות" ייתפס לפני "אחרי", "כי תצא" לפני "תצא" וכו'.
_VARIANTS_BY_LEN = sorted(_ALL_VARIANTS.items(), key=lambda kv: -len(kv[0]))


def detect_parsha(title: str) -> str | None:
    """
    מזהה את שם/שמות הפרשה מהכותרת.
    פרשות מחוברות (למשל "מטות-מסעי") מוחזרות כשמות מחוברים במקף לפי סדר התורה.
    מחזיר None אם לא זוהתה פרשה.
    """
    found: set[str] = set()
    remaining = title or ""
    for variant, canonical in _VARIANTS_BY_LEN:
        pattern = r"(?<![\wא-ת])" + re.escape(variant).replace(r"\ ", r"[\s\-]") + r"(?![\wא-ת])"
        if re.search(pattern, remaining):
            found.add(canonical)
            # מוחקים את ההתאמה כדי שוריאציה קצרה לא תתפוס שוב את אותו קטע
            remaining = re.sub(pattern, " ", remaining)
    if not found:
        return None
    ordered = sorted(found, key=TORAH_ORDER.index)
    return "-".join(ordered)


# --- מיון חלקים בתוך פרשה ---
_GEMATRIA = {
    "א": 1, "ב": 2, "ג": 3, "ד": 4, "ה": 5, "ו": 6, "ז": 7, "ח": 8, "ט": 9,
    "י": 10, "כ": 20, "ך": 20, "ל": 30, "מ": 40, "ם": 40, "נ": 50, "ן": 50,
    "ס": 60, "ע": 70, "פ": 80, "ף": 80, "צ": 90, "ץ": 90,
    "ק": 100, "ר": 200, "ש": 300, "ת": 400,
}


def gematria(letters: str) -> int:
    return sum(_GEMATRIA.get(ch, 0) for ch in letters)


_FRONT_PART_RE = re.compile(r"חלק\s+(?:ה?קדמי|קדמון)|(?<![\wא-ת])(?:קדמי|פתיחה|הקדמה)(?![\wא-ת])")
# "אות ב" / "אות ב'" / "אות ב-ג" / "אות ב'-ג'" / "אות יא"
_OT_RE = re.compile(
    r"אות\s+([א-ת]{1,3})['׳]?(?:\s*[-–־]\s*(?:אות\s+)?([א-ת]{1,3})['׳]?)?"
)


def parse_part(title: str) -> tuple[tuple[int, int, int], str]:
    """
    מחלץ מהכותרת את מפתח המיון של החלק ותווית קריאה.
    מחזיר (sort_key, label) כאשר sort_key הוא:
      (0, 0, 0)                  - חלק קדמי / פתיחה / הקדמה
      (1, גימטריה ראשונה, שנייה) - "אות X" או "אות X-Y"
      (2, 0, 0)                  - לא זוהה חלק (ימוין לפי תאריך)
    """
    t = title or ""
    if _FRONT_PART_RE.search(t):
        return (0, 0, 0), "חלק קדמי"
    m = _OT_RE.search(t)
    if m:
        first = gematria(m.group(1))
        second = gematria(m.group(2)) if m.group(2) else 0
        label = f"אות {m.group(1)}" + (f"-{m.group(2)}" if m.group(2) else "")
        return (1, first, second), label
    return (2, 0, 0), "לא זוהה"


def item_sort_key(item: dict) -> tuple:
    """מפתח מיון מלא לפריט בקטלוג: דרגת חלק, ואז תאריך/מזהה כשובר שוויון."""
    part_key = tuple(item.get("part_key") or parse_part(item.get("title", ""))[0])
    date_key = item.get("timestamp") or 0
    return (*part_key, date_key, item.get("upload_date") or "", item.get("id", ""))


# --- ניקוי שמות קבצים ---
_BAD_CHARS_RE = re.compile(r'[\\/:*?"<>|\'`׳״”“‘’\n\r\t]+')


def sanitize_filename(title: str, max_len: int = 80) -> str:
    """מנקה כותרת לשם קובץ בטוח: מסיר תווים בעייתיים, רווחים -> _, קיצוץ אורך."""
    name = unicodedata.normalize("NFC", title or "")
    name = _BAD_CHARS_RE.sub(" ", name)
    name = re.sub(r"\s+", "_", name.strip())
    name = name.strip("._-")
    if len(name) > max_len:
        name = name[:max_len].rstrip("._-")
    return name or "ללא_כותרת"
