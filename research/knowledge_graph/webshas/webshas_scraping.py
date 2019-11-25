import requests, re, codecs, json, os, django, shutil
from collections import defaultdict
from copy import deepcopy
django.setup()
from sefaria.model import *
from sefaria.system.exceptions import InputError
from bs4 import BeautifulSoup, NavigableString, Comment

ROOT = "http://www.webshas.org/"


class WebShasParser:

    @staticmethod
    def get_page(url, verbose=True):
        url = url.replace(ROOT, "")
        try:
            with codecs.open("html/{}".format(url.replace("/", "_")), "rb", encoding="utf8") as fin:
                return fin.read()
        except IOError:

            try:
                with codecs.open("html/bad/{}".format(url.replace("/", "_")), "rb", encoding="utf8") as fin:
                    return False
            except IOError:
                if verbose:
                    print("fetching: {}".format(url))
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
                page = requests.get(ROOT + url, headers=headers)
                with codecs.open("html/{}".format(url.replace("/", "_")), "wb", encoding="utf8") as fout:
                    fout.write(page.text)
                return page.text
        except UnicodeDecodeError:
            print(url)
            return False

    @staticmethod
    def download_unknown_pages():
        with codecs.open("unknown_links.json", "rb", encoding="utf8") as fin:
            jin = json.load(fin)
        for link in jin:
            WebShasParser.get_page(link)

    @staticmethod
    def remove_bad_pages():
        count = 0
        for subdir, dirs, files in os.walk("html"):
            for file in files:
                if file.startswith(".") or subdir != "html":
                    continue
                filepath = subdir + os.sep + file
                is_good = WebShasParser.is_good_link(file, False)
                if not is_good:
                    count += 1
                    shutil.move(filepath, subdir + os.sep + "bad" + os.sep + file)
        print(count)

    @staticmethod
    def line2str(ln):
        return " ".join([i.strip() if isinstance(i, NavigableString) else i.get_text().strip() for i in ln])

    @staticmethod
    def parse_refs(refs):
        replacements = {
            "Rosh haShanah": "Rosh Hashanah",
            "Menachos": "Menachot"
        }
        srefs = []
        ref_list = re.split(r"[;,]", refs)
        mult_added = 0
        mult_reg = r"[(\[](\d+)x[)\]]"
        for i, r in enumerate(ref_list):
            if i != 0 and re.search(r"^\d+[ab](?:-(?:\d+)?[ab])?(?: {})?$".format(mult_reg), r.strip()):
                if len(srefs) - mult_added != i:
                    continue
                r = srefs[i-1].index.title + r
            try:
                # remove multiplier
                multiplier = re.search(mult_reg, r)
                times = 1
                if multiplier:
                    try:
                        times = int(multiplier.group(1))
                        r = r.replace(multiplier.group(), '')
                    except ValueError:
                        pass
                mult_added += (times - 1)
                # remove other parentheticals
                r = re.sub(r"[(\[][^)\]]+[)\]]?", "", r)
                # normalize book name
                for k, v in list(replacements.items()):
                    if k in r:
                        r = r.replace(k, v)
                srefs += [Ref(r.strip()) for _ in range(times)]
            except InputError:
                print("INPUT ERROR: {}".format(r))
            except ValueError:
                print("VALUE ERROR: {}".format(r))
            except AttributeError:
                print("ATTRIBUTE ERROR: {}".format(r))

        try:
            return [r.normal() for r in srefs]
        except AttributeError:
            print("ATTRIBUTE ERROR")
            print(refs)
            return []

    @classmethod
    def normalize_href(cls, href, page_href="", relative=True):
        href = href.replace(ROOT, "")
        href = href.strip()
        if re.search(r"^\s*(\.\./)+", href):
            href = re.sub(r"^\s*(\.\./)+", "", href)
        elif relative:
            page_href = page_href.replace(ROOT, "")
            page_loc = re.findall("(^.*/)[^/]+\.htm$", page_href)[0]
            href = page_loc + href
        return ROOT + href, href not in cls.all_links

    @staticmethod
    def parse_line(ln, page_href, subtopic):
        obj = {'links': []}
        text = WebShasParser.line2str(ln)
        if (len(ln) == 1 and ln[0].name == "a") or subtopic == "Links":
            obj['text'] = text
        else:
            text_split = re.split(r":(?=[^:]+$)", text)
            if len(text_split) != 2:
                print("WEIRD LINE: len {}".format(len(text_split)))
            else:
                text, refs = text_split
                obj['text'] = text
                obj['refs'] = WebShasParser.parse_refs(refs)
        unknown_links = []
        for elem in ln:
            if elem.name == 'a':
                href, is_unknown = WebShasParser.normalize_href(elem['href'], page_href)
                if is_unknown:
                    unknown_links += [href]
                obj['links'] += [href]
        return obj, unknown_links

    @staticmethod
    def parse_link(l, verbose=True):
        page = WebShasParser.get_page(l)
        if not page:
            raise InputError
        subsoup = BeautifulSoup(page, "lxml")
        h2 = subsoup.select_one("h2")
        if h2 is None:
            print("NO H2!!")
            raise InputError
        title = h2.get_text()
        if verbose:
            print("-------"*20)
            print(title + " - " + l)
        out = {"link": l, "subtopics": {}}
        unknown_links = defaultdict(list)
        subtopic_list = subsoup.select("i")
        for subtopic in subtopic_list:
            item_list = subtopic.findNext("ul")
            if item_list is None:
                continue
            subtopic_title = subtopic.get_text().strip()
            if verbose:
                print("> {}".format(subtopic_title))
            out["subtopics"][subtopic_title] = []
            temp_line = []
            for item in item_list.descendants:
                if item.parent != item_list and (item.parent.name != "ul" or item.parent.parent != item_list):
                    # avoid recursion
                    continue
                if isinstance(item, NavigableString):
                    if len(item.strip()) == 0 or isinstance(item, Comment):
                        continue
                    temp_line += [item]
                elif len(item.get_text().strip()) == 0:
                    if item.name == "hr":  # last element on the page
                        break
                    elif item.name == "br":
                        if len(temp_line) > 0:
                            parsed_line, temp_unknown_links = WebShasParser.parse_line(temp_line, l, subtopic_title)
                            out["subtopics"][subtopic_title] += [parsed_line]
                            unknown_links[subtopic_title] += [temp_unknown_links]
                            temp_line = []
                elif item.name == "a":
                    temp_line += [item]
                else:
                    print("UNKNOWN ELEMENT: {} - {}".format(item.name, item))
        return title, out, unknown_links

    @staticmethod
    def is_good_link(l, verbose=True):
        if len(l) == 0:
            return False
        page = WebShasParser.get_page(l)
        if not page:
            return False
        subsoup = BeautifulSoup(page, "lxml")
        body = subsoup.select_one("body").get_text().strip()
        if len(body) == 0:
            if verbose:
                print("no body")
            return False
        h1 = subsoup.select_one("h1")
        if h1 is not None:
            if h1.get_text().strip() == "Multiple Choices":
                print("Multiple Choices")
                return False
        return True

    @staticmethod
    def parse():
        out = {}
        unhandled_unknown_links = set()
        soup = BeautifulSoup(WebShasParser.get_page("engindex.htm"), "lxml")
        meta_topic_links = sorted(
            [x for x in list(set([link["href"] for link in soup.select("table a")])) if not x.startswith("http")])
        all_links = set()
        # filter out bad links
        for l in meta_topic_links:
            if WebShasParser.is_good_link(l):
                all_links.add(l)
        WebShasParser.all_links = deepcopy(all_links)
        for l in all_links:

            title, subout, unknown_links = WebShasParser.parse_link(l)
            out[title] = subout
            for subtopic, subtopic_links in list(unknown_links.items()):
                for isubtopic_item_links, subtopic_item_links in enumerate(subtopic_links):
                    if len(subtopic_item_links) == 0:
                        continue
                    for yo in subtopic_item_links:
                        if yo in unhandled_unknown_links:
                            unhandled_unknown_links.remove(yo)
                    subpages = []
                    for sublink in subtopic_item_links:
                        if not WebShasParser.is_good_link(sublink):
                            continue
                        try:
                            norm_href, is_unknown = WebShasParser.normalize_href(sublink, relative=False)
                            subtitle, subout, unknown_links = WebShasParser.parse_link(norm_href)
                            subpages += [subout]
                            WebShasParser.all_links.add(norm_href.replace(ROOT, ""))
                        except InputError:
                            continue
                        for k, v in list(unknown_links.items()):
                            for yoyo in v:
                                for yoyoyo in yoyo:
                                    unhandled_unknown_links.add(yoyoyo)
                    if len(subpages) > 0:
                        out[title]["subtopics"][subtopic][isubtopic_item_links]["subpages"] = subpages
        for yo in WebShasParser.all_links:
            if ROOT + yo in unhandled_unknown_links:
                unhandled_unknown_links.remove(ROOT + yo)
        print("STILL UNHANDLED UNKNOWN LINKS: {}".format(len(unhandled_unknown_links)))
        with codecs.open("known_links.json", "wb", encoding="utf8") as fout:
            json.dump(list(WebShasParser.all_links), fout, indent=2, ensure_ascii=False)
        with codecs.open("unknown_links.json", "wb", encoding="utf8") as fout:
            json.dump(list(unhandled_unknown_links), fout, indent=2, ensure_ascii=False)
        with codecs.open("webshas.json", "wb", encoding="utf8") as fout:
            json.dump(out, fout, indent=2, ensure_ascii=False)

    @staticmethod
    def stats():
        with codecs.open("webshas.json", "rb", encoding="utf8") as fin:
            shas = json.load(fin)
        top_level = 0
        sub_top = 0
        low_level = 0
        sources = 0
        for k1, v1 in list(shas.items()):
            top_level += 1
            for k2, v2 in list(v1["subtopics"].items()):
                sub_top += 1
                for k3 in v2:
                    if "refs" not in k3:
                        sub_top += 1
                    else:
                        low_level += 1
                        sources += len(k3["refs"])
                    if "subpages" in k3:
                        for k4 in k3["subpages"]:
                            sub_top += 1
                            for k5, v5 in list(k4["subtopics"].items()):
                                sub_top += 1
                                if "refs" not in k5:
                                    sub_top += 1
                                else:
                                    low_level += 1
                                    sources += len(k5["refs"])
        print("Top Level: {}".format(top_level))
        print("Sub Top Level: {}".format(sub_top))
        print("Low Level: {}".format(low_level))
        print("Sources: {}".format(sources))


if __name__ == '__main__':
    # WebShasParser.parse()
    # WebShasParser.stats()
    WebShasParser.download_unknown_pages()
    # WebShasParser.remove_bad_pages()

"""
Weird ref types:
- R. Succah 49b "Migamaya"
- and see Rashi there "mishraf sharif"
- Tosafot Berachot 18a "v'sefer"
- Tos. Berachot 3b #2
- " Makkot 5a - Witnesses Who Intentionally Incriminate Falsely [Edim Zomimin] - baisdin/edus/zomimin.htm
- 2b - Witnesses Who Intentionally Incriminate Falsely [Edim Zomimin] - baisdin/edus/zomimin.htm
- 21b - Declaring/Enlarging the Month - baisdin/powers/chodesh.htm
- Rashi Rosh HaShanah 33a "DePiturot"
- Ran Nedarim 8b "Baal"
- Gilyon HaShas Berachot 12a
- Pesachim 7b [See Rashi Blessings on Mitzvot - berachos/mitzvah.htm
- See Gd and Yisrael for numerous links
- Ketubot16a-b (pretty common)
- "Maaser Sheni" is a secondary tithe taken from produce during certain years of the shemitah cycle. It is brought to Jerusalem and consumed there

TOP LEVEL CATS
animals
avel
baisdin
berachos
chesed - Acts of Kindness / Social Issues
dibbur
dwelling
emunah
eretz
ishus
kashrus
kelal
kinyan
levush
mikdash
neder
nezek
science
seudah
shabbos
spec
taanis
taharah
tefillah
torah
ttm
yomtov
zevach
"""




