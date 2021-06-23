import os
from sources.functions import *
import time
from bs4 import BeautifulSoup, NavigableString
from collections import Counter
endings = set()
startings = set()
verse_length = Counter()
def check_str(v, pos='ending'):
    if pos == 'ending':
        poss_endings = ['”', '“', '‘', '‘']
        for p in poss_endings:
            if v.endswith(p):
                return True
    else:
        poss_starts = [",", ";", ".", ":", "'", "’"]
        for p in poss_starts:
            if v.startswith(p):
                return True
    return False


p_styles = set()
other_tags = set()
for f in os.listdir("."):
    if not f.endswith("usx"):
        continue
    lines = ""
    title = f.replace(".usx", "")
    text_dict = {}
    curr_ch = 0
    curr_seg = 0
    with open(f, 'r') as f:
        lines = "\n".join(list(f))
        xml = BeautifulSoup(lines, parser='lxml')
        segment = ""
        curr_ref = ""
        prev_was_lord = False
        for p_num, p in enumerate(xml.find_all("para")):
            if p.name == "para":
                if len(p) > 1 or len(p.attrs) > 1:
                    if p["style"] in ["q1", "q2"]:
                        text_dict[curr_ch][curr_seg] += "<br/>"
                    for v in p.contents:
                        if isinstance(v, NavigableString) and len(v.strip()) > 0:
                            if prev_was_lord and check_str(v, "start"):
                                text_dict[curr_ch][curr_seg] = text_dict[curr_ch][curr_seg].strip()
                            text_dict[curr_ch][curr_seg] += v.strip()
                            prev_was_lord = False
                        elif v.name == "verse" and "sid" in v.attrs:
                            segment = v.attrs["number"]
                            ref = v.attrs["sid"].split()[-1]
                            ref_sec, ref_seg = ref.split(":")
                            assert segment == ref_seg
                            curr_ref = "{} {}".format(title, ref)
                            if curr_ch in text_dict and curr_seg in text_dict[curr_ch]:
                                text_dict[curr_ch][curr_seg] = text_dict[curr_ch][curr_seg].replace("  ", " ")
                            curr_ch, curr_seg = ref.split(":")
                            curr_ch = int(curr_ch)
                            curr_seg = int(curr_seg)
                            if curr_ch not in text_dict:
                                text_dict[curr_ch] = {}
                            if curr_seg not in text_dict[curr_ch]:
                                text_dict[curr_ch][curr_seg] = ""
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
                                if isinstance(ft, NavigableString):
                                    if len(ft.strip()) > 0:
                                        ft_txt += ft
                                elif ft.attrs["style"] == 'fr':
                                    ft_ref = ft.text.replace(".", ":").strip()
                                    if "–" not in ft_ref:
                                        assert ft_ref in curr_ref
                                    else:
                                        print(ft_ref)
                                elif ft.attrs["style"] == "fq":
                                    ft_txt += "<b>{}</b>".format(ft.text)
                                elif ft.attrs["style"] == "ft":
                                    ft_txt += ft.text.strip()
                                elif ft.attrs["style"] == "fv":
                                    ft_txt += "<b>{}</b> ".format(ft.text.strip())
                            text_dict[curr_ch][curr_seg] = text_dict[curr_ch][curr_seg].strip()
                            text_dict[curr_ch][curr_seg] += "<sup>{}</sup><i class='footnote'>{}</i> ".format(caller, ft_txt)
                        elif v.name == "char":
                            other_tags.add(v.name)
                            if not check_str(text_dict[curr_ch][curr_seg], "ending"):
                                text_dict[curr_ch][curr_seg] = text_dict[curr_ch][curr_seg].strip() + " "
                            text_dict[curr_ch][curr_seg] += v.text.strip() + " "
                            prev_was_lord = True
                    text_dict[curr_ch][curr_seg] = text_dict[curr_ch][curr_seg].replace("  ", " ")

    for ch in text_dict:
        orig = len(Ref("{} {}".format(title, ch)).all_segment_refs())
        text_dict[ch] = convertDictToArray(text_dict[ch])
        if orig != len(text_dict[ch]):
            print("Verses in Ch {} are off: {} vs {}".format(ch, orig, len(text_dict[ch])))
        for v, verse in enumerate(text_dict[ch]):
            text_dict[ch][v] = re.sub("<sup>.{1}</sup>", "", text_dict[ch][v])
            soup = BeautifulSoup(text_dict[ch][v])
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
            if abs(len(orig.split()) - len(new.split())) > diff:
                print("****")
                print("{} {}:{}".format(title, ch, v+1))
                print(orig)
                print(new)

    text_dict = convertDictToArray(text_dict)
    send_text = {
        "language": "en",
        "versionTitle": "Contemporary JPS",
        "versionSource": "https://www.sefaria.org",
        "text": text_dict
    }
    post_text(title, send_text, server="https://germantalmud.cauldron.sefaria.org")
    time.sleep(10)


print(p_styles)
print(other_tags)
print(verse_length.most_common(20))