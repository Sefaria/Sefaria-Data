# encoding=utf-8

import os
import bs4
import re
import html
import pymongo
import requests
import openpyxl
import functools
from itertools import cycle
from sefaria.model import *
from sefaria.settings import *
from sefaria.utils.hebrew import decode_hebrew_numeral, encode_small_hebrew_numeral
from sefaria.datatype.jagged_array import JaggedTextArray


mesechtot = ["Avodah Zarah", "Bava Batra", "Bava Kamma", "Bava Metzia", "Beitzah", "Berakhot", "Bikkurim", "Chagigah", "Challah", "Demai", "Eruvin", "Gittin", "Horayot", "Ketubot", "Kiddushin", "Kilayim", "Maaser Sheni", "Maasrot", "Makkot", "Megillah", "Moed Katan", "Nazir", "Nedarim", "Niddah", "Orlah", "Peah", "Pesachim", "Rosh Hashanah", "Sanhedrin", "Shabbat", "Shekalim", "Sheviit", "Shevuot", "Sotah", "Sukkah", "Taanit", "Terumot", "Yevamot", "Yoma"]
jtindxes = ["JTmock " + x for x in mesechtot]

g_version = "Guggenheimer"
g_collection = "g_segs"

m_collection = "mm_paras"

v_version = "Venice"
v_collection = "v_columns"

comp_collection = "comparison"


def connect():
    client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
    return client["yerushalmi_work"]


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


word_split_re = re.compile(r"\s+")
def word_count(s):
    return len(word_split_re.split(s.strip()))


class MishnahAlignment(object):

    def __init__(self, valign_obj, mesechet, perek, halacha, skip_mishnah=False):
        self.mesechet = mesechet
        self.perek = int(perek)
        self.halacha = int(halacha)
        self.skip_mishnah = skip_mishnah    # Only align talmud/halacha sections
        self.valign_obj = valign_obj
        self.working_dir = valign_obj.working_dir  # "./comparison"

        self.a = self._process_version(valign_obj.v_a)  # name, records, ja, text
        self.b = self._process_version(valign_obj.v_b)

        self._raw_comparison_data = None        # mfirst   #v1first
        self._b2a_map = None
        self._a2b_map = None
        self.a_according_to_b = []

        self._mark_a()

    def _process_version(self, v):
        records = self._get_records_from_db(v.collection)
        if v.needs_escaping:
            raw_content = [html.escape(r["content"]) for r in records]
        else:
            raw_content = [r["content"] for r in records]
        ja = AnnotatedJTA(raw_content)

        return {
            "name": v.name,
            "records": records,
            "ja": ja,
            "text": ja.flatten_to_string()
        }

    def _get_records_from_db(self, collection):
        db = connect()
        query = {"mesechet": self.mesechet,
                 "perek_num": self.perek,
                 "halacha_num": self.halacha
                 }

        if self.skip_mishnah:
            query["eng_type"] = "Talmud"

        records = db[collection].find(query).sort("num", pymongo.ASCENDING)
        return [r for r in records]

    def get_latest_a_mark(self):
        return self.a["records"][-1]["daf_num"]

    def _mark_a(self):
        latest_page = self.valign_obj.latest_a_mark
        for i, r in enumerate(self.a["records"]):
            if r["daf_num"] == latest_page:
                continue
            latest_page = r["daf_num"]
            self.a["ja"].add_marker_before(i, latest_page)

    def xlsx_file(self):
        return f"{self.working_dir}/{self.mesechet}.{self.perek}.{self.halacha}-comp-{self.a['name']}-{self.b['name']}.xlsx"

    def run_compare(self):
        part = f"{self.mesechet}.{self.perek}.{self.halacha}"
        print(f"Comparing {part}")
        a_file = f"{self.working_dir}/{part}-{self.a['name']}.txt"
        b_file = f"{self.working_dir}/{part}-{self.b['name']}.txt"

        with open(a_file, 'w') as f:
            f.write(self.a["text"])

        with open(b_file, 'w') as f:
            f.write(self.b["text"])

        self.dicta_compare(a_file, b_file, self.xlsx_file())

    def dicta_compare(self, fn1, fn2, result_fn):

        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Origin': 'https://synoptic.dicta.org.il',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Referer': 'https://synoptic.dicta.org.il/',
            'Sec-GPC': '1',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
        }
        response_of_id = requests.post('https://synopsis-2-3-alt.loadbalancer.dicta.org.il/synopsis/api/synopsis/uploadfile/0',
                                 headers=headers)
        file_id = response_of_id.json()["id"]
        print(f"Dicta ID {file_id}")
        url_to_upload = f"https://synopsis-2-3-alt.loadbalancer.dicta.org.il/synopsis/api/synopsis/uploadfile/{file_id}"
        file1 = {'file': open(fn1, 'rb')}
        file2 = {'file': open(fn2, 'rb')}
        _r = requests.post(url_to_upload, files=file1)
        _r2 = requests.post(url_to_upload, files=file2)

        value1 = {'Grouping': 'None'}
        response_of_result = requests.post(f'https://synopsis-2-3-alt.loadbalancer.dicta.org.il/synopsis/api/synopsis/{file_id}',
                           data=value1)
        try:
            download_excel_url = response_of_result.json()["output_url"].replace(".",
                                                             "https://synopsis-2-3-alt.loadbalancer.dicta.org.il/synopsis",
                                                             1)
        except KeyError:
            print("Error in Response")
            raise Exception("Dicta API returned error")
        print(f"Getting Excel file: {download_excel_url}")
        r = requests.get(download_excel_url)
        with open(result_fn, 'wb') as f:
            f.write(r.content)

    def import_xlsx(self):
        filename = self.xlsx_file()
        workbook = openpyxl.load_workbook(filename)
        sheet = workbook.active
        afirst = self.a['name'] in sheet["A1"].value        # Presumes that one name isn't a subset of other
        self._raw_comparison_data = [[c.value for c in r] if afirst else [c.value for c in r[::-1]] for r in sheet.iter_rows(min_row=2, max_col=2)]

        self._b2a_map = {0: 0}
        self._a2b_map = {0: 0}
        g_word_count = m_word_count = 0
        for row in self._raw_comparison_data:
            mword = row[0]
            mlength = 0 if mword is None else len(word_split_re.split(mword))        # Same logic as used to split words in JA
            m_word_count += mlength

            gword = row[1]
            glength = 0 if gword is None else len(word_split_re.split(mword))        # Same logic as used to split words in JA
            g_word_count += glength

            self._b2a_map[g_word_count] = m_word_count
            self._a2b_map[m_word_count] = g_word_count

    def a2b(self, m):
        return self._a2b_map[m]

    def b2a(self, g):
        return self._b2a_map[g]

    def get_a_according_to_b(self):
        a_text_array = word_split_re.split(self.a["text"])
        try:
            a_ends = [self.b2a(l) for l in self.b["ja"].accumulated_lengths] + [None]
        except KeyError as e:
            print(f"{self.mesechet}.{self.perek}.{self.halacha}")
            print(e)
            raise

        a_begins = [0] + a_ends[:-1]
        self.a_according_to_b = [" ".join(a_text_array[s:f]) for s, f in zip(a_begins, a_ends)]  # This won't work for Guggenheimer, where there's makaf
        return self.a_according_to_b

    def save_comparison_data(self):
        d = {
            "perek_num": self.perek,
            "halacha_num": self.halacha,
            "mesechet": self.mesechet,
            "raw_comparison": self._raw_comparison_data,
            "a": self.a["name"],
            "b": self.b["name"],
            "a2b": self._a2b_map,
            "b2a": self._b2a_map,
            "a_according_to_b": self.a_according_to_b,
        }
        db = connect()
        db[comp_collection].insert_one(d)


class JVersion(object):
    def __init__(self, name, collection, needs_escaping=False):
        self.name = name
        self.collection = collection
        self.needs_escaping = needs_escaping

gugg = JVersion("Gugg", "g_segs", needs_escaping=False)
mm = JVersion("Machon", "mm_paras", needs_escaping=True)
venice = JVersion("Venice", "v_columns", needs_escaping=False)


class VersionAlignment(object):
    def __init__(self, working_dir, v_a, v_b, skip_mishnah=False):
        self.working_dir = working_dir
        self.v_a = v_a
        self.v_b = v_b
        self.errors = []
        self.latest_a_mark = None
        self.skip_mishnah = skip_mishnah

    def make_version_obj(self, index_title, new_version_title, new_version_source, content):
        Version({
            "language": "he",
            "title": index_title,
            "versionSource": new_version_source,
            "versionTitle": new_version_title,
            "chapter": content
        }).save()

    def generate_comparisons(self):
        for mesechet, index in [q for q in zip(mesechtot, jtindxes)]:
            base_ref = Ref(index)  # text is depth 3.

            for perek in base_ref.all_subrefs():
                perek_num = int(perek.normal_section(0))

                for halacha in perek.all_subrefs():
                    halacha_num = int(halacha.normal_section(1))

                    try:
                        ma = MishnahAlignment(self, mesechet, perek_num, halacha_num, self.skip_mishnah)
                        ma.run_compare()
                    except IndexError:
                        self.errors += [f"*** Failed to align {mesechet} {perek_num}:{halacha_num}"]
                    except Exception as e:
                        self.errors += [f"*** {str(e)} *** {mesechet} {perek_num}:{halacha_num}"]

    def create_new_versions(self, new_version_title, new_version_source):
        for mesechet, index in [q for q in zip(mesechtot, jtindxes)]:
            base_ref = Ref(index)  # text is depth 3.
            self.latest_a_mark = None
            version_content = []

            for perek in base_ref.all_subrefs():
                perek_num = int(perek.normal_section(0))
                perek_content = []

                for halacha in perek.all_subrefs():
                    halacha_num = int(halacha.normal_section(1))

                    try:
                        ma = MishnahAlignment(self, mesechet, perek_num, halacha_num)
                        self.latest_a_mark = ma.get_latest_a_mark()
                        ma.import_xlsx()
                        perek_content += [ma.get_a_according_to_b()]
                    except FileNotFoundError:
                        perek_content += [[]]
                        self.errors += [f"Missing {halacha.normal()}"]
                    except (KeyError, IndexError):
                        perek_content += [[]]
                        self.errors += [f"Mis-alignment of {halacha.normal()}"]

                version_content += [perek_content]

            print(f"Creating {mesechet}")
            self.make_version_obj(index, new_version_title, new_version_source, version_content)


class TaggedTextBlock(object):
    """
    רִבִּי יוּדָן בְּעָא. כְּמָאן דְּאָמַר. הוּא אֵינוֹ חַייָב עַל הַחֲלִיצָה אֲבָל חַייָב הוּא עַל הַצָּרָה. חֲלִיצָה פְּטוֹר. בִּיאָה פְּטוֹר. כְּמַה דְתֵימַר. חָלַץ לָהּ נֶאֶסְרָה לָאַחִין. וְדִכְװָתָהּ בָּא עָלֶיהָ נֶאֶסְרָה לָאַחִין. תַּנֵּי רִבִּי חִייָה. מֵת הָרִאשׁוֹן יְיַבֵּם הַשֵּׁינִי. מֵת הַשֵּׁינִי יְיַבֵּם הַשְּׁלִישִׁי. אָמַר רִבִּי יוֹסֵי מַה אַתְּ סָבַר. הִיא חֲלִיצָה הִיא <i data-overlay="Venice Pages" data-value="2d"></i>בִּיאָה. כֵּיוָן שֶׁחָלַץ לָהּ נֶעֶקְרָה הִימֶּינָּה זִיקַת הַמֵּת לְמַפְרֵיעָה. לְמַפְרֵיעָה חָל עָלֶיהָ אִיסּוּרוֹ שֶׁלְּמֵת אֵצֶל הָאַחִין. אֲבָל אִם בָּא עָלֶיהָ אִשְׁתּוֹ הִיא. וְתַנֵּי רִבִּי חִייָה. מֵת הָרִאשׁוֹן יְיַבֵּם הַשֵּׁינִי. מֵת הַשֵּׁינִי יְיַבֵּם הַשְּׁלִישִׁי.
    """
    tag_pattern = re.compile(r"(<[^<]+>)")

    def __init__(self, content):
        self._raw_content = content
        self._parts = self._decompose()

    def _decompose(self):
        typer = cycle(["text", "tag"])
        parts = [{
            "content": p,
            "type": next(typer)
        } for p in self.tag_pattern.split(self._raw_content)]
        parts = [p for p in parts if p["content"]]  # Remove blanks in between/before/after tags
        running_length = 0
        for p in parts:
            if p["type"] == "text":
                p["start"] = running_length

                white_start = re.search("^\s+", p["content"])
                white_end = re.search("\s+$", p["content"])
                p["white_start"] = white_start.group() if white_start else ""
                p["white_end"] = white_end.group() if white_end else ""
                p["content"] = p["content"].strip()
                words = word_split_re.split(p["content"])
                word_len = len(words)
                running_length += word_len

                p["word_array"] = words
                p["word_count"] = word_len
                p["end"] = running_length

        return parts


    def insert_tag_after_word(self, after_word_num, tag, attrs):
        """

        :param after_word_num: 0 means at the beginning
        :param tag:
        :param attrs:
        :return:
        """
        attr_string = " ".join([f"{a} = '{b}'" for a, b in attrs.items()])
        open_tag = {
            "content": f"<{tag} {attr_string}>",
            "type": "tag"
        }
        close_tag = {
            "content": f"</{tag}>",
            "type": "tag"
        }

        # Find the right part
        part_indx = [i for i, p in enumerate(self._parts) if p["start"] < after_word_num < p["end"]][0]
        initial_part = self._parts[part_indx]

        split_pos = after_word_num - initial_part["start"]
        first_content = initial_part["content"][:split_pos]
        second_content = initial_part["content"][split_pos:]

        # cut the part into two
        first_part = {
            "type": "text",
            "word_array": first_content,
            "content": " ".join(first_content),
            "start": initial_part["start"],
            "word_count": split_pos,
            "end": initial_part["start"] + split_pos,
            "white_start": initial_part["white_start"],
            "white_end": " "
        }
        second_part = {
            "type": "text",
            "word_array": second_content,
            "content": " ".join(second_content),
            "start": initial_part["start"] + split_pos,
            "word_count": len(second_content),
            "end": initial_part["end"],
            "white_start": "",
            "white_end": initial_part["white_end"]
        }

        # insert tags in between
        self._parts = self._parts[:part_indx - 1] + [first_part, open_tag, close_tag, second_part] + self._parts[part_indx:]
        return self

    def as_text(self):
        s = ""
        for p in self._parts:
            if p["type"] == "tag":
                s += p["content"]
            elif p["type"] == "text":
                s += p["white_start"] + p["content"] + p["white_end"]
        return s


class AnnotatedJTA(JaggedTextArray):
    """
    For our purposes, we're assuming depth 1.
    """
    def __init__(self, ja=None):
        super(AnnotatedJTA, self).__init__(ja)
        self._store = [TextChunk._strip_itags(_) for _ in self._store]
        self._lengths = [word_count(seg) for seg in self._store]
        self.accumulated_lengths = functools.reduce(lambda a,u: a + [u + a[-1]], self._lengths, [0])[1:]    # Add lengths up to get accumulated length.  Slice at end removes initial 0.
        self._markers = [None] * (len(self._store))  # markers for before each segment


    def add_marker_before(self, before, marker):
        """

        :param before: before which segment to put the marker, base 0
        :param marker: What to place in the marker
        :return:
        """
        self._markers[before] = marker


def load_guggenheimer_data():
    db = connect()
    db[g_collection].delete_many({})

    for mesechet, index in zip(mesechtot, jtindxes):
        base_ref = Ref(index)          # text is depth 3.
        all_halachot = [halacha for perek in base_ref.all_subrefs() for halacha in perek.all_subrefs()]
        run_num = 0
        for halacha in all_halachot:
            perek_num = halacha.normal_section(0)
            halacha_num = halacha.normal_section(1)
            tc = TextChunk(halacha, vtitle=g_version, lang="he")
            for i, segment in enumerate(tc.text):
                run_num += 1
                d = {
                    "perek_num": int(perek_num),
                    "halacha_num": int(halacha_num),
                    "segment_num": i + 1,
                    "eng_type": "Mishna" if i == 0 else "Talmud",
                    "content": segment,
                    "mesechet": mesechet,
                    "index": index,
                    "num": run_num
                }
                db[g_collection].insert_one(d)


def load_venice_data():
    db = connect()
    db[v_collection].delete_many({})

    html_dir = 'Venice'
    input_files = [f for f in os.listdir(html_dir) if f.endswith('txt')]

    '''  Double header_pattern
    תלמוד ירושלמי (ונציה) מסכת בבא מציעא פרק א דף ז טור ד /מ"ב

    תלמוד ירושלמי (ונציה) מסכת בבא מציעא פרק א דף ז טור ד /מ"ב
    '''
    # ('יומא', 'ד', 'מא', 'ג', 'ה"א')  Results of split


    header_pattern = "תלמוד ירושלמי \(ונציה\) מסכת" + " (.+) " + "פרק" + " (.+) " + "דף" + " (.+) " + "טור" + " (.+) " + "/" + "(.+)" + r"[\n\s]+"
    page_pattern = re.compile(header_pattern + header_pattern)

    # Section
    # /ה"ג/  Three spaces preceed, one follows
    #  /מי"א/ /מ"ז/  Two spaces precede mishnah, one follows
    section_pattern = re.compile("/" + "([מה])" + '([\u05d0-\u05ea"]+)' + "/")

    for file in input_files:
        with open(os.path.join(html_dir, file)) as fp:
            mesechet = Ref(file.replace(".txt", "")).normal().replace("Mishnah ", "")
            print(mesechet)

            def key_pages(d):
                # d: mesechet, perek, daf, tur, segment, mesechet, perek, daf, tur, segment, content
                # Generate dict from item i with list d
                # Get's mesechet from outer loop
                section_type_letter = d[4][0]       # מ or ה
                section_num = decode_hebrew_numeral(d[4][1:].replace('"', ''))
                return {
                    "mesechet": mesechet,
                    "perek": d[1],
                    "perek_num": decode_hebrew_numeral(d[1]),
                    "daf": d[2],
                    "daf_num": decode_hebrew_numeral(d[2]),
                    "tur": d[3],
                    "tur_num": decode_hebrew_numeral(d[3]),
                    "content": d[10].strip(),
                    "eng_type":  "Mishna" if section_type_letter == "מ" else "Talmud",
                    "section_num": section_num
                }

            content = fp.read()
            result = page_pattern.split(content)[1:]     # Trim off initial blank value
            pages = map(key_pages, chunks(result, 11))
            run_num = 0
            for page in pages:
                section_list = section_pattern.split(page["content"])
                section_label_begins_page = False
                if section_list[0]:
                    # First one will use all metadata from the page object, later ones will replace mishnah / halacha
                    run_num += 1
                    first_section = page.copy()
                    first_section["content"] = section_list[0].strip()
                    first_section["num"] = run_num
                    if first_section["eng_type"] == "Talmud":              # For portability of comparison code
                        first_section["halacha_num"] = first_section["section_num"]
                    db[v_collection].insert_one(first_section)
                else:
                    section_label_begins_page = True

                for i,l in enumerate(chunks(section_list[1:], 3)):
                    run_num += 1
                    if i > 0 or not section_label_begins_page:
                        # The general case - not at the beginning of the page
                        if l[0] == "מ" and l[1].replace('"', '') == "א":
                            # a /מ"א/ indicates that the perek has turned.
                            # Change page data so all subsequent matches get new data
                            page["perek_num"] += 1
                            page["perek"] = encode_small_hebrew_numeral(page["perek_num"])
                    section_d = page.copy()
                    section_d["eng_type"] = "Mishna" if l[0] == "מ" else "Talmud"
                    section_d["section_num"] = decode_hebrew_numeral(l[1].replace('"',''))
                    if section_d["eng_type"] == "Talmud":                  # For portability of comparison code
                        section_d["halacha_num"] = section_d["section_num"]
                    section_d["content"] = l[2].strip()
                    section_d["num"] = run_num
                    db[v_collection].insert_one(section_d)


def load_machon_mamre_data():
    db = connect()
    db[m_collection].delete_many({})

    html_dir = 'mechon-mamre'
    input_files = [f for f in os.listdir(html_dir) if f.endswith('html')]
    pattern = re.compile(
        "דף " + "(?P<daf>.+),(?P<amud>.+) " + "פרק" + " (?P<perek>.+) " + "הלכה" + " (?P<halacha>.+) " + "(?P<type>משנה|גמרא)")
    for file in input_files:
        with open(os.path.join(html_dir, file)) as fp:
            # Load raw data
            mesechet = Ref(file.replace(".html", "")).normal().replace("Mishnah ","")
            soup = bs4.BeautifulSoup(fp, 'lxml')
            headings = soup.select("div p b")
            for i, heading in enumerate(headings):
                citation = heading.get_text()
                match = pattern.match(citation)
                d = match.groupdict()  # {'daf': 'לב', 'amud': 'א', 'perek': 'ז', 'halacha': 'ד', 'type': 'גמרא'}
                d["eng_type"] = "Mishna" if d["type"] == "משנה" else "Talmud"
                d["mesechet"] = mesechet
                d["content"] = heading.next_sibling.strip()
                d["perek_num"] = decode_hebrew_numeral(d["perek"])
                d["daf_num"] = str(decode_hebrew_numeral(d["daf"])) + ("a" if d["amud"] == 'א' else "b")
                d["num"] = i + 1
                try:
                    d["halacha_num"] = decode_hebrew_numeral(d["halacha"])
                except KeyError:  # 'halacha': '(ב) ג'
                    d["halacha_num"] = decode_hebrew_numeral(d["halacha"][-1])

                db[m_collection].insert_one(d)
