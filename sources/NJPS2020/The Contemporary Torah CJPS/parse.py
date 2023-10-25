import os
from sources.functions import *
import time
from bs4 import BeautifulSoup, NavigableString
from collections import Counter
import re
special_span = False
prev_span_closed = False
place = False
acrostics = ""
next_acrostics = ""
endings = set()
styles = defaultdict(list)
startings = set()
verse_length = Counter()
def modify_small(x):
    for el in re.findall('<small>(.*?)</small>', x):
        if el in ["GOD", "ETERNAL", "LORD"]:
            x = x.replace(f"<small>{el}</small>", el[0] + f"<small>{el[1:]}</small>", 1)
    while "<br><br>" in x:
        x = x.replace("<br><br>", "<br>", 1)
    x = x.replace('<span class="poetry indentAllDouble"> </span>', '').replace('<span class="poetry indentAllDouble"></span>', '')
    if x.strip().endswith("<br>"):
        x = x[:-4]
    if x.strip().endswith("<br/>"):
        x = x[:-5]
    return x


def check_str(v, pos='ending'):
    v = bleach.clean(v, strip=True, tags=[])
    if pos == 'ending':
        # if v.endswith(" "):
        #     return False
        poss_endings = ['”', '“', '‘', '‘', ' ', '[', '—', '(']
        for p in poss_endings:
            if v.endswith(p):
                return True
    else:
        poss_starts = [",", ";", ".", ":", "'", "’", '—', '?', '!', ']', ')', '-']
        for p in poss_starts:
            if v.startswith(p):
                return True
    return False

def modify_char(v_num, brothers, is_char=False):
    global place, acrostics, next_acrostics
    v = brothers[v_num]
    meta_chars = []
    regular_chars = v.find_all('char') if not is_char else v.find_all('char')+[v]
    for c in regular_chars:
        if c.attrs["style"] == 'tl':
            c.name = "i"
            c.attrs = {}
            place = True
        elif c.attrs['style'] == 'qac':
            c.name = 'b'
            c.attrs = {}
            place = True
            brother_end_of_line = False
            for bro in brothers[v_num+1:]:
                if isinstance(bro, Tag) and bro.name == 'verse' and 'eid' in bro.attrs:
                    brother_end_of_line = True
                    break
                elif isinstance(bro, Tag):
                    break
            if c.text == 'א' and not brother_end_of_line:
                pass
            else:
                if next_acrostics != "":
                    next_acrostics += " "+str(c)
                else:
                    next_acrostics = str(c)
                c.decompose()
        elif c.attrs["style"] in ["it", "tl"]:
            c.name = "i"
            c.attrs = {}
            place = True
        elif c.attrs["style"] == "sc":
            c.name = "small"
            c.attrs = {}
            c.string = c.text.upper()
            place = True
        elif c.attrs["style"] == 'fr':
            c.string = c.text.replace(".", ":").strip()
            if "–" not in c.text:
                if c.text not in curr_ref:
                    print(f"Problem in {c.text} vs {curr_ref}")
            c.extract()
        elif c.attrs["style"] in ["fq"]:
            c.name = 'b'
            c.attrs = {}
        elif c.attrs["style"] in ["fv"]:
            c.name = 'sup'
            c.attrs = {}
        elif c.attrs['style'] == 'ft':
            meta_chars.append(c)
        elif c.attrs['style'] == 'qs':
            c.name = 'i'
            c.attrs = {}
            c.string = f"\u00a0\u00a0\u00a0{c.text}"
    # for c in meta_chars:
    #     c.string = bleach.clean(str(c), tags=ALLOWED_TAGS, attributes=allowed_attrs, strip=True)

def add_text(el, string=False):
    global special_span, prev_span_closed, acrostics, next_acrostics
    if string:
        txt = el
    else:
        assert v.find_all('char') == []
        txt = bleach.clean(el, tags=ALLOWED_TAGS, attributes=allowed_attrs, strip=True) + " "
    if prev_span_closed:
        prev_span_closed = False
    if acrostics != "":
        txt = acrostics + " " + txt
        acrostics = ""
    # if special_span:
    #     special_span = False
    #     prev_span_closed = True
    #     txt += "</span>"
    return txt

# I had assumed that there is one and only one span per p.  In actuality, within one verse, you can
# have multiple ps and one p can have multiple verses.  Three diff cases
# one verse across multiple ps: dont add a msg if there's already in this p by checking the string itself
# one p with multiple verses: when verse changes add </span>
issues = """Psalms 3:2""".splitlines()
places = {}
allowed_attrs = ['class', 'data-ref', 'href']
p_style_dict = {"q2": '<span class="poetry indentAllDouble">',
                'pi': '<br>',
                "pmr": '<span class="poetry indentAllDouble">',
                'mi': '<span class="poetry indentAll">',
                'lim1': '<span class="poetry indentAll">',
                'q1': '<span class="poetry indentAll">',
                         'qc': '<span class="poetry indentAll">'}
p_styles = set()
other_tags = set()
start = ""
for dir in ['RJPS Kethuvim for Sefaria, USX format - July 2023', "RJPS Torah for Sefaria, USX format - July 2023"]:
    for f in os.listdir(f"../RJPS_for_Sefaria.11Jul23/{dir}"):
        place = False
        poss_find = None
        if not f.endswith("usx"):
            continue
        if start not in f:
            continue
        start = ""
        lines = ""
        title = f.replace(".usx", "")
        # if title not in str(issues):
        #     continue
        print(title)
        text_dict = {}
        curr_ch = 0
        curr_seg = 0
        with open(f"../RJPS_for_Sefaria.11Jul23/{dir}/"+f, 'r') as f:
            lines = "\n".join(list(f))
            special_span = False
            xml = BeautifulSoup(lines, parser='lxml')
            segment = ""
            curr_ref = ""
            prev_was_lord = False
            pi3 = False
            for p_num, p in enumerate(xml.find_all("para")):
                if len(p.text) > 0 and p.name == "para" and p.attrs['style'] != 'rem':
                    verses_bool = len([x for x in p.contents if isinstance(x, Tag)]) > 0
                    if (len(p) > 1 or len(p.attrs) > 1):
                        for r in p.find_all('ref'):
                            r.attrs['loc'] = r.attrs['loc'].replace("EZK", "Ezekiel").replace("CH", " Chronicles").replace("1SA", "1 Samuel").replace("2SA", "2 Samuel")
                            r.attrs['loc'] = r.attrs['loc'].replace("ZEC", "Zechariah").replace("1KI", "1 Kings").replace("2KI", "2 Kings").replace("JOL", "Joel").replace("ZEP", "Zephaniah")
                            r.attrs['loc'] = r.attrs['loc'].replace("SNG", "Song of Songs").replace("NAM", "Nehemiah").replace("PSA", "Psalms").replace("NUM", "Numbers")
                            r.attrs['loc'] = r.attrs['loc'].replace("ISA", "Isaiah").replace("LEV", "Leviticus").replace("PRO", "Proverbs").replace("HOS", "Hoshea").replace("ECC", "Ecclesiastes")
                            r.attrs['loc'] = r.attrs['loc'].replace("EZR", "Ezra")
                            try:
                                loc = Ref(r.attrs['loc'].title().replace(" Of", " of"))
                            except Exception as e:
                                print(f"PROBLEM WITH {r.attrs}")
                                continue
                            t = Tag(name='a')
                            t.attrs['href'] = loc.url()
                            t.attrs['class'] = 'refLink'
                            t.attrs['data-ref'] = loc.normal()
                            t.string = r.text
                            r.replace_with(t)

                        styles[p["style"]].append(p)
                        if p['style'] == 'pi3':
                            if pi3:
                                text_dict[curr_ch][curr_seg] += "</small><br><small>"
                            else:
                                text_dict[curr_ch][curr_seg] += "<br><br><small>"
                            pi3 = True
                        if p["style"].startswith("q"):
                            other_tags.add(p["style"])
                        if p["style"] == "p" and 'vid' in p.attrs:
                            vid = p.attrs['vid']
                            poss_ch, poss_seg = [int(x) for x in vid.split(" ")[-1].split(":")]
                            assert poss_ch == curr_ch and poss_seg == curr_seg
                            text_dict[curr_ch][curr_seg] += "<br>"
                        # one verse across multiple ps: dont add a msg if there's already in this p by checking the string itself
                        new_msg = ""
                        for k in p_style_dict:
                            if p["style"] == k:
                                new_msg = p_style_dict[p["style"]]
                        if new_msg != "":
                            msg = new_msg
                            if 'vid' in p.attrs:
                                vid = p.attrs['vid']
                            else:
                                vid = p.find("verse").attrs['sid']

                            poss_ch, poss_seg = [int(x) for x in vid.split(" ")[-1].split(":")]
                            if poss_ch == curr_ch and poss_seg == curr_seg:
                                if new_msg in text_dict.get(curr_ch, {}).get(curr_seg, ''):
                                    new_msg = ""
                            if poss_ch not in text_dict:
                                text_dict[poss_ch] = {}
                            if poss_seg not in text_dict[poss_ch]:
                                if special_span:
                                    text_dict[curr_ch][curr_seg] += "</span>"
                                text_dict[poss_ch][poss_seg] = ""
                            if pi3:
                                text_dict[curr_ch][curr_seg] += "</small><br>"
                            if f"{title} {curr_ch}:{curr_seg}" in issues:
                                print(f"\nISSUE: {title} {curr_ch}:{curr_seg}")
                                print(text_dict[curr_ch][curr_seg])
                            curr_ch = poss_ch
                            curr_seg = poss_seg
                            if not text_dict[curr_ch][curr_seg].endswith(msg):
                                if len(text_dict[curr_ch][curr_seg]) > 0:
                                    if special_span:
                                        text_dict[curr_ch][curr_seg] += "</span>"
                                    if len(text_dict[curr_ch][curr_seg]) > 0:
                                        text_dict[curr_ch][curr_seg] += "<br>"
                                text_dict[curr_ch][curr_seg] += msg
                            special_span = True
                        else:
                            try:
                                if text_dict[curr_ch][curr_seg].endswith("</span>"):
                                    text_dict[curr_ch][curr_seg] += "<br>"
                            except KeyError as e:
                                pass
                            special_span = False


                        for v_num, v in enumerate(p.contents):
                            if not isinstance(v, NavigableString):
                                modify_char(v_num, p.contents)
                            if isinstance(v, NavigableString):
                                if len(v.strip()) == 0:
                                    continue
                                if prev_was_lord and check_str(v, "start"):
                                    text_dict[curr_ch][curr_seg] = text_dict[curr_ch][curr_seg].strip()
                                s_start = v.startswith("s. ") or v.startswith("s ") or v == "s"
                                if s_start:
                                    text_dict[curr_ch][curr_seg] = text_dict[curr_ch][curr_seg].strip()
                                    place = True
                                text_dict[curr_ch][curr_seg] += add_text(v, string=True)
                                prev_was_lord = False

                            elif v.name == "verse" and "sid" in v.attrs:
                                if next_acrostics == 'א':
                                    text_dict[curr_ch][curr_seg] += next_acrostics + " "
                                    next_acrostics = ""
                                if place:
                                    m = re.findall("<sup>.{1}</sup><sup>.{1}</sup>", text_dict[curr_ch][curr_seg])
                                    changed = len(m) > 0
                                    for x in m:
                                        text_dict[curr_ch][curr_seg] = text_dict[curr_ch][curr_seg].replace(x, "<sup>*</sup>", 1)
                                    places[f"{f.name[:-4]} {curr_ch}:{curr_seg}"] = text_dict[curr_ch][curr_seg]
                                segment = v.attrs["number"]
                                ref = v.attrs["sid"].split()[-1]
                                ref_sec, ref_seg = ref.split(":")
                                assert segment == ref_seg
                                curr_ref = "{} {}".format(title, ref)
                                if curr_ch in text_dict and curr_seg in text_dict[curr_ch]:
                                    text_dict[curr_ch][curr_seg] = text_dict[curr_ch][curr_seg].replace("  ", " ")
                                prev_ch = curr_ch
                                prev_seg = curr_seg
                                if pi3:
                                    text_dict[curr_ch][curr_seg] += "</small><br>"
                                if f"{title} {curr_ch}:{curr_seg}" in issues:
                                    print(f"\nISSUE: {title} {curr_ch}:{curr_seg}")
                                    print(text_dict[curr_ch][curr_seg])
                                curr_ch, curr_seg = [int(x) for x in ref.split(":")]
                                curr_ch = int(curr_ch)
                                curr_seg = int(curr_seg)
                                if curr_ch not in text_dict:
                                    text_dict[curr_ch] = {}
                                if curr_seg not in text_dict[curr_ch]:
                                    text_dict[curr_ch][curr_seg] = ""

                                if p.attrs.get('style', "") in p_style_dict: # and 'vid' in p.attrs:
                                    this_p_verses = [x.attrs.get('sid', '').split(' ')[-1] for x in p.find_all('verse') if len(x.attrs.get('sid', '').split(' ')[-1]) > 0]
                                    #p_ch, p_v = [int(x) for x in p.attrs.get('vid').split(" ")[-1].split(":")]
                                    if prev_ch != curr_ch or prev_seg != curr_seg:
                                        #print(f"{title} {p_ch}:{p_v}")
                                        assert "<span" in text_dict[prev_ch][prev_seg]
                                        text_dict[prev_ch][prev_seg] += "</span>"
                                        text_dict[curr_ch][curr_seg] += p_style_dict[p['style']]
                                        special_span = True
                                place = False
                            elif v.name == "verse":
                                acrostics = next_acrostics
                                next_acrostics = ""
                                ref = v.attrs["eid"].split()[-1]
                                ref_sec, ref_seg = ref.split(":")
                                assert segment == ref_seg
                                poss_ref = "{} {}".format(title, ref)
                                assert poss_ref == curr_ref
                            elif v.name == "note":
                                caller = v.attrs["caller"]
                                assert v.attrs["style"] == "f"
                                ft_txt = bleach.clean(v, tags=ALLOWED_TAGS, attributes=allowed_attrs, strip=True).strip()
                                full_i_tag = f'<sup class="footnote-marker">{caller}</sup><i class="footnote">{ft_txt}</i>'
                                text_dict[curr_ch][curr_seg] = text_dict[curr_ch][curr_seg].strip()
                                full_i_tag += ' '
                                text_dict[curr_ch][curr_seg] += add_text(full_i_tag, string=True)
                                prev_was_lord = True
                            elif v.name == "char":
                                if not check_str(text_dict[curr_ch][curr_seg], "ending"):
                                    if len(bleach.clean(text_dict[curr_ch][curr_seg], tags=[], strip=True)) > 0:
                                        text_dict[curr_ch][curr_seg] = text_dict[curr_ch][curr_seg].strip() + " "
                                found = False
                                modify_char(v_num, p.contents, is_char=True)
                                text_dict[curr_ch][curr_seg] += add_text(v, string=False)
                                prev_was_lord = True
                        text_dict[curr_ch][curr_seg] = text_dict[curr_ch][curr_seg].replace("  ", " ")
                        if place:
                            m = re.findall("<sup>.{1}</sup><sup>.{1}</sup>", text_dict[curr_ch][curr_seg])
                            changed = len(m) > 0
                            for x in m:
                                text_dict[curr_ch][curr_seg] = text_dict[curr_ch][curr_seg].replace(x, "<sup>*</sup>", 1)
                            places[f"{f.name[:-4]} {curr_ch}:{curr_seg}"] = text_dict[curr_ch][curr_seg]
            if pi3:
                text_dict[curr_ch][curr_seg] += "</small><br>"


        for ch in text_dict:
            orig = len(Ref("{} {}".format(title, ch)).all_segment_refs())
            text_dict[ch] = [modify_small(x.replace("'", "\u2019")) for x in convertDictToArray(text_dict[ch])]
            if orig != len(text_dict[ch]):
                print("Verses in Ch {} are off: {} vs {}".format(ch, orig, len(text_dict[ch])))
            for v, verse in enumerate(text_dict[ch]):
                text = re.sub("<sup>.{1}</sup>", "", text_dict[ch][v])
                text = "<html><body>{}</body></html>".format(text)
                soup = BeautifulSoup(text)
                for i_tag in soup.find_all('i', {"class": "footnote"}):
                    if 'class' in i_tag.attrs:
                        i_tag.decompose()

                orig = bleach.clean(Ref("{} {}:{}".format(title, ch, v+1)).text('en').text, tags=[], strip=True)
                new = ""
                tag = "p" if soup.find("p") is not None else "body"
                for el in soup.find(tag).contents:
                    if isinstance(el, NavigableString):
                        new += el + " "
                    else:
                        new += " "
                new = new.replace("  ", " ").strip()
                orig = orig.replace("  ", " ").strip()
                verse_length[new.count(" ")] += 1
                if new.count(" ") < 15:
                    diff = 3
                elif new.count(" ") < 30:
                    diff = 5
                else:
                    diff = 10
                # if abs(len(orig.split()) - len(new.split())) > diff:
                #     print("****")
                #     print("{} {}:{}".format(title, ch, v+1))
                #     print(orig)
                #     print(new)

        for p in text_dict:
            for v, verse in enumerate(text_dict[p]):
                if verse.startswith("<br>"):
                    text_dict[p][v] = verse.replace("<br>", "", 1)
                text_dict[p][v] = text_dict[p][v].replace("<br><br>", "<br>")
        text_dict = convertDictToArray(text_dict)
        tc = TextChunk(Ref(title), lang='en', vtitle="THE JPS TANAKH: Gender-Sensitive Edition")
        if tc.text != text_dict:
            tc.text = text_dict
            tc.save()

print(other_tags)
for v in VersionSet({"versionTitle": "THE JPS TANAKH: Gender-Sensitive Edition"}):
    v.versionSource = "https://jps.org/books/the-jps-tanakh-gender-sensitive-edition/"
    v.shortVersionTitle = "JPS, 2023"
    v.versionTitle = 'THE JPS TANAKH: Gender-Sensitive Edition'
    v.versionNotes = """<a href="http://purl.org/jps/rjps-preface">Read the Preface to the Revised JPS Edition</a>
<br><br>
<a href="http://purl.org/jps/gender">Read the Notes on Gender in Translation for the Revised JPS Edition</a>
<br><br>
<a href="https://www.sefaria.org/collections/commentary-on-the-usage-and-rendering-of-%D7%90%D7%99%D7%A9?tab=sheets">Read a Commentary on the Hebrew word 'ish in the Revised JPS Edition</a>"""
    v.save()

# vtitle = "The Contemporary Torah, Jewish Publication Society, 2006"
# for i in ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]:
#     refs = library.get_index(i).all_segment_refs()
#     for ref in refs:
#         tc = TextChunk(ref, lang='en', vtitle=vtitle)
#         soup = BeautifulSoup(tc.text)
#         m = re.findall("<sup>.{1}</sup><sup>.{1}</sup>", tc.text)
#         changed = len(m) > 0
#         for x in m:
#             tc.text = tc.text.replace(x, "<sup>*</sup>", 1)
#         send_text = {
#             "language": "en", "versionTitle": vtitle, "text": tc.text, "versionSource": "https://www.nli.org.il/he/books/NNL_ALEPH002529489/NLI"
#         }
#         if changed:
#             if ref.normal() not in places:
#                 places[ref.normal()] = tc.text
#
# with open("cjps issues.csv", 'w') as f:
#     writer = csv.writer(f)
#     writer.writerow(["Ref", "Text"])
#     for ref, comm in places.items():
#         writer.writerow([ref, comm])

details = {
    "purchaseInformationImage": "https://storage.googleapis.com/sefaria-physical-editions/JPS-Tanakh-Gender-Sensitive-Edition-Cover-300x450.jpg",
    "purchaseInformationURL": "https://jps.org/books/the-jps-tanakh-gender-sensitive-edition/"}
for version in VersionSet({"versionTitle": "THE JPS TANAKH: Gender-Sensitive Edition"}):
    print(version)
    for k, value in details.items():
        setattr(version, k, value)
        version.save()
