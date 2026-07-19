# מאגר שיעורי "ביאור הגליון" — הרב לוי יצחק שוב

כלים להורדה וסידור של סדרת השיעורים "ביאור הגליון" מערוץ היוטיוב
([UCn70PgtpHOgCEbjWwuXz2-g](https://www.youtube.com/channel/UCn70PgtpHOgCEbjWwuXz2-g/streams)),
כבסיס עתידי לבוט וואטסאפ להאזנה לשיעורים.

## דרישות

```bash
pip install yt-dlp
# וכן ffmpeg מותקן במערכת (apt-get install ffmpeg / brew install ffmpeg)
```

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
