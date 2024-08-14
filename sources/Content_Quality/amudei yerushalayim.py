
from sources.functions import *
enDesc = "Amudei Yerushalayim is a 19th-century commentary on the Jerusalem Talmud by Rabbi Yisrael Eisenstein, a part of which was originally printed together with the author’s responsa, Amudei Esh. It consists of detailed analysis, incorporating positions of earlier commentators."
heDesc = "״עמודי ירושלים״ הוא פירוש מהמאה ה-19 לתלמוד הירושלמי מאת רבי ישראל אייזנשטיין, שחלקו נדפס במקור יחד עם שו""ת הלכתי של המחבר - ״עמודי אש״. הוא מורכב מניתוח מפורט של הטקסט התלמודי, תוך שילוב עמדות של פרשנים קודמים."
pubDate = [1880]
pubPlace = "Lviv"
author = 'yisrael-eisenstein'
for b in library.get_indices_by_collective_title("Amudei Yerushalayim"):
    if "Jerusalem Talmud" in b:
        b = library.get_index(b)
        b.enDesc = enDesc
        b.authors = [author]
        b.pubDate = pubDate
        b.pubPlace = pubPlace
        b.heDesc = heDesc
        b.save(override_dependencies=True)
