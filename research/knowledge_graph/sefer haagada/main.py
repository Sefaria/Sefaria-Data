# -*- coding: utf-8 -*-

import re
import django
import unicodecsv
django.setup()
from collections import defaultdict
from tqdm import tqdm
from sefaria.model import *
from sefaria.utils.hebrew import strip_cantillation, gematria, has_cantillation
from sefaria.system.exceptions import InputError
from research.link_disambiguator.main import Link_Disambiguator

# TODO figure out how to map mekhilta


def init_midrash_books():
    easy_midrash = {
        u"בר\"ר": u"בראשית רבה",
        u"שמו\"ר": u"שמות רבה",
        u"ויק\"ר": u"ויקרא רבה",
        u"במ\"ר": u"במדבר רבה",
        u"דב\"ר": u"דברים רבה",
        u"רו\"ר": u"רות רבה",
        u"קה\"ר": u"קוהלת רבה",
        u"איכ\"ר": u"איכה רבה",
        u"אסת\"ר": u"אסתר רבה",
        u"פדר\"כ": u"פסיקתא דרב כהנא",
        u"ספרי במדבר": u"ספרי במדבר",
        u"ספרי דברים": u"ספרי דברים",
        u'אדר"נ, נו"א,': u'אבות דרבי נתן',
        u'אדר"נ, נו"ב,': u'אבות דרבי נתן',
        u"מד\"ת": u'מדרש תהילים',
        u"מדמ\"ש": u'מדרש משלי',
        u"פדר\"א": u'פרקי דרבי אליעזר',
        u"סדר עולם רבה": u"סדר עולם רבה"
    }
    possibly_inaccurate_midrash = {
        u"סא\"ר": u"תנא דבי אליהו רבה",
        u"סא\"ז": u"תנא דבי אליהו זוטא, סדר אליהו זוטא",  # numbering goes past 15. seems to go into other additions to the book
        u"דרך ארץ": u"מסכת דרך ארץ רבה",  # numbering seems consistently behind by 2 perakim
        u"פס\"ר": u"פסיקתא רבתי",  # seems accurate to the section but not the segment
    }
    lapassuk_dict = {
        u'מדרש תהילים': u"תהילים",
        u"קוהלת רבה": u"קהלת",
        u"איכה רבה": u"איכה",
        u'מדרש משלי': u'משלי',
        u"שיר השירים רבה": u'שיר השירים',
        u"מכילתא דרשב\"י": u'שמות',
    }
    needs_disambiguation = {
        u"מדרש תמורה": u"אוצר מדרשים, מדרש תמורה"
    }
    otzar_midrashim = {
        u"מדרש תמורה": u"אוצר מדרשים, מדרש תמורה",
        u"מדרש לחנוכה": u"אוצר מדרשים, מדרשים על חנוכה, מדרש לחנוכה",
        u"מדרש יונה": u"אוצר מדרשים, מדרשים על ספר יונה, (מדרש יונה (מפרקי דר\"א",  # note, typo in parens apparently exists in actual title
        u"חנוך הוא מטטרון": u"אוצר מדרשים, מטטרון - חנוך א",  # this ref is impossible to parse because it has a dash in it
        u"אלפא ביתא דבן סירא": u"אוצר מדרשים, אלפא ביתא דבן סירא, אלפא ביתא אחרת לבן סירא",
        u"מסכת גיהינום": u"אוצר מדרשים, גן עדן; גיהנם, מסכת גיהנם",
        u"מדרש עשרת הדיברות": u"אוצר מדרשים, מדרש עשרת הדברות",
        u"קדושת ברכו ליחיד": u"אוצר מדרשים, קדושא, קדושת ברכו ליחיד"

    }
    midrash_dict = {
        u"מכילתא דר\"י": "Mekhilta d'Rabbi Yishmael",  # TODO seems to also be able to use pasuk as sections
        u"לק\"ט": None,  # category + we don't have lekach tov on Torah yet
        u"מד\"ש": None,  # Midrash Shmuel, I believe. We don't have it
        u"ילקוט לשה\"ש": "Yalkut Shimoni on Nach, Shir HaShirim",  # appears once
        u"ספרא": "Sifra",  # TODO
        u"אג\"ב": "UNKNOWN",
        u"מד\"א": "Midrash Agada",  # appears four times
    }
    talmud = library.get_indexes_in_category("Bavli", full_records=True)
    for t in talmud:
        midrash_dict[t.get_title("he")] = t.title

    mishnah = library.get_indexes_in_category("Mishnah", full_records=True)
    mishnah_dict = {}
    for m in mishnah:
        he = m.get_title("he").replace(u"משנה ", u"")
        en = m.title.replace(u"Mishnah ", u"")
        mishnah_dict[he] = en

    minor = library.get_indexes_in_category("Minor Tractates", full_records=True)
    minor_dict = {}
    for m in minor:
        he = m.get_title("he").replace(u"מסכת ", u"")
        en = m.title.replace(u"Tractate ", u"")
        minor_dict[he] = en

    return midrash_dict, mishnah_dict, minor_dict, easy_midrash, possibly_inaccurate_midrash, otzar_midrashim, lapassuk_dict


def parse_ref(tref, source):
    tref = tref.strip()
    try:
        if re.match(ur"שם,? ", tref):
            return None
        if u"הסכוליון" in tref:
            # not sure what this text is
            return None
        if any([re.match(k, tref) for k in OTZAR_MIDRASH.keys()]):
            replacer = None
            for k, v in OTZAR_MIDRASH.items():
                if re.match(k, tref):
                    replacer = k
                    break
            tref = OTZAR_MIDRASH[replacer]  # simply replace. needs to be disambiguated
        elif u'שהש"ר' in tref:
            print 'yo'
            return Ref(u"שיר השירים רבה")
        elif u"ירושלמי" in tref:
            replacement_mesechtot = {
                u"תרומה": u"תרומות",
                u"כלאיים": u"כלאים",
            }
            for k, v in replacement_mesechtot.items():
                tref = tref.replace(u" {} ".format(k), u" {} ".format(v))
            titles = library.get_titles_in_string(tref)
            if len(titles) > 0:
                return Ref(titles[0])
        elif u"תוספתא" in tref:
            return Ref(tref)
        elif re.search(u' \u05e2(?:"|\'\')[\u05d0\u05d1]', tref):
            # talmud
            tref = re.sub(ur",? ?\u05e2(?:\"|'')\u05d0", u'.', tref)
            tref = re.sub(ur",? ?\u05e2(?:\"|'')\u05d1", u':', tref)
            if re.search(ur"[\u2014\-]", tref):
                tref1, tref2 = re.split(ur"[\u2014\-]", tref)
                oref1 = Ref(tref1)
                oref2 = Ref((tref1[:-1] + tref2) if tref2 == u':' else (oref1.index.get_title("he") + u" " + tref2))
                oref = oref1.to(oref2)
            else:
                oref = Ref(tref)
            return oref
        elif any([t in tref for t in MISHNAH.keys()]):
            # mishnah
            return Ref(u"{} {}".format(u"משנה", tref))
        elif any([t in tref for t in MINOR.keys()]):
            # minor tractates
            tref = u"{} {}".format(u"מסכת", tref) if u"מסכת" not in tref else tref
            return Ref(tref)
        elif any([t in tref for t in EASY_MIDRASH.keys()]):
            # midrash rabbah
            replacer = None
            replacement = None
            for t, r in EASY_MIDRASH.items():
                if t in tref:
                    replacer = t
                    replacement = r
                    break
            tref = tref.replace(replacer, replacement)
            tref = tref.replace(u"איכה רבה פתיחתא", u"איכה רבה, פתיחתא")
        elif any([t in tref for t in INACCURATE_MIDRASH.keys()]):
            replacer = None
            replacement = None
            for t, r in INACCURATE_MIDRASH.items():
                if t in tref:
                    replacer = t
                    replacement = r
                    break
            tref = tref.replace(replacer, replacement)
        elif re.match(ur"^\u05ea\u05e0\u05d7\u05d5\u05de\u05d0(?P<buber>(?: \u05d1\u05d5\u05d1\u05e8)?) (?P<parsha>[\u05d0-\u05ea ]+), ", tref):
            # midrash tanchuma
            tref = re.sub(ur"^\u05ea\u05e0\u05d7\u05d5\u05de\u05d0(?P<buber>(?: \u05d1\u05d5\u05d1\u05e8)?) (?P<parsha>[\u05d0-\u05ea ]+), ", ur"\u05ea\u05e0\u05d7\u05d5\u05de\u05d0\g<buber>, \g<parsha>, ", tref)
            replacement_parshas = {
                u"תצווה": u"תצוה",
                u"חוקת": u"חקת",
                u"קורח": u"קרח",
                u"ניצבים": u"נצבים",
                u"נשוא": u"נשא",
                u"בחוקותי": u"בחוקתי",
                u"פינחס": u"פנחס",
                u"אחרי": u"אחרי מות",
                u"שלח לך": u"שלח",
                u"כי תישא": u"כי תשא"
            }
            for k, v in replacement_parshas.items():
                tref = tref.replace(u" {}, ".format(k), u" {}, ".format(v))
            if u"הוספה " in tref:
                tref = re.sub(u" (?P<parsha>[\u05d0-\u05ea ]+), (?P<hosafa>\u05d4\u05d5\u05e1\u05e4\u05d4)", u" \g<hosafa> \u05dc\g<parsha>", tref)
        elif re.match(ur"מכילתא דר\"י", tref):
            matches = filter(lambda x: x.index.get_title("en") == "Exodus" and 12 <= x.sections[0] <= 35,
                             library.get_refs_in_string(source, "he", citing_only=True))
            if len(matches) > 0:
                my_passuk = matches[0].he_normal()
                tref = my_passuk.replace(u"שמות", u"מכילתא דרבי ישמעאל")
            else:
                pass
                # print "NO EXODUS"

        elif re.match(ur'\u05d9\u05dc\u05e7"\u05e9 ', tref):
            # yalkut shimoni
            match = re.match(ur'\u05d9\u05dc\u05e7"\u05e9 \u05dc(?P<parsha>[\u05d0-\u05ea ]+(?: [\u05d0\u05d1])?),? ', tref)
            if not match:
                raise InputError
            book = match.groupdict()['parsha']
            if book == u"שמואל":
                book = u"שמואל א"
            elif book == u"מלכים":
                book = u"מלכים א"
            elif book == u"דברי הימים":
                book = u"דברי הימים א"
            index = library.get_index(book)
            if len(index.categories) > 1 and index.categories[0] == "Tanakh":
                if index.categories[1] == "Torah":
                    replacer = u"על התורה"
                else:
                    replacer = u"על נ\"ך"
            else:
                raise InputError
            tref = re.sub(ur'\u05d9\u05dc\u05e7"\u05e9 \u05dc(?P<parsha>[\u05d0-\u05ea ]+(?: [\u05d0\u05d1])?),? ', u'\u05d9\u05dc\u05e7\u05d5\u05d8 \u05e9\u05de\u05e2\u05d5\u05e0\u05d9 {} '.format(replacer), tref)
        if u"לפסוק" in tref:
            for k, book in LAPASUK.items():
                if k in tref:
                    matches = filter(lambda x: x.index.get_title("he") == book, library.get_refs_in_string(source, "he", citing_only=True))
                    # TODO deal with more than one match
                    if len(matches) > 0:
                        my_passuk = matches[0].he_normal()
                        tref = my_passuk.replace(book, k)
                    else:
                        # print u"NO MATCHES"
                        print tref
                    break

        return Ref(tref)
    except InputError:
        # print u"BADNESS"
        print tref
    except IndexError:
        # print u"BADNESS INDEX"
        print tref


def is_filler_midrash_word(word):
    is_hashem = re.match(ur"\s*\u05d4[\u05f3'][\":;!?,.—()״׳]*$", word) is not None
    is_gomer = re.match(ur"\s*\u05d5?\u05d2\u05d5[\u05f3']?[\":;!?,.—()״׳]*$", word) is not None
    return is_hashem or is_gomer


def get_midrashic_text(text):
    """
    Given text, removes commentary text and returns midrashic text
    If it determines text is all commentary, returns empty string
    :param text:
    :return:
    """
    dash = u"—"
    words = text.split()
    if len(words) == 0:
        return u"", u""
    midrash_words = 0.0
    filler_words = 0.0
    curr_non_midrash_start = None
    curr_midrash_start = None
    in_paren = False
    potential_non_midrash_span = None
    non_midrash_spans = []
    for i, w in enumerate(words):
        if u"(" in w:
            in_paren = True
        if in_paren or re.match(ur"^[^\u05d0-\u05ea]+$", w):
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
        if u")" in w:
            in_paren = False
        if re.search(ur"\.\s*$", w) and not re.search(ur"\.\.\.\s*$", w):
            # period means end of potential non midrash span
            curr_midrash_start = None
    if curr_non_midrash_start is not None:
        non_midrash_spans += [(curr_non_midrash_start, len(words))]
    actual_len = len(words) - filler_words
    non_midrash_words = reduce(lambda a, b: a + (b[1]-b[0]), non_midrash_spans, 0)
    cutoff = 0.7 if actual_len < 20 else 0.8
    if actual_len <= 0:
        return u"", text
    if (non_midrash_words / actual_len) > cutoff:
        return u"", text
    if len(non_midrash_spans) == 0:
        return text, u""
    midrashic_text = u""
    commentary_text = u""
    last_end = 0
    for s, e in non_midrash_spans:
        midrashic_text += u" ".join(words[last_end:s])
        commentary_text += u" ".join(words[s:e])
        last_end = e
    midrashic_text += u" ".join(words[last_end:])
    return midrashic_text, commentary_text


def disambiguate_all(source_list):
    ref_map = defaultdict(list)
    source_dict_map = {}

    def make_key(source_dict):
        return u"{}|{}|{}".format(source_dict["chapter_name"], source_dict["topic_name"], source_dict["source_num"])
    for source_dict in source_list:
        key = make_key(source_dict)
        if key in source_dict_map:
            print "AHHHHHH"
        source_dict_map[key] = source_dict
        for oref in source_dict["ref_list"]:
            ref_map[oref.normal()] += [(source_dict["source"], key)]

    for tref, temp_source_list in tqdm(ref_map.items()):
        results = disambiguate_ref_list(tref, temp_source_list)
        for key, result in results.items():

            source_dict = source_dict_map[key]

            if "good_ref_list" not in source_dict:
                source_dict["good_ref_list"] = []
                source_dict["bad_ref_list"] = []
            if result is None:
                source_dict["bad_ref_list"] += [Ref(tref)]
            else:
                source_dict["good_ref_list"] += [Ref(result["A Ref"])]
    return source_list


def disambiguate_ref_list(main_tref, tref_list):
    """
    Find exact segment ref which oref matches. oref can be either segment or section
    :param oref:
    :return:
    """
    ld = Link_Disambiguator()
    results = ld.disambiguate_segment_by_snippet(main_tref, tref_list)
    return results


def make_parsed_source(chapter_name, chapter_num, topic_name, topic_num, source_num, prev_rows):
    global TOTAL_REFS, PARSED_REFS
    source, commentary = u"", u""
    for r in prev_rows:
        s, c = get_midrashic_text(r["source"])
        source += s
        commentary += c
    m = re.search(ur"\(([^)]+)\)\s*\.?\s*\$?\s*$", source)
    if m is None:
        print u"OH NO -- {} {} {}: {}".format(chapter_num, topic_num, source_num, topic_name)
        print strip_cantillation(source, strip_vowels=True)[-20:]
        return None
    else:
        source = re.sub(ur"\(([^)]+)\)\s*\.?\s*\$?\s*$", u"", source)
        ref_list = [parse_ref(r, source) for r in re.split(ur"[:;]", m.group(1))]
        TOTAL_REFS += len(ref_list)
        PARSED_REFS += len(filter(None, ref_list))
    return {
        "chapter_name": chapter_name,
        "chapter_num": chapter_num,
        "topic_name": topic_name,
        "topic_num": topic_num,
        "source_num": source_num,
        "source": source,
        "commentary": commentary,
        "ref_list": filter(None, ref_list)
    }


def update_chapter(row):
    if len(row["chapter"]) > 0:
        m = re.match(ur"\u05e4\u05e8\u05e7 ([\u05d0-\u05ea]{1,3}) (.+)$", row["chapter"])
        if m is None:
            print row
            return None
        chapter_num = gematria(m.group(1))
        chapter_name = m.group(2)
        return chapter_name, chapter_num
    else:
        return None


def update_topic(row):
    if len(row["topic"]) > 0:
        m = re.match(ur"([\u05d0-\u05ea]{1,4})\. (.+)$", row["topic"])
        if m is None:
            print row
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
                    print u"{} <= {} {}".format(new_chapter[1], curr_chapter_num, curr_chapter_name)
                curr_chapter_name, curr_chapter_num = new_chapter
                curr_topic_num = 0
                curr_source_num = 0
            # update topic
            new_topic = update_topic(row)
            if new_topic:
                if new_topic[1] != curr_topic_num + 1:
                    print u"{} <= {} {}".format(new_topic[1], curr_topic_num, curr_topic_name)
                curr_topic_name, curr_topic_num = new_topic
            # update source num
            if len(row["sourceNum"]) > 0:
                new_source_num = gematria(row["sourceNum"])
                if new_source_num != curr_source_num + 1:
                    print u"yoyoyo {} <= {} {} -- {}".format(new_source_num, curr_source_num, curr_topic_name, curr_topic_num)
                curr_source_num = new_source_num

            prev_rows += [row]
        if len(prev_rows) > 0:
            sources += [make_parsed_source(curr_chapter_name, curr_chapter_num, curr_topic_name, curr_topic_num, curr_source_num, prev_rows)]
    sources = filter(None, sources)
    sources = disambiguate_all(sources)
    with open("parsed.csv", "wb") as fout:
        csv = unicodecsv.DictWriter(fout, ["chapter_name", "chapter_num", "topic_name", "topic_num", "source_num", "source", "commentary", "good_ref_list", "bad_ref_list", "ref_list"])
        csv.writeheader()
        for s in sources:
            s["ref_list"] = u", ".join([r.normal() for r in s.get("ref_list", [])])
            s["good_ref_list"] = u", ".join([r.normal() for r in s.get("good_ref_list", [])])
            s["bad_ref_list"] = u", ".join([r.normal() for r in s.get("bad_ref_list", [])])
        csv.writerows(sources)
    with open("topics.csv", "wb") as fout:
        unique_topics = map(lambda x: {"chapter_name": x["chapter_name"], "topic_name": x["topic_name"]}, reduce(lambda a, b: a + ([b] if (len(a) == 0 or a[-1]['topic_name'] != b['topic_name']) else []),
                               sources, []))
        csv = unicodecsv.DictWriter(fout, ["chapter_name", "topic_name"])
        csv.writeheader()
        csv.writerows(unique_topics)


if __name__ == "__main__":
    PARSED_REFS = 0.0
    TOTAL_REFS = 0
    MIDRASH, MISHNAH, MINOR, EASY_MIDRASH, INACCURATE_MIDRASH, OTZAR_MIDRASH, LAPASUK = init_midrash_books()
    library.rebuild_toc()
    open_csv()
    print u"Percent refs parsed - {}/{} {}%".format(PARSED_REFS, TOTAL_REFS, PARSED_REFS/TOTAL_REFS)