import requests, re, codecs, json, os, django, shutil, unicodecsv, csv
from collections import defaultdict
from copy import deepcopy
django.setup()
from sefaria.model import *
from sefaria.system.exceptions import InputError
from bs4 import BeautifulSoup, NavigableString, Comment

ROOT = "http://www.webshas.org/"

"""
[
    {
        "name": "baisdin",
        "link": "baisdin_index.htm",
        "subpages": [
            {
                "name": "dayyan",
                "link": "baisdin_dayyan_index.htm",
                "subpages": [

                ]
            }
        ]
    }
]
"""

class WebShasParser:

    def __init__(self):
        # self.all_links = set()
        # self.leftover_links = set()
        # self.visited_links = set()
        # self.file_tree = []
        # self.make_file_tree()
        # self.parse_file_tree()
        self.extract_topic_headers(4)

    def make_file_tree(self):
        for subdir, dirs, files in os.walk("html"):
            for file in files:
                if file.startswith(".") or subdir != "html":
                    continue
                path = file.split("_")

                sub_file_tree = self.file_tree
                for i, p in enumerate(path):
                    p_obj = next((x for x in sub_file_tree if x["name"] == p), None)
                    if p_obj is None:
                        p_obj = {"name": p, "subpages": []}
                        sub_file_tree += [p_obj]
                    if i == len(path) - 1 or (i == len(path) - 2 and path[i+1] == "index.htm"):
                        p_obj["link"] = file
                        break
                    else:
                        sub_file_tree = p_obj["subpages"]
        with codecs.open("file_tree.json", "wb", encoding="utf8") as fout:
            json.dump(self.file_tree, fout, indent=2, ensure_ascii=False)

    def extract_topic_headers(self, max_indent):
        with codecs.open("webshas2.json", "rb", encoding="utf8") as fin:
            jin = json.load(fin)
        rows = self.extract_topic_headers_recurse(jin, [])
        # rows = filter(lambda x: len(x["indent"]) < max_indent, rows)
        # rows = [x for x in rows if len(x["refs"]) == 0]
        # combine parents
        max_depth = 0
        ref_set = set()
        total_refs = 0
        for r in rows:
            if len(r['refs']) > 0:
                ref_list = list(r['refs'].split(', '))
                total_refs += len(ref_list)
                ref_set |= set(ref_list)
            if len(r["parents"]) > max_depth:
                max_depth = len(r["parents"])
            for i, p in enumerate(r["parents"]):
                r["level {}".format(i+1)] = p
            del r["parents"]
        smaller_files = {}
        for r in rows:
            num_cols = 0
            for k, v in r.items():
                if len(v) > 0:
                    num_cols += 1
            if num_cols == 1 and len(r['level 1']) > 0:
                smaller_files[r['level 1']] = []
        for r in rows:
            smaller_files[r['level 1']] += [r]
        for f, small_rows in smaller_files.items():
            temp_max_depth = 0
            for r in small_rows:
                num_cols = 0
                for k, v in r.items():
                    if len(v) > 0:
                        num_cols += 1
                if num_cols > temp_max_depth:
                    temp_max_depth = num_cols
            with open("small_parsed/webshas {}.csv".format(f.replace('/', ' - ')), 'w') as fout:
                c = csv.DictWriter(fout, ["level {}".format(i+1) for i in range(temp_max_depth-1)] + ["refs"])
                c.writeheader()
                c.writerows(small_rows)
        with open("topic_headers_with_refs.csv", "w") as fout:
            c = csv.DictWriter(fout, ["level {}".format(i+1) for i in range(max_depth)] + ["refs"])
            c.writeheader()
            c.writerows(rows)
        print("Total Refs", total_refs)
        print("Unique Refs", len(ref_set))

    def extract_topic_headers_recurse(self, children, parents, indent=0):
        rows = []
        for c in children:
            temp_rows = []
            temp_parents = parents + [c["text"]] if "text" in c else parents
            if "subtopics" in c:
                temp_rows = self.extract_topic_headers_recurse(c["subtopics"], temp_parents, indent + 1)
            if "text" in c and (("refs" in c and len(c["refs"]) > 0) or ("subtopics" in c and len(temp_rows) > 0)):
                rows += [{"refs": ", ".join(c.get("refs", [])), "parents": temp_parents}]
            rows += temp_rows
        return rows

    def get_all_links(self, curr_root):
        all_links = set()
        children = curr_root["subpages"] if isinstance(curr_root, dict) else curr_root
        for c in children:
            all_links |= self.get_all_links(c)
            if "link" in c:
                all_links.add(self.denormalize_href(c["link"]))
        return all_links

    def parse_file_tree(self):
        out = []
        # topic = "shabbos"
        # curr_root = next((x for x in self.file_tree if x["name"] == topic), None)
        self.all_links = self.get_all_links(self.file_tree)
        # self.file_tree = [{"link": "{}_index.htm".format(topic)}]
        for p_obj in self.file_tree:
            if "link" not in p_obj or not p_obj["link"].endswith("index.htm"):
                continue
            out += [self.parse_link(p_obj["link"], verbose=False)]
        self.leftover_links = [l for l in self.all_links]
        self.visited_links = set()
        out = []
        for p_obj in self.file_tree:
            if "link" not in p_obj or not p_obj["link"].endswith("index.htm"):
                continue
            try:
                out += [self.parse_link(p_obj["link"], verbose=False)]
            except InputError:
                pass
        print("LINKS UNTOUCHED {} -- {}".format(len(self.all_links), self.all_links))
        with codecs.open("webshas2.json", "wb", encoding="utf8") as fout:
            json.dump(out, fout, indent=2, encoding="utf8")

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

    def parse_list(self, ul, page_href, verbose=True):
        i_tag = ul.find_previous_sibling("i")
        if i_tag is None:
            # TODO no subtitle. still parse content
            title = None
        else:
            title = i_tag.get_text().strip()
            if verbose:
                print("> {}".format(title))
        out = {"text": title, "subtopics": []}
        links = []
        temp_line = []
        for item in ul.descendants:
            if item.parent != ul and (item.parent.name != "ul" or item.parent.parent != ul):
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
                        parsed_line, temp_links = self.parse_line(temp_line, page_href, title, verbose=verbose)
                        out["subtopics"] += [parsed_line]
                        links += temp_links
                        temp_line = []
                elif item.name == "ul":
                    # TODO find title
                    parsed_list, links = self.parse_list(item, page_href, verbose=verbose)
                    out["subtopics"] += [parsed_list]
            elif item.name == "a":
                temp_line += [item]
            else:
                print("UNKNOWN ELEMENT: {} - {}".format(item.name, item))
        return out, links

    def parse_link(self, l, verbose=True):

        page_href = self.denormalize_href(l)
        if page_href in self.all_links:
            self.all_links.remove(page_href)
        if page_href in self.visited_links:
            print("DONT REVISIT {}".format(page_href))
            raise InputError
        self.visited_links.add(page_href)
        page = self.get_page(page_href)
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
        out = {"text": title, "link": page_href, "subtopics": []}
        subtopic_list = subsoup.select("ul")
        if len(subtopic_list) == 0:
            # assume list a a_tags. use parent as list root
            subtopic_list = [h2.parent] + h2.parent.select("p")
        for ul in subtopic_list:
            parsed_list, links = self.parse_list(ul, page_href, verbose=verbose)
            if not parsed_list:
                continue
            if parsed_list["text"] is None:
                out["subtopics"] = parsed_list["subtopics"]
            else:
                out["subtopics"] += [parsed_list]



        return out

    def line2str(self, ln):
        return " ".join([i.strip() if isinstance(i, NavigableString) else i.get_text().strip() for i in ln])

    def parse_refs(self, refs):
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
                r = srefs[i - 1].index.title + r
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

    def normalize_href(self, href, page_href="", relative=True):
        href = href.replace(ROOT, "")
        href = href.strip()
        if re.search(r"^\s*(\.\./)+", href):
            href = re.sub(r"^\s*(\.\./)+", "", href)
        elif relative:
            page_href = page_href.replace(ROOT, "")
            try:
                page_loc = re.findall("(^.+)/[^/]+\.htm$", page_href)[0]
            except IndexError:
                page_loc = re.findall("(^[^/]+)/index\.htm$", page_href)[0]
            href = page_loc + "/" + href
        return ROOT + href

    def denormalize_href(self, href):
        href = href.replace(ROOT, "")
        return ROOT + href.replace("_", "/")

    def should_follow_link(self, page_href, new_href):
        """

        :param page_href:
        :param new_href:
        :return:
        """
        if new_href in self.leftover_links:
            top_level1 = re.findall("^" + ROOT + "[^/]+", page_href)
            top_level2 = re.findall("^" + ROOT + "[^/]+", new_href)
            if top_level1 == top_level2:
                print("LEFTOVERS: {} - {}".format(page_href, new_href))
                self.leftover_links.remove(new_href)
                return True
            else:
                print("REJECT LEOVER: {} - {}".format(page_href, new_href))
        page_href = re.sub(r"(?:/index|/general)?\.htm", "", page_href)
        return new_href.startswith(page_href)

    def parse_line(self, ln, page_href, subtopic, verbose=True):
        obj = {'links': []}
        links = []
        text = self.line2str(ln)
        just_a_link = False
        if (len(ln) == 1 and ln[0].name == "a") or subtopic == "Links":
            obj['text'] = text
            just_a_link = True
        else:
            text_split = re.split(r":(?=[^:]+$)", text)
            if len(text_split) != 2:
                print("WEIRD LINE: len {}".format(len(text_split)))
            else:
                text, refs = text_split
                obj['text'] = text
                obj['refs'] = self.parse_refs(refs)
        for elem in ln:
            if elem.name == 'a':
                href = self.normalize_href(elem['href'], page_href)
                if just_a_link:
                    links += [href]
                    # TODO deal with multiple links in one line
                    if 'links' in obj:
                        del obj['links']
                    obj['link'] = href
                    if self.should_follow_link(page_href, href):
                        try:
                            parsed_link = self.parse_link(href, verbose=verbose)
                        except InputError:
                            print("Couldn't parse: {}".format(href))
                            continue
                        obj['alt_text'] = parsed_link['text']
                        obj['subtopics'] = parsed_link['subtopics']
                else:
                    obj['links'] += [href]
        return obj, links

if __name__ == '__main__':
    wsp = WebShasParser()


"""
pages I'm still not sure are parsed
http://www.webshas.org/lead/kindness.htm
http://www.webshas.org/kinyan/shetar/simpon.htm
http://www.webshas.org/torah/tanna/yonasan.htm
http://www.webshas.org/torah/alpeh/lists.htm
http://www.webshas.org/kelal/shiurim/rimon.htm
http://www.webshas.org/kelal/pesak/rabbinic.htm
"""
