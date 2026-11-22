# מאגר שיעורי "ביאור הגליון" — הרב לוי יצחק שוב

כלים להורדה וסידור של סדרת השיעורים "ביאור הגליון" מערוץ היוטיוב
([UCn70PgtpHOgCEbjWwuXz2-g](https://www.youtube.com/channel/UCn70PgtpHOgCEbjWwuXz2-g/streams)),
כבסיס עתידי לבוט וואטסאפ להאזנה לשיעורים.

## דרישות

- Python 3.10+
- ffmpeg (Windows: `winget install ffmpeg` · Mac: `brew install ffmpeg` · Linux: `apt install ffmpeg`)
- Node.js 20+ או deno — yt-dlp צריך סביבת JavaScript כדי לחלץ פורמטים מיוטיוב
  (Windows: `winget install OpenJS.NodeJS.LTS` · Mac: `brew install node`)

```bash
python -m pip install -U "yt-dlp[default]"
```

חשוב להתקין עם `python -m pip` (ולא `pip` לבד), כדי ש-yt-dlp יותקן לאותה
גרסת פייתון שמריצה את הסקריפטים.

## הרצה על המחשב האישי

```bash
git clone https://github.com/enadot/levi-itzhak.git
cd levi-itzhak
git checkout claude/torah-lessons-youtube-archive-ebgr2l
python scripts/download_parsha.py --parsha נשא   # פיילוט
python scripts/download_parsha.py --all           # כל השאר
```

`videos_all.json` ו-`catalog.json` כבר נמצאים בריפו, כך שאין צורך להריץ את
שלבים 1–2 שוב. ההורדה מדלגת על קבצים שכבר קיימים, כך שאפשר לעצור ולהמשיך.

## שלבי העבודה

```bash
# 1. משיכת רשימת כל הסרטונים מהערוץ (נשמר ל-videos_all.json כגיבוי)
python scripts/fetch_channel.py           # --refresh למשיכה מחדש

# 2. סינון "ביאור הגליון", קיבוץ לפי פרשה ומיון חלקים -> catalog.json
python scripts/build_catalog.py           # סיכום כל הפרשות
python scripts/build_catalog.py --show נשא  # הצגת פרשה אחת לבדיקה

# 3. הורדת MP3 + index.json לכל פרשה
python scripts/download_parsha.py --parsha נשא   # פרשה אחת (פיילוט)
python scripts/download_parsha.py --all           # כל הפרשות
```

כל השלבים idempotent — הרצה חוזרת מדלגת על מה שכבר קיים.

## עדכון אוטומטי

```bash
python scripts/update.py
```

מושך את רשימת הסרטונים מחדש, ממזג סרטונים חדשים ל-`videos_all.json` (התאריכים
הקיימים נשמרים), בונה את הקטלוג מחדש ומוריד רק שיעורים חסרים. אם שיעור חדש
נכנס באמצע פרשה, הקבצים שאחריו מקבלים מספור חדש בלי להוריד אותם שוב.
הלוג נשמר ב-`logs/update_YYYY-MM-DD.log`. אפשר לתזמן הרצה יומית ב-Task Scheduler.

## מבנה התוצרים

```
videos_all.json          # גיבוי רשימת כל סרטוני הערוץ
catalog.json             # הקטלוג המסונן והממוין לפי פרשות
indexes/<פרשה>.json      # עותק של index.json לכל פרשה (נשמר ב-git)
ביאור_הגליון/
  <פרשה>/
    index.json
    01_<כותרת>.mp3       # קבצי האודיו (לא נדחפים ל-git)
```

## סדר החלקים בכל פרשה

המיון (`parse_part` ב-`scripts/gilyon_common.py`) מבין את מבנה הסדרה:

1. חלק קדמי / פתיחה / הקדמה
2. אות א', אות ב', אות ב'-ג' וכו' — לפי ערך גימטרי של האות הראשונה
   (וטווח כמו "ב-ג" ממוין אחרי "ב" לבדה)
3. כותרות ללא חלק מזוהה — לפי תאריך העלאה

סרטוני "ביאור הגליון" שלא זוהתה בהם פרשה נאספים תחת `_לא_משויך` בקטלוג
ומדווחים בלוג — לשיוך ידני.
