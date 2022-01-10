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
from sefaria.model.schema import AddressType
from sefaria.settings import *
from sefaria.utils.hebrew import decode_hebrew_numeral, encode_small_hebrew_numeral
from sefaria.datatype.jagged_array import JaggedTextArray
from sefaria.system.exceptions import BookNameError


mesechtot = ["Avodah Zarah", "Bava Batra", "Bava Kamma", "Bava Metzia", "Beitzah", "Berakhot", "Bikkurim", "Chagigah", "Challah", "Demai", "Eruvin", "Gittin", "Horayot", "Ketubot", "Kiddushin", "Kilayim", "Maaser Sheni", "Maasrot", "Makkot", "Megillah", "Moed Katan", "Nazir", "Nedarim", "Niddah", "Orlah", "Peah", "Pesachim", "Rosh Hashanah", "Sanhedrin", "Shabbat", "Shekalim", "Sheviit", "Shevuot", "Sotah", "Sukkah", "Taanit", "Terumot", "Yevamot", "Yoma"]
jtindxes = ["Jerusalem Talmud " + x for x in mesechtot]

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
    """
    b provides the segmentation
    tools to rewrite a, according to segmentation of b
    tools to insert markers into b, according to marks in a
    """
    def __init__(self, mesechet, perek, halacha, v_a, v_b, working_dir, starting_a_mark=None, skip_mishnah=False):
        self.mesechet = mesechet
        self.perek = int(perek)
        self.halacha = int(halacha)
        self.skip_mishnah = skip_mishnah    # Only align talmud/halacha sections
        self.working_dir = working_dir  # "./comparison"
        self.starting_a_mark = starting_a_mark

        self.a = self._process_version(v_a)  # name, records, ja, text
        self.b = self._process_version(v_b)

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
            "v": v,
            "name": v.name,
            "records": records,
            "ja": ja,
            "text": ja.flatten_to_string()
        }

    def _get_mishnah_content(self, v):
        db = connect()
        query = {"mesechet": self.mesechet,
                 "perek_num": self.perek,
                 "halacha_num": self.halacha,
                 "eng_type": "Mishna"
                 }
        records = db[v.collection].find(query)
        if records.count() > 1:
            print(f"Found more than one Mishnah for {self.mesechet} {self.perek} {self.halacha}")
        r = records[0]
        return html.escape(r["content"]) if v.needs_escaping else r["content"]

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
        latest_page = self.starting_a_mark
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
        b_word_count = a_word_count = 0
        for row in self._raw_comparison_data:
            aword = row[0]
            alength = 0 if aword is None else len(word_split_re.split(aword))
            a_word_count += alength

            bword = row[1]
            blength = 0 if bword is None else len(word_split_re.split(bword))
            b_word_count += blength

            self._b2a_map[b_word_count] = a_word_count
            self._a2b_map[a_word_count] = b_word_count

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
        self.a_according_to_b = [""] if self.skip_mishnah else []
        self.a_according_to_b += [" ".join(a_text_array[s:f]) for s, f in zip(a_begins, a_ends)]  # This won't work for Guggenheimer, where there's makaf
        return self.a_according_to_b


    def get_b_with_a_marks(self, overlay):
        # Return all b's in range, mutated to include a marks
        marker_apos_dict = self.a["ja"].get_marker_word_positions()
        marker_bpos_dict = {self.a2b(a_pos): marker for a_pos, marker in marker_apos_dict.items()}
        marker_positions = marker_bpos_dict.keys()

        new_b = [self._get_mishnah_content(self.b["v"])] if self.skip_mishnah else []
        for section, start, end in self.b["ja"].get_sections_and_ranges():
            # For section in b
            ttb = TaggedTextBlock(section)
            for mp in marker_positions:
                # if there's are a marks in the range, mutate b
                if start <= mp < end:
                    ttb.insert_tag_after_word(mp - start, "i", {"data-overlay": overlay, "data-value": marker_bpos_dict[mp]})
            new_b += [ttb.as_text()]

        return new_b

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
    def __init__(self, name, collection, overlay=None, needs_escaping=False):
        self.name = name
        self.collection = collection
        self.overlay = overlay
        self.needs_escaping = needs_escaping

gugg = JVersion("Gugg", "g_segs", needs_escaping=False)
mm = JVersion("Machon", "mm_paras", "Vilna Pages", needs_escaping=True)
venice = JVersion("Venice", "v_columns", "Venice Columns", needs_escaping=False)


class VersionAlignment(object):
    def __init__(self, v_a, v_b, working_dir, skip_mishnah=False):
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
                        ma = MishnahAlignment(mesechet, perek_num, halacha_num, self.v_a, self.v_b, self.working_dir, self.latest_a_mark, self.skip_mishnah)
                        ma.run_compare()
                    except IndexError:
                        self.errors += [f"*** Failed to align {mesechet} {perek_num}:{halacha_num}"]
                    except Exception as e:
                        self.errors += [f"*** {str(e)} *** {mesechet} {perek_num}:{halacha_num}"]

    def annotate_base(self):
        """
        Add annotations in b reflecting the structure of a
        :return:
        """
        for mesechet, index in [q for q in zip(mesechtot, jtindxes)]:
            base_ref = Ref(index)  # text is depth 3.
            version_content = []

            for perek in base_ref.all_subrefs():
                perek_num = int(perek.normal_section(0))
                perek_content = []

                for halacha in perek.all_subrefs():
                    halacha_num = int(halacha.normal_section(1))

                    try:
                        ma = MishnahAlignment(mesechet, perek_num, halacha_num, self.v_a, self.v_b, self.working_dir,
                                                     starting_a_mark=self.latest_a_mark, skip_mishnah=self.skip_mishnah)
                        ma.import_xlsx()
                        perek_content += [ma.get_b_with_a_marks(self.v_a.overlay)]

                        self.latest_a_mark = ma.get_latest_a_mark()

                    except FileNotFoundError:
                        perek_content += [[]]
                        self.errors += [f"Missing {halacha.normal()}"]
                    except (KeyError, IndexError):
                        perek_content += [[]]
                        self.errors += [f"Mis-alignment of {halacha.normal()}"]

                version_content += [perek_content]

            print(f"Creating {mesechet}")
            self.make_version_obj(index, f"With {self.v_a.overlay}", "foo", version_content)


#Guggenheimer

    def create_new_versions(self, new_version_title, new_version_source):
        """
        Create a version of `a` according to the structure of `b`
        :param new_version_title:
        :param new_version_source:
        :return:
        """

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
                        ma = MishnahAlignment(mesechet, perek_num, halacha_num, self.v_a, self.v_b, self.working_dir, starting_a_mark=self.latest_a_mark, skip_mishnah=self.skip_mishnah)
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


class OverlayBuilder(object):
    def __init__(self, versionTitle, overlayName, alt_struct_name, addressType, sectionName):
        self.versionTitle = versionTitle
        self.overlayName = overlayName
        self.addressType = addressType
        self.sectionName = sectionName
        self.alt_struct_name = alt_struct_name

    def setAllAltStructs(self):
        for mesechet, index in [q for q in zip(mesechtot, jtindxes)]:
            try:
                bavli_index = library.get_index(mesechet)
            except BookNameError:
                bavli_index = None
            yerushalmi_index_ref = Ref(index)
            alt_struct = self.getAltStructForMesechet(bavli_index, yerushalmi_index_ref)

            ind = library.get_index(index)
            assert isinstance(ind, Index)
            ind.set_alt_structure(self.alt_struct_name, alt_struct)
            ind.save()

    def getAltStructForMesechet(self, bavli_index, yerushalmi_index_ref):
        yerushalmi_chapters = yerushalmi_index_ref.all_subrefs()

        if bavli_index and bavli_index.get_alt_structure("Chapters"):
            bavli_chapters = bavli_index.get_alt_structure("Chapters").children
        else:
            bavli_chapters = [None] * len(yerushalmi_chapters)

        latest_addr = None

        alt_struct = TitledTreeNode()

        chapter = 0
        for bc, yc in zip(bavli_chapters, yerushalmi_chapters):
            chapter += 1
            amn = ArrayMapNode()
            amn.add_primary_titles(
                bc.get_primary_title("en") if bc is not None else "Chapter " + str(chapter),
                bc.get_primary_title("he") if bc is not None else "פרק " + encode_small_hebrew_numeral(chapter))
            amn.depth = 1
            amn.addressTypes = [self.addressType]
            amn.sectionNames = [self.sectionName]

            try:
                addr_ranges = self.getAddressRangesForPerek(yc, latest_addr)
            except IndexError:  # no marks, skip this one
                continue

            amn.startingAddress = addr_ranges[0]["addr"]
            amn.refs = [r["start"].to(r["end"]).normal() for r in addr_ranges]
            amn.wholeRef = addr_ranges[0]["start"].to(addr_ranges[-1]["end"]).normal()

            alt_struct.append(amn)
            latest_addr = addr_ranges[-1]["addr"]

        return alt_struct

    def areAllAddressInOrder(self):
        for index in jtindxes:
            yerushalmi_index = Ref(index)
            self.areAddressesInOrder(yerushalmi_index)

    def areAddressesInOrder(self, yerushalmi_index_ref):
        yerushalmi_chapters = yerushalmi_index_ref.all_subrefs()
        atClass = AddressType.to_class_by_address_type(self.addressType)
        assert isinstance(atClass, AddressType)

        latest_perek_addr = None

        for yc in yerushalmi_chapters:
            try:
                addr_ranges = self.getAddressRangesForPerek(yc, latest_perek_addr)
            except IndexError:
                print(f"{yc.normal()} has no marks.")
                continue
            if len(addr_ranges) < 2:
                print(f"{yc.normal()} has only {len(addr_ranges)} marks.")
            latest_marker_addr = None
            for i, a in enumerate(addr_ranges):
                if latest_marker_addr is not None:
                    first_num = atClass.toNumber("en", latest_marker_addr)
                    second_num = atClass.toNumber("en", a["addr"])
                    first_locale = addr_ranges[i-1]['start'].normal()
                    second_locale = a['start'].normal()

                    if first_num >= second_num:
                        print(
f"""
Page marks out of order:
- {latest_marker_addr} is at {first_locale}
- {a["addr"]} is at {second_locale}""")

                    elif first_num + 1 !=  second_num:
                        print(
f"""
Missing page marks: 
- Between {latest_marker_addr} and {a['addr']}.
- Between {first_locale} and {second_locale}""")

                latest_marker_addr = a["addr"]
            latest_perek_addr = addr_ranges[-1]["addr"]


    def getAddressRangesForPerek(self, perek, starting_addr=None):
        """

        :param perek:
        :param starting_addr:
        :return:   List of {"addr": a, "start": s, "end": e}
        """
        reg = re.compile(rf'<i data-overlay="{self.overlayName}" data-value="([0-9a-z]+)">')
        marker_addrs = []
        marker_orefs = []
        for halacha in perek.all_subrefs():
            for segment in halacha.all_subrefs():
                for pg_match in reg.finditer(TextChunk(segment, "he", self.versionTitle).text):
                    marker_addrs += [pg_match.group(1)]
                    marker_orefs += [segment]

        detailed_perek_oref = perek.as_ranged_segment_ref()
        perek_start_oref = detailed_perek_oref.starting_ref()
        perek_end_oref = detailed_perek_oref.ending_ref()

        if perek_start_oref == marker_orefs[0] or starting_addr == None:
            marker_addrs = marker_addrs
            range_starts = marker_orefs
            range_ends = marker_orefs[1:] + [perek_end_oref]
        else:
            marker_addrs = [starting_addr] + marker_addrs
            range_starts = [perek_start_oref] + marker_orefs
            range_ends = marker_orefs + [perek_end_oref]

        return [{"addr": a, "start": s, "end": e} for a,s,e in zip(marker_addrs, range_starts, range_ends)]


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
        parts = [p for p in parts if p["content"]]  # Remove nulls in between/before/after tags
        running_length = 0
        for p in parts:
            if p["type"] == "text":
                p["start"] = running_length

                white_start = re.search(r"^\s+", p["content"])
                white_end = re.search(r"\s+$", p["content"]) if not re.match(r"^\s+$", p["content"]) else None
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


    def insert_tag_after_word(self, insert_position, tag, attrs):
        """

        :param insert_position: After which word number to insert tag.  0 means at the beginning.  1 means after first word.
                There's no facility to insert at end, currently.
        :param tag:
        :param attrs:
        :return:
        """
        attr_string = " ".join([f'{a}="{b}"' for a, b in attrs.items()])
        open_tag = {
            "content": f"<{tag} {attr_string}>",
            "type": "tag"
        }
        close_tag = {
            "content": f"</{tag}>",
            "type": "tag"
        }

        # Find the right part
        part_indx = [i for i, p in enumerate(self._parts) if p["type"] == "text" and p["start"] <= insert_position < p["end"]][0]
        initial_part = self._parts[part_indx]

        split_pos = insert_position - initial_part["start"]

        # cut the part into two
        if split_pos > 0:
            first_content_word_array = initial_part["word_array"][:split_pos]
            first_part = {
                "type": "text",
                "word_array": first_content_word_array,
                "content": " ".join(first_content_word_array),
                "start": initial_part["start"],
                "word_count": split_pos,
                "end": insert_position,
                "white_start": initial_part["white_start"],
                "white_end": " "
            }

        second_content_word_array = initial_part["word_array"][split_pos:]
        second_part = {
            "type": "text",
            "word_array": second_content_word_array,
            "content": " ".join(second_content_word_array),
            "start": insert_position,
            "word_count": len(second_content_word_array),
            "end": initial_part["end"],
            "white_start": "",
            "white_end": initial_part["white_end"]
        }

        # insert tags in between

        newparts = [] if part_indx == 0 else self._parts[:part_indx]
        if split_pos > 0:
            newparts += [first_part]
        newparts += [open_tag, close_tag, second_part] + self._parts[part_indx+1:]
        self._parts = newparts
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
        self._raw_store = self._store[:]
        self._store = [TextChunk._strip_itags(_) for _ in self._store]
        self._lengths = [word_count(seg) for seg in self._store]
        self.accumulated_lengths = functools.reduce(lambda a, u: a + [u + a[-1]], self._lengths, [0])[1:]    # Add lengths up to get accumulated length.  Slice at end removes initial 0.
        self._markers = [None] * (len(self._store))  # markers for before each segment

    def add_marker_before(self, before, marker):
        """

        :param before: before which segment to put the marker, base 0
        :param marker: What to place in the marker
        :return:
        """
        self._markers[before] = marker

    def get_marker_word_positions(self):
        """
        :return: dict {word position: marker}
        """
        starts = [0] + self.accumulated_lengths[:-1]
        return {starts[i]: m for i, m in enumerate(self._markers) if m}

    def get_sections_and_ranges(self):
        next_start = 0
        for i, section in enumerate(self._raw_store):
            yield section, next_start, self.accumulated_lengths[i]
            next_start = self.accumulated_lengths[i]


def load_guggenheimer_data(g_version="Guggenheimer"):
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
    tur_map = {
        "א": "a",
        "ב": "b",
        "ג": "c",
        "ד": "d"
    }
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
                    "tur": d[3],
                    "tur_num": decode_hebrew_numeral(d[3]),
                    "daf_num": str(decode_hebrew_numeral(d[2])) + tur_map[d[3]],
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
