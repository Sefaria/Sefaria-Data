# -*- coding: utf-8 -*-

import re
import django
import unicodecsv
from functools import reduce
django.setup()
from collections import defaultdict
from tqdm import tqdm
from sefaria.model import *
from sefaria.utils.hebrew import strip_cantillation, gematria, has_cantillation
from sefaria.system.exceptions import InputError
from linking_utilities.citation_disambiguator.citation_disambiguator import CitationDisambiguator

# TODO figure out how to map mekhilta


def init_midrash_books():
    easy_midrash = {
        "בר\"ר": "בראשית רבה",
        "שמו\"ר": "שמות רבה",
        "ויק\"ר": "ויקרא רבה",
        "במ\"ר": "במדבר רבה",
        "דב\"ר": "דברים רבה",
        "רו\"ר": "רות רבה",
        "קה\"ר": "קוהלת רבה",
        "איכ\"ר": "איכה רבה",
        "אסת\"ר": "אסתר רבה",
        "פדר\"כ": "פסיקתא דרב כהנא",
        "ספרי במדבר": "ספרי במדבר",
        "ספרי דברים": "ספרי דברים",
        'אדר"נ, נו"א,': 'אבות דרבי נתן',
        'אדר"נ, נו"ב,': 'אבות דרבי נתן',
        "מד\"ת": 'מדרש תהילים',
        "מדמ\"ש": 'מדרש משלי',
        "פדר\"א": 'פרקי דרבי אליעזר',
        "סדר עולם רבה": "סדר עולם רבה"
    }
    possibly_inaccurate_midrash = {
        "סא\"ר": "תנא דבי אליהו רבה",
        "סא\"ז": "תנא דבי אליהו זוטא, סדר אליהו זוטא",  # numbering goes past 15. seems to go into other additions to the book
        "דרך ארץ": "מסכת דרך ארץ רבה",  # numbering seems consistently behind by 2 perakim
        "פס\"ר": "פסיקתא רבתי",  # seems accurate to the section but not the segment
    }
    lapassuk_dict = {
        'מדרש תהילים': "תהילים",
        "קוהלת רבה": "קהלת",
        "איכה רבה": "איכה",
        'מדרש משלי': 'משלי',
        "שיר השירים רבה": 'שיר השירים',
        "מכילתא דרשב\"י": 'שמות',
    }
    needs_disambiguation = {
        "מדרש תמורה": "אוצר מדרשים, מדרש תמורה"
    }
    otzar_midrashim = {
        "מדרש תמורה": "אוצר מדרשים, מדרש תמורה",
        "מדרש לחנוכה": "אוצר מדרשים, מדרשים על חנוכה, מדרש לחנוכה",
        "מדרש יונה": "אוצר מדרשים, מדרשים על ספר יונה, (מדרש יונה (מפרקי דר\"א",  # note, typo in parens apparently exists in actual title
        "חנוך הוא מטטרון": "אוצר מדרשים, מטטרון - חנוך א",  # this ref is impossible to parse because it has a dash in it
        "אלפא ביתא דבן סירא": "אוצר מדרשים, אלפא ביתא דבן סירא, אלפא ביתא אחרת לבן סירא",
        "מסכת גיהינום": "אוצר מדרשים, גן עדן; גיהנם, מסכת גיהנם",
        "מדרש עשרת הדיברות": "אוצר מדרשים, מדרש עשרת הדברות",
        "קדושת ברכו ליחיד": "אוצר מדרשים, קדושא, קדושת ברכו ליחיד"

    }
    midrash_dict = {
        "מכילתא דר\"י": "Mekhilta d'Rabbi Yishmael",  # TODO seems to also be able to use pasuk as sections
        "לק\"ט": None,  # category + we don't have lekach tov on Torah yet
        "מד\"ש": None,  # Midrash Shmuel, I believe. We don't have it
        "ילקוט לשה\"ש": "Yalkut Shimoni on Nach, Shir HaShirim",  # appears once
        "ספרא": "Sifra",  # TODO
        "אג\"ב": "UNKNOWN",
        "מד\"א": "Midrash Agada",  # appears four times
    }
    talmud = library.get_indexes_in_category("Bavli", full_records=True)
    for t in talmud:
        midrash_dict[t.get_title("he")] = t.title

    mishnah = library.get_indexes_in_category("Mishnah", full_records=True)
    mishnah_dict = {}
    for m in mishnah:
        he = m.get_title("he").replace("משנה ", "")
        en = m.title.replace("Mishnah ", "")
        mishnah_dict[he] = en

    minor = library.get_indexes_in_category("Minor Tractates", full_records=True)
    minor_dict = {}
    for m in minor:
        he = m.get_title("he").replace("מסכת ", "")
        en = m.title.replace("Tractate ", "")
        minor_dict[he] = en

    return midrash_dict, mishnah_dict, minor_dict, easy_midrash, possibly_inaccurate_midrash, otzar_midrashim, lapassuk_dict


def parse_ref(tref, source):
    tref = tref.strip()
    try:
        if re.match(r"שם,? ", tref):
            return None
        if "הסכוליון" in tref:
            # not sure what this text is
            return None
        if any([re.match(k, tref) for k in list(OTZAR_MIDRASH.keys())]):
            replacer = None
            for k, v in list(OTZAR_MIDRASH.items()):
                if re.match(k, tref):
                    replacer = k
                    break
            tref = OTZAR_MIDRASH[replacer]  # simply replace. needs to be disambiguated
        elif 'שהש"ר' in tref:
            print('yo')
            return Ref("שיר השירים רבה")
        elif "ירושלמי" in tref:
            replacement_mesechtot = {
                "תרומה": "תרומות",
                "כלאיים": "כלאים",
            }
            for k, v in list(replacement_mesechtot.items()):
                tref = tref.replace(" {} ".format(k), " {} ".format(v))
            titles = library.get_titles_in_string(tref)
            if len(titles) > 0:
                return Ref(titles[0])
        elif "תוספתא" in tref:
            return Ref(tref)
        elif re.search(' \u05e2(?:"|\'\')[\u05d0\u05d1]', tref):
            # talmud
            tref = re.sub(r",? ?\u05e2(?:\"|'')\u05d0", '.', tref)
            tref = re.sub(r",? ?\u05e2(?:\"|'')\u05d1", ':', tref)
            if re.search(r"[\u2014\-]", tref):
                tref1, tref2 = re.split(r"[\u2014\-]", tref)
                oref1 = Ref(tref1)
                oref2 = Ref((tref1[:-1] + tref2) if tref2 == ':' else (oref1.index.get_title("he") + " " + tref2))
                oref = oref1.to(oref2)
            else:
                oref = Ref(tref)
            return oref
        elif any([t in tref for t in list(MISHNAH.keys())]):
            # mishnah
            return Ref("{} {}".format("משנה", tref))
        elif any([t in tref for t in list(MINOR.keys())]):
            # minor tractates
            tref = "{} {}".format("מסכת", tref) if "מסכת" not in tref else tref
            return Ref(tref)
        elif any([t in tref for t in list(EASY_MIDRASH.keys())]):
            # midrash rabbah
            replacer = None
            replacement = None
            for t, r in list(EASY_MIDRASH.items()):
                if t in tref:
                    replacer = t
                    replacement = r
                    break
            tref = tref.replace(replacer, replacement)
            tref = tref.replace("איכה רבה פתיחתא", "איכה רבה, פתיחתא")
        elif any([t in tref for t in list(INACCURATE_MIDRASH.keys())]):
            replacer = None
            replacement = None
            for t, r in list(INACCURATE_MIDRASH.items()):
                if t in tref:
                    replacer = t
                    replacement = r
                    break
            tref = tref.replace(replacer, replacement)
        elif re.match(r"^\u05ea\u05e0\u05d7\u05d5\u05de\u05d0(?P<buber>(?: \u05d1\u05d5\u05d1\u05e8)?) (?P<parsha>[\u05d0-\u05ea ]+), ", tref):
            # midrash tanchuma
            tref = re.sub(r"^\u05ea\u05e0\u05d7\u05d5\u05de\u05d0(?P<buber>(?: \u05d1\u05d5\u05d1\u05e8)?) (?P<parsha>[\u05d0-\u05ea ]+), ", r"\u05ea\u05e0\u05d7\u05d5\u05de\u05d0\g<buber>, \g<parsha>, ", tref)
            replacement_parshas = {
                "תצווה": "תצוה",
                "חוקת": "חקת",
                "קורח": "קרח",
                "ניצבים": "נצבים",
                "נשוא": "נשא",
                "בחוקותי": "בחוקתי",
                "פינחס": "פנחס",
                "אחרי": "אחרי מות",
                "שלח לך": "שלח",
                "כי תישא": "כי תשא"
            }
            for k, v in list(replacement_parshas.items()):
                tref = tref.replace(" {}, ".format(k), " {}, ".format(v))
            if "הוספה " in tref:
                tref = re.sub(" (?P<parsha>[\u05d0-\u05ea ]+), (?P<hosafa>\u05d4\u05d5\u05e1\u05e4\u05d4)", " \g<hosafa> \u05dc\g<parsha>", tref)
        elif re.match(r"מכילתא דר\"י", tref):
            matches = [x for x in library.get_refs_in_string(source, "he", citing_only=True) if x.index.get_title("en") == "Exodus" and 12 <= x.sections[0] <= 35]
            if len(matches) > 0:
                my_passuk = matches[0].he_normal()
                tref = my_passuk.replace("שמות", "מכילתא דרבי ישמעאל")
            else:
                pass
                # print "NO EXODUS"

        elif re.match(r'\u05d9\u05dc\u05e7"\u05e9 ', tref):
            # yalkut shimoni
            match = re.match(r'\u05d9\u05dc\u05e7"\u05e9 \u05dc(?P<parsha>[\u05d0-\u05ea ]+(?: [\u05d0\u05d1])?),? ', tref)
            if not match:
                raise InputError
            book = match.groupdict()['parsha']
            if book == "שמואל":
                book = "שמואל א"
            elif book == "מלכים":
                book = "מלכים א"
            elif book == "דברי הימים":
                book = "דברי הימים א"
            index = library.get_index(book)
            if len(index.categories) > 1 and index.categories[0] == "Tanakh":
                if index.categories[1] == "Torah":
                    replacer = "על התורה"
                else:
                    replacer = "על נ\"ך"
            else:
                raise InputError
            tref = re.sub(r'\u05d9\u05dc\u05e7"\u05e9 \u05dc(?P<parsha>[\u05d0-\u05ea ]+(?: [\u05d0\u05d1])?),? ', '\u05d9\u05dc\u05e7\u05d5\u05d8 \u05e9\u05de\u05e2\u05d5\u05e0\u05d9 {} '.format(replacer), tref)
        if "לפסוק" in tref:
            for k, book in list(LAPASUK.items()):
                if k in tref:
                    matches = [x for x in library.get_refs_in_string(source, "he", citing_only=True) if x.index.get_title("he") == book]
                    # TODO deal with more than one match
                    if len(matches) > 0:
                        my_passuk = matches[0].he_normal()
                        tref = my_passuk.replace(book, k)
                    else:
                        # print u"NO MATCHES"
                        print(tref)
                    break

        return Ref(tref)
    except InputError:
        # print u"BADNESS"
        print(tref)
    except IndexError:
        # print u"BADNESS INDEX"
        print(tref)


def is_filler_midrash_word(word):
    is_hashem = re.match(r"\s*\u05d4[\u05f3'][\":;!?,.—()״׳]*$", word) is not None
    is_gomer = re.match(r"\s*\u05d5?\u05d2\u05d5[\u05f3']?[\":;!?,.—()״׳]*$", word) is not None
    return is_hashem or is_gomer


def get_midrashic_text(text):
    """
    Given text, removes commentary text and returns midrashic text
    If it determines text is all commentary, returns empty string
    :param text:
    :return:
    """
    dash = "—"
    words = text.split()
    if len(words) == 0:
        return "", ""
    midrash_words = 0.0
    filler_words = 0.0
    curr_non_midrash_start = None
    curr_midrash_start = None
    in_paren = False
    potential_non_midrash_span = None
    non_midrash_spans = []
    for i, w in enumerate(words):
        if "(" in w:
            in_paren = True
        if in_paren or re.match(r"^[^\u05d0-\u05ea]+$", w):
            if w.strip() == dash and curr_midrash_start is not None:
                potential_non_midrash_span = (curr_midrash_start, i+1)
            filler_words += 1
        elif has_cantillation(w, detect_vowels=True) or is_filler_midrash_word(w):
            if curr_non_midrash_start is not None:
                non_midrash_spans += [(curr_non_midrash_start, i)]
            curr_non_midrash_start = None
            potential_non_midrash_span = None
            if curr_midrash_start is None:
                curr_midrash_start = i
            midrash_words += 1
        else:
            curr_midrash_start = None
            if curr_non_midrash_start is None:
                if potential_non_midrash_span is not None:
                    potential_non_midrash_span_len = potential_non_midrash_span[1] - potential_non_midrash_span[0]
                    if potential_non_midrash_span_len <= 8:
                        non_midrash_spans += [potential_non_midrash_span]
                    potential_non_midrash_span = None
                curr_non_midrash_start = i
        if ")" in w:
            in_paren = False
        if re.search(r"\.\s*$", w) and not re.search(r"\.\.\.\s*$", w):
            # period means end of potential non midrash span
            curr_midrash_start = None
    if curr_non_midrash_start is not None:
        non_midrash_spans += [(curr_non_midrash_start, len(words))]
    actual_len = len(words) - filler_words
    non_midrash_words = reduce(lambda a, b: a + (b[1]-b[0]), non_midrash_spans, 0)
    cutoff = 0.7 if actual_len < 20 else 0.8
    if actual_len <= 0:
        return "", text
    if (non_midrash_words / actual_len) > cutoff:
        return "", text
    if len(non_midrash_spans) == 0:
        return text, ""
    midrashic_text = ""
    commentary_text = ""
    last_end = 0
    for s, e in non_midrash_spans:
        midrashic_text += " ".join(words[last_end:s])
        commentary_text += " ".join(words[s:e])
        last_end = e
    midrashic_text += " ".join(words[last_end:])
    return midrashic_text, commentary_text


def disambiguate_all(source_list):
    ref_map = defaultdict(list)
    source_dict_map = {}

    def make_key(source_dict):
        return "{}|{}|{}".format(source_dict["chapter_name"], source_dict["topic_name"], source_dict["source_num"])
    for source_dict in source_list:
        key = make_key(source_dict)
        if key in source_dict_map:
            print("AHHHHHH")
        source_dict_map[key] = source_dict
        for oref in source_dict["ref_list"]:
            ref_map[oref.normal()] += [(source_dict["source"], key)]

    for tref, temp_source_list in tqdm(list(ref_map.items())):
        results = disambiguate_ref_list(tref, temp_source_list)
        for key, result in list(results.items()):

            source_dict = source_dict_map[key]

            if "good_ref_list" not in source_dict:
                source_dict["good_ref_list"] = []
                source_dict["bad_ref_list"] = []
            if result is None:
                source_dict["bad_ref_list"] += [Ref(tref)]
            else:
                source_dict["good_ref_list"] += [Ref(result["A Ref"])]
    return source_list


def disambiguate_ref_list(main_tref, tref_list, **kwargs):
    """
    Find exact segment refs of main_tref for each tref in tref_list.
    :param main_tref: str which is a textual ref
    :param tref_list: list, each item could be either tuple of form (str, key) or a str which is a textual ref
    :return: dict where key is key and value is {"A Ref": tref, "B Ref": tref or key, "Score": float}. "A Ref" will be the disambiguagted ref for main_tref. value will be None if no result was found
    """
    ld = CitationDisambiguator()
    results = ld.disambiguate_segment_by_snippet(main_tref, tref_list, **kwargs)
    return results


def make_parsed_source(chapter_name, chapter_num, topic_name, topic_num, source_num, prev_rows):
    global TOTAL_REFS, PARSED_REFS
    source, commentary = "", ""
    for r in prev_rows:
        s, c = get_midrashic_text(r["source"])
        source += s
        commentary += c
    m = re.search(r"\(([^)]+)\)\s*\.?\s*\$?\s*$", source)
    if m is None:
        print("OH NO -- {} {} {}: {}".format(chapter_num, topic_num, source_num, topic_name))
        print(strip_cantillation(source, strip_vowels=True)[-20:])
        return None
    else:
        source = re.sub(r"\(([^)]+)\)\s*\.?\s*\$?\s*$", "", source)
        ref_list = [parse_ref(r, source) for r in re.split(r"[:;]", m.group(1))]
        TOTAL_REFS += len(ref_list)
        PARSED_REFS += len([_f for _f in ref_list if _f])
    return {
        "chapter_name": chapter_name,
        "chapter_num": chapter_num,
        "topic_name": topic_name,
        "topic_num": topic_num,
        "source_num": source_num,
        "source": source,
        "commentary": commentary,
        "ref_list": [_f for _f in ref_list if _f]
    }


def update_chapter(row):
    if len(row["chapter"]) > 0:
        m = re.match(r"\u05e4\u05e8\u05e7 ([\u05d0-\u05ea]{1,3}) (.+)$", row["chapter"])
        if m is None:
            print(row)
            return None
        chapter_num = gematria(m.group(1))
        chapter_name = m.group(2)
        return chapter_name, chapter_num
    else:
        return None


def update_topic(row):
    if len(row["topic"]) > 0:
        m = re.match(r"([\u05d0-\u05ea]{1,4})\. (.+)$", row["topic"])
        if m is None:
            print(row)
            return None
        topic_num = gematria(m.group(1))
        topic_name = m.group(2)
        return topic_name, topic_num
    else:
        return None


def open_csv():
    sources = []
    curr_chapter_name, curr_chapter_num, curr_topic_name, curr_topic_num, curr_source_num, curr_source, prev_rows = None, 0, None, 0, 0, None, []
    with open("sefer_haagada.csv", "rb") as fin:
        csv = unicodecsv.DictReader(fin)
        for row in csv:
            # if len(sources) >= 30:
            #     break
            if len(row["sourceNum"]) > 0:
                if len(prev_rows) > 0:
                    sources += [make_parsed_source(curr_chapter_name, curr_chapter_num, curr_topic_name, curr_topic_num, curr_source_num, prev_rows)]
                    prev_rows = []
            # update chapter
            new_chapter = update_chapter(row)
            if new_chapter:
                if new_chapter[1] != curr_chapter_num + 1:
                    print("{} <= {} {}".format(new_chapter[1], curr_chapter_num, curr_chapter_name))
                curr_chapter_name, curr_chapter_num = new_chapter
                curr_topic_num = 0
                curr_source_num = 0
            # update topic
            new_topic = update_topic(row)
            if new_topic:
                if new_topic[1] != curr_topic_num + 1:
                    print("{} <= {} {}".format(new_topic[1], curr_topic_num, curr_topic_name))
                curr_topic_name, curr_topic_num = new_topic
            # update source num
            if len(row["sourceNum"]) > 0:
                new_source_num = gematria(row["sourceNum"])
                if new_source_num != curr_source_num + 1:
                    print("yoyoyo {} <= {} {} -- {}".format(new_source_num, curr_source_num, curr_topic_name, curr_topic_num))
                curr_source_num = new_source_num

            prev_rows += [row]
        if len(prev_rows) > 0:
            sources += [make_parsed_source(curr_chapter_name, curr_chapter_num, curr_topic_name, curr_topic_num, curr_source_num, prev_rows)]
    sources = [_f for _f in sources if _f]
    sources = disambiguate_all(sources)
    with open("parsed.csv", "wb") as fout:
        csv = unicodecsv.DictWriter(fout, ["chapter_name", "chapter_num", "topic_name", "topic_num", "source_num", "source", "commentary", "good_ref_list", "bad_ref_list", "ref_list"])
        csv.writeheader()
        for s in sources:
            s["ref_list"] = ", ".join([r.normal() for r in s.get("ref_list", [])])
            s["good_ref_list"] = ", ".join([r.normal() for r in s.get("good_ref_list", [])])
            s["bad_ref_list"] = ", ".join([r.normal() for r in s.get("bad_ref_list", [])])
        csv.writerows(sources)
    with open("topics.csv", "wb") as fout:
        unique_topics = [{"chapter_name": x["chapter_name"], "topic_name": x["topic_name"]} for x in reduce(lambda a, b: a + ([b] if (len(a) == 0 or a[-1]['topic_name'] != b['topic_name']) else []),
                               sources, [])]
        csv = unicodecsv.DictWriter(fout, ["chapter_name", "topic_name"])
        csv.writeheader()
        csv.writerows(unique_topics)


if __name__ == "__main__":
    PARSED_REFS = 0.0
    TOTAL_REFS = 0
    MIDRASH, MISHNAH, MINOR, EASY_MIDRASH, INACCURATE_MIDRASH, OTZAR_MIDRASH, LAPASUK = init_midrash_books()
    library.rebuild_toc()
    open_csv()
    print("Percent refs parsed - {}/{} {}%".format(PARSED_REFS, TOTAL_REFS, PARSED_REFS/TOTAL_REFS))