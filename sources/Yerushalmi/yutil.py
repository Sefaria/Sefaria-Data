# encoding=utf-8

import os
import bs4
import re
import pymongo
import requests
import openpyxl
import functools
from sefaria.model import *
from sefaria.settings import *
from sefaria.utils.hebrew import heb_string_to_int
from sefaria.datatype.jagged_array import JaggedTextArray


mesechtot = ["Avodah Zarah", "Bava Batra", "Bava Kamma", "Bava Metzia", "Beitzah", "Berakhot", "Bikkurim", "Chagigah", "Challah", "Demai", "Eruvin", "Gittin", "Horayot", "Ketubot", "Kiddushin", "Kilayim", "Maaser Sheni", "Maasrot", "Makkot", "Megillah", "Moed Katan", "Nazir", "Nedarim", "Niddah", "Orlah", "Peah", "Pesachim", "Rosh Hashanah", "Sanhedrin", "Shabbat", "Shekalim", "Sheviit", "Shevuot", "Sotah", "Sukkah", "Taanit", "Terumot", "Yevamot", "Yoma"]
jtindxes = ["JTmock " + x for x in mesechtot]

g_version = "Guggenheimer"
g_collection = "g_segs"

m_version = "Mehon-Mamre"
m_collection = "mm_paras"

comp_collection = "comparison"

def connect():
    client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
    return client["yerushalmi_work"]

class MishnahAlignment(object):
    working_dir = "./comparison"

    def __init__(self, mesechet, perek, halacha, initial_latest_page=None):
        self.mesechet = mesechet
        self.perek = int(perek)
        self.halacha = int(halacha)

        self._raw_comparison_data = None        # mfirst
        self._g2m_map = None
        self._m2g_map = None

        self.g_records = self._get_records_from_db(g_collection)
        self.g_ja = self._get_ja_from_records(self.g_records)
        self.g_text = self.g_ja.flatten_to_string()

        self.m_records = self._get_records_from_db(m_collection)
        self.m_ja = self._get_ja_from_records(self.m_records)
        self.m_text = self.m_ja.flatten_to_string()
        self.m_according_to_g = []
        self._mark_mm_pages(initial_latest_page)


    def _get_records_from_db(self, collection):
        db = connect()
        records = db[collection].find({"mesechet": self.mesechet,
                                         "perek_num": self.perek,
                                         "halacha_num": self.halacha
                                         }).sort("num", pymongo.ASCENDING)
        return [r for r in records]

    def _get_ja_from_records(self, records):
        content = [r["content"] for r in records]
        return AnnotatedJTA(content)

    def _mark_mm_pages(self, latest_page = None):
        latest_page = latest_page or self.m_records[0]["daf_num"]
        for i, r in enumerate(self.m_records):
            if r["daf_num"] == latest_page:
                continue
            latest_page = r["daf_num"]
            self.m_ja.add_marker_before(i, latest_page)

    def xlsx_file(self):
        return f"{self.working_dir}/{self.mesechet}.{self.perek}.{self.halacha}-comp.xlsx"

    def run_compare(self):
        part = f"{self.mesechet}.{self.perek}.{self.halacha}"
        print(f"Comparing {part}")
        m_file = f"{self.working_dir}/{part}-m.txt"
        g_file = f"{self.working_dir}/{part}-g.txt"

        with open(m_file, 'w') as f:
            f.write(self.m_text)

        with open(g_file, 'w') as f:
            f.write(self.g_text)

        self.dicta_compare(m_file, g_file, self.xlsx_file())

    #f1:
    # result_file: f"/./comparison/{file_id}.xlsx"

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
        mfirst = "-m" in sheet["A1"].value
        self._raw_comparison_data = [[c.value for c in r] if mfirst else [c.value for c in r[::-1]] for r in sheet.iter_rows(min_row=2, max_col=2)]

        self._g2m_map = {0: 0}
        self._m2g_map = {0: 0}
        g_word_count = m_word_count = 0
        for row in self._raw_comparison_data:
            mword = row[0]
            mlength = 0 if mword is None else len(re.split(r"[\s\u05be]+", mword))        # Same logic as used to split words in JA
            m_word_count += mlength

            gword = row[1]
            glength = 0 if gword is None else len(re.split(r"[\s\u05be]+", gword))        # Same logic as used to split words in JA
            g_word_count += glength

            self._g2m_map[g_word_count] = m_word_count
            self._m2g_map[m_word_count] = g_word_count

    def m2g(self, m):
        return self._m2g_map[m]

    def g2m(self, g):
        return self._g2m_map[g]

    def get_m_according_to_g(self):
        m_text_array = re.split(r"[\s\u05be]+", self.m_text)
        try:
            m_ends = [self.g2m(l) for l in self.g_ja.accumulated_lengths] + [None]
        except KeyError as e:
            print(f"{self.mesechet}.{self.perek}.{self.halacha}")
            print(e)
            raise

        m_begins = [0] + m_ends[:-1]
        self.m_according_to_g = [" ".join(m_text_array[s:f]) for s, f in zip(m_begins, m_ends)]  # This won't work for Guggenheimer, where there's makaf
        return self.m_according_to_g

    def save_comparison_data(self):
        d = {
            "perek_num": self.perek,
            "halacha_num": self.halacha,
            "mesechet": self.mesechet,
            "raw_comparison": self._raw_comparison_data,
            "m2g": self._m2g_map,
            "g2m": self._g2m_map,
            "m_according_to_g": self.m_according_to_g,
        }
        db = connect()
        db[comp_collection].insert_one(d)


class AnnotatedJTA(JaggedTextArray):
    """
    For our purposes, we're assuming depth 1.
    """
    def __init__(self, ja=None):
        super(AnnotatedJTA, self).__init__(ja)
        self._store = [TextChunk._strip_itags(_) for _ in self._store]
        self._lengths = [self._wcnt(seg) for seg in self._store]
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
            paras = []
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
                d["perek_num"] = heb_string_to_int(d["perek"])
                d["daf_num"] = str(heb_string_to_int(d["daf"])) + ("a" if d["amud"] == 'א' else "b")
                d["num"] = i + 1
                try:
                    d["halacha_num"] = heb_string_to_int(d["halacha"])
                except KeyError:  # 'halacha': '(ב) ג'
                    d["halacha_num"] = heb_string_to_int(d["halacha"][-1])

                db[m_collection].insert_one(d)
