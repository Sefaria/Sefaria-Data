# create_haftarot_csv.py
# -*- coding: utf-8 -*-

import django
django.setup()

from sefaria.model import *   # noqa: F401,F403
import re                     # noqa: F401 (included per your pattern)

import csv
import datetime as dt
from typing import List, Dict, Any

from convertdate import hebrew as hebcal
from sefaria.system.database import db
from sefaria.utils.hebrew import hebrew_parasha_name
from sefaria.utils.util import get_hebrew_date

# Columns in the CSV
FIELDNAMES = [
    "date_gregorian",
    "date_hebrew_en",
    "parasha_en",
    "parasha_he",
    "location",  # Israel / Diaspora
    "haftarah_ashkenazi",
    "haftarah_sephardi",
    # "haftarah_edot_hamizrach",
    "customs_available",  # which customs had data for that date
]

# Normalized custom keys found in data
CUSTOM_KEYS = ["ashkenazi", "sephardi",
               # "edot hamizrach"
               ]


def _in_hebrew_year(date_greg: dt.date, hy: int) -> bool:
    y, m, d = hebcal.from_gregorian(date_greg.year, date_greg.month, date_greg.day)
    return y == hy


def _hebrew_year_range_gregorian(hy: int) -> tuple[dt.datetime, dt.datetime]:
    # Start at 1 Tishrei HY, end is 1 Tishrei (HY+1) exclusive
    start_g = hebcal.to_gregorian(hy, 7, 1)       # Tishrei = 7
    end_g   = hebcal.to_gregorian(hy + 1, 7, 1)
    return dt.datetime(*start_g), dt.datetime(*end_g)


def _normalize_haftarah_field(haft) -> Dict[str, List[str]]:
    """
    Normalize haftarah field to: dict(custom -> list[str(normalized ref)])
    - If list: legacy style (assume Ashkenazi).
    - If dict: keys are customs; values may be str or list[str].
    """
    out: Dict[str, List[str]] = {k: [] for k in CUSTOM_KEYS}
    if not haft:
        return out

    src = {"ashkenazi": haft} if isinstance(haft, list) else haft
    for k, refs in src.items():
        if not refs:
            continue
        refs = refs if isinstance(refs, list) else [refs]
        try:
            out[k] = [Ref(r).normal() for r in refs]
        except Exception:
            out[k] = [str(r) for r in refs]
    return out


def _row_for_doc(doc, location_label: str) -> Dict[str, Any]:
    d = doc["date"]
    he_en, he_he = get_hebrew_date(d)  # english/hebrew formatted Hebrew date strings
    parasha_en = doc.get("parasha") or ""
    parasha_he = hebrew_parasha_name(parasha_en) or ""

    haft_by_custom = _normalize_haftarah_field(doc.get("haftara"))
    customs_available = [k for k in CUSTOM_KEYS if haft_by_custom.get(k)]

    return {
        "date_gregorian": d.strftime("%Y-%m-%d"),
        "date_hebrew_en": he_en,
        "parasha_en": parasha_en,
        "parasha_he": parasha_he,
        "location": location_label,
        "haftarah_ashkenazi": "; ".join(haft_by_custom.get("ashkenazi", [])),
        "haftarah_sephardi": "; ".join(haft_by_custom.get("sephardi", [])),
        # "haftarah_edot_hamizrach": "; ".join(haft_by_custom.get("edot hamizrach", [])),
        "customs_available": ", ".join(customs_available),
    }


def _build_rows(hebrew_year: int = 5786) -> List[Dict[str, Any]]:
    start, end = _hebrew_year_range_gregorian(hebrew_year)
    cur = db.parshiot.find({"date": {"$gte": start, "$lt": end}}).sort([("date", 1)])

    rows: List[Dict[str, Any]] = []
    for doc in cur:
        if not _in_hebrew_year(doc["date"].date(), hebrew_year):
            continue

        diaspora_val = doc.get("diaspora", None)  # None => applies to both
        if diaspora_val is True:
            rows.append(_row_for_doc(doc, "Diaspora"))
        elif diaspora_val is False:
            rows.append(_row_for_doc(doc, "Israel"))
        else:
            rows.append(_row_for_doc(doc, "Israel"))
            rows.append(_row_for_doc(doc, "Diaspora"))
    return rows


def write_csv(path: str = "haftarot_5786.csv", hebrew_year: int = 5786) -> None:
    rows = _build_rows(hebrew_year)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        w.writeheader()
        w.writerows(rows)


# When you run this file directly, it will create the CSV with defaults.
if __name__ == "__main__":
    write_csv()
