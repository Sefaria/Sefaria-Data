# encoding=utf-8

import os
import bs4
import re
import pymongo
import requests
from sefaria.model import *
from sefaria.settings import *
from sefaria.utils.hebrew import heb_string_to_int

mesechtot = ["Avodah Zarah", "Bava Batra", "Bava Kamma", "Bava Metzia", "Beitzah", "Berakhot", "Bikkurim", "Chagigah", "Challah", "Demai", "Eruvin", "Gittin", "Horayot", "Ketubot", "Kiddushin", "Kilayim", "Maaser Sheni", "Maasrot", "Makkot", "Megillah", "Moed Katan", "Nazir", "Nedarim", "Niddah", "Orlah", "Peah", "Pesachim", "Rosh Hashanah", "Sanhedrin", "Shabbat", "Shekalim", "Sheviit", "Shevuot", "Sotah", "Sukkah", "Taanit", "Terumot", "Yevamot", "Yoma"]
jtindxes = ["JTmock " + x for x in mesechtot]
g_version = "Guggenheimer"
m_version = "Mehon-Mamre"


def connect():
    client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
    return client["yerushalmi_work"]


def load_guggenheimer_data():
    db = connect()
    collection = "g_segs"
    db[collection].delete_many({})

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
                    "perek_num": perek_num,
                    "halacha_num": halacha_num,
                    "segment_num": i + 1,
                    "eng_type": "Mishna" if i == 0 else "Talmud",
                    "content": segment,
                    "mesechet": mesechet,
                    "index": index,
                    "num": run_num
                }
                db[collection].insert_one(d)




#add masechet
def load_machon_mamre_data():
    db = connect()
    collection = "mm_paras"
    db[collection].delete_many({})

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

                db[collection].insert_one(d)

#f1:
# result_file: f"/./comparison/{file_id}.xlsx"

def dicta_compare(fn1, fn2, result_fn):

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

    url_to_upload = f"https://synopsis-2-3-alt.loadbalancer.dicta.org.il/synopsis/api/synopsis/uploadfile/{file_id}"
    file1 = {'file': open(fn1, 'rb')}
    file2 = {'file': open(fn2, 'rb')}
    _r = requests.post(url_to_upload, files=file1)
    _r2 = requests.post(url_to_upload, files=file2)

    value1 = {'Grouping': 'None'}
    response_of_result = requests.post(f'https://synopsis-2-3-alt.loadbalancer.dicta.org.il/synopsis/api/synopsis/{file_id}',
                       data=value1)
    download_excel_url = response_of_result.json()["output_url"].replace(".",
                                                         "https://synopsis-2-3-alt.loadbalancer.dicta.org.il/synopsis",
                                                         1)
    print(download_excel_url)
    r = requests.get(download_excel_url)
    with open(result_fn, 'wb') as f:
        f.write(r.content)