import os
from sources.functions import *
import time
from bs4 import BeautifulSoup, NavigableString
from collections import Counter
import re
special_span = False
prev_span_closed = False
endings = set()
styles = defaultdict(list)
startings = set()
verse_length = Counter()
def modify_small(x):
    for el in re.findall('<small>(.*?)</small>', x):
        x = x.replace(f"<small>{el}</small>", el[0] + f"<small>{el[1:]}</small>", 1)
    while "<br><br>" in x:
        x = x.replace("<br><br>", "<br>", 1)
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
        poss_starts = [",", ";", ".", ":", "'", "’", '—', '?', '!', ']', ')']
        for p in poss_starts:
            if v.startswith(p):
                return True
    return False


def add_text(el, string=False):
    global special_span
    global prev_span_closed
    if string:
        txt = el
    else:
        for x in v.find_all('char'):
            found = False
            if x.attrs["style"] in ["tl", "it"]:
                x.name = "i"
                found = True
            if x.attrs["style"] in ["sc"]:
                x.name = "small"
                found = True
                x.string = x.text.upper()
            if found:
                x.attrs = {}
        txt = bleach.clean(el, tags=ALLOWED_TAGS, attributes=allowed_attrs, strip=True) + " "
    if prev_span_closed:
        prev_span_closed = False
    if special_span:
        special_span = False
        prev_span_closed = True
        txt += "</span>"
    return txt


issues = """Exodus 4:11
Exodus 10:24
Leviticus 8:21
Deuteronomy 2:22
Leviticus 1:1
Deuteronomy 10:4
Genesis 2:12
Exodus 3:5
Leviticus 23:20
Numbers 21:14
Numbers 33:8
Numbers 18:16
Numbers 21:6""".splitlines()
issues = """Numbers 18:15
Numbers 21:5""".splitlines()
places = {}
allowed_attrs = ['class', 'data-ref', 'href']
p_style_dict = {"q2": '<span class="poetry indentAllDouble">', "pmr": '<span class="poetry indentAllDouble">', 'q1': '<span class="poetry indentAll">',
                         'qc': '<span class="poetry indentAll">'}
p_styles = set()
other_tags = set()
start = ""
dir = "RJPS Torah for Sefaria, USX format - July 2023"
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
            if p.name == "para" and p.attrs['style'] != 'rem':
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
                            text_dict[curr_ch][curr_seg] += "</small><br>"
                        text_dict[curr_ch][curr_seg] += "<small>"
                        pi3 = True
                    if p["style"].startswith("q"):
                        other_tags.add(p["style"])
                    if p["style"] == "p" and 'vid' in p.attrs:
                        vid = p.attrs['vid']
                        poss_ch, poss_seg = [int(x) for x in vid.split(" ")[-1].split(":")]
                        assert poss_ch == curr_ch and poss_seg == curr_seg
                        text_dict[curr_ch][curr_seg] += "<br>"
                    if p["style"].startswith("q") or p['style'] == 'pmr':
                        msg = p_style_dict[p['style']]
                        if 'vid' in p.attrs:
                            vid = p.attrs['vid']
                        else:
                            vid = p.find("verse").attrs['sid']

                        poss_ch, poss_seg = [int(x) for x in vid.split(" ")[-1].split(":")]
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

                            if p.attrs.get('style', "").startswith("q") and 'vid' in p.attrs:
                                p_ch, p_v = [int(x) for x in p.attrs.get('vid').split(" ")[-1].split(":")]
                                if p_ch != curr_ch or p_v != curr_seg:
                                    #print(f"{title} {p_ch}:{p_v}")
                                    text_dict[curr_ch][curr_seg] += p_style_dict[p['style']]
                                    special_span = True
                            place = False
                        elif v.name == "verse":
                            ref = v.attrs["eid"].split()[-1]
                            ref_sec, ref_seg = ref.split(":")
                            assert segment == ref_seg
                            poss_ref = "{} {}".format(title, ref)
                            assert poss_ref == curr_ref
                        elif v.name == "note":
                            caller = v.attrs["caller"]
                            assert v.attrs["style"] == "f"
                            ft_txt = ""
                            for ft in v:
                                if isinstance(ft, Tag):
                                    for x in ft.find_all("char", {"style": "tl"}):
                                        x.name = "i"
                                        x.attrs = {}
                                        place = True
                                    for x in ft.find_all("char", {"style": "it"}):
                                        x.name = "i"
                                        x.attrs = {}
                                        place = True
                                    for x in ft.find_all("char", {"style": "sc"}):
                                        x.name = "small"
                                        x.attrs = {}
                                        x.string = x.text.upper()
                                        place = True
                                if isinstance(ft, NavigableString):
                                    if len(ft.strip()) > 0:
                                        ft_txt += ft
                                elif ft.attrs["style"] in ["tl", "it"]:
                                    place = True
                                    ft_txt += "<i>"+bleach.clean(ft, tags=ALLOWED_TAGS, attributes=allowed_attrs, strip=True)+"</i>"
                                elif ft.attrs["style"] == 'fr':
                                    ft_ref = ft.text.replace(".", ":").strip()
                                    if "–" not in ft_ref:
                                        if ft_ref not in curr_ref:
                                            print(f"Problem in {ft_ref} vs {curr_ref}")
                                    else:
                                        pass
                                elif ft.attrs["style"] in ["fq", "fv"]:
                                    ft_txt += "<b>"+bleach.clean(ft, tags=ALLOWED_TAGS, attributes=allowed_attrs, strip=True)+"</b>"
                                elif ft.attrs["style"] == "ft":
                                    ft_txt += bleach.clean(ft, tags=ALLOWED_TAGS, attributes=allowed_attrs, strip=True).strip()
                            text_dict[curr_ch][curr_seg] = text_dict[curr_ch][curr_seg].strip()
                            text_dict[curr_ch][curr_seg] += add_text(f'<sup class="footnote-marker">{caller}</sup><i class="footnote">{ft_txt}</i> ', string=True)
                            prev_was_lord = True
                        elif v.name == "char":
                            if not check_str(text_dict[curr_ch][curr_seg], "ending"):
                                if len(bleach.clean(text_dict[curr_ch][curr_seg], tags=[], strip=True)) > 0:
                                    text_dict[curr_ch][curr_seg] = text_dict[curr_ch][curr_seg].strip() + " "
                            found = False
                            if v.attrs["style"] in ["tl", "it"]:
                                v.name = "i"
                                found = True
                                place = True

                            if v.attrs["style"] in ["sc"]:
                                v.name = "small"
                                found = True
                                place = True

                            if found:
                                v.attrs = {}

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

    text_dict = convertDictToArray(text_dict)
    tc = TextChunk(Ref(title), lang='en', vtitle="THE JPS TANAKH: Gender-Sensitive Edition (new batch)")
    if tc.text != text_dict:
        tc.text = text_dict
        tc.save()

print(other_tags)
for v in VersionSet({"versionTitle": "THE JPS TANAKH: Gender-Sensitive Edition (new batch)"}):
    v.versionSource = "https://jps.org/books/the-jps-tanakh-gender-sensitive-edition/"
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
for version in VersionSet({"versionTitle": "THE JPS TANAKH: Gender-Sensitive Edition (new batch)"}):
    print(version)
    for k, value in details.items():
        setattr(version, k, value)
        version.save()
