from typing import List
import django, argparse, json, zipfile, re
django.setup()
from functools import reduce, partial
from tqdm import tqdm
from dataclasses import dataclass
from sefaria.model import *
from sources.local_settings import DICTA_LIBRARY_PATH
from sources.functions import post_index, post_text

"""
TODO
category, en title, section names, version title, version source
"""


class DictaLibraryManager:

    def __init__(self, lib_path):
        self.lib_path = lib_path
        self.books_by_name = {}
        with open(f"{self.lib_path}/books.json", "r") as fin:
            self.books_list = [DictaBook(lib_path=DICTA_LIBRARY_PATH, **book_dict) for book_dict in json.load(fin)]
        for book in self.books_list:
            self.books_by_name[book.displayName] = book

    def get_book(self, name):
        return self.books_by_name[name]

    def parse_and_post_book(self, book_name: 'DictaBook', server, post=False):
        book = self.get_book(book_name)
        parallels = book.parse()
        if post:
            book.post(server)


@dataclass
class DictaParallel:
    section_index: int
    start_segment_index: int
    end_segment_index: int
    url: str
    baseTextLength: int
    baseStartChar: int
    baseStartToken: int
    baseEndToken: int
    baseMatchedText: str
    compBookXmlId: str
    compName: str
    compNameHe: str
    sortOrder: int
    compTextLength: int
    compStartChar: int
    compMatchedText: str
    identified: int = None  # no idea what this is


@dataclass
class DictaPage:
    displayName: str
    fileName: str
    nakdanResponseFile: str

    def parse(self, root_dir):
        jin = self.__get_json_content(root_dir)
        text = self.__get_text(jin)
        paragraphs = list(filter(lambda x: len(x) > 0, text.split('\n')))
        index = self.__get_zero_based_index()
        parallels = self.__get_parallels(jin, index, paragraphs)
        return paragraphs, index, parallels

    def __get_zero_based_index(self):
        m = re.search(r'\d+$', self.displayName)
        return int(m.group(0)) - 1

    def __get_json_content(self, root_dir):
        json_fname = self.fileName.replace('.zip', '.json')
        with zipfile.ZipFile(f"{root_dir}/{self.fileName}") as zin:
            with zin.open(json_fname, mode='r') as fin:
                return json.load(fin)

    @staticmethod
    def __get_text(jin):
        return reduce(lambda a, b: a + b['str'], jin['tokens'], "")

    @staticmethod
    def __get_parallels(jin: dict, page_index: int, paragraphs: List[str]):
        parallels = jin['data']['parallelsResults']['results'][0]['data']
        return map(partial(DictaPage.__create_parallel_object, page_index, paragraphs), parallels)

    @staticmethod
    def __create_parallel_object(page_index: int, paragraphs: List[str], parallel_dict: dict):
        from bisect import bisect_right
        import pylcs
        base_text_match = parallel_dict['baseMatchedText']
        parag_end_indexes = reduce(
            lambda a, b: a + [len(b) + ((a[-1] + 1) if len(a) > 0 else 0)],
            paragraphs, []
        )
        page_text = " ".join(paragraphs)
        try:
            base_index = page_text.index(base_text_match)
        except ValueError:
            res = pylcs.lcs_string_idx(base_text_match, page_text)
            base_text_match = ''.join([page_text[i] for i in res if i != -1])
            base_index = page_text.index(base_text_match)

        start_seg_index = bisect_right(parag_end_indexes, base_index)
        end_seg_index = bisect_right(parag_end_indexes, base_index + len(base_text_match) - 1)

        # testing
        segs_with_base_text = " ".join(paragraphs[start_seg_index: end_seg_index + 1])
        assert base_text_match in segs_with_base_text
        if start_seg_index < end_seg_index:
            segs_wo_base_text = " ".join(paragraphs[start_seg_index+1: end_seg_index+1])
            assert base_text_match not in segs_wo_base_text
            segs_wo_base_text = " ".join(paragraphs[start_seg_index:end_seg_index])
            assert base_text_match not in segs_wo_base_text
        return DictaParallel(
            section_index=page_index,
            start_segment_index=start_seg_index,
            end_segment_index=end_seg_index,
            **parallel_dict
        )

@dataclass
class DictaBook:
    lib_path: str
    displayName: str
    fileName: str
    printYear: int
    printLocation: str
    author: str
    category: str
    categoryEnglish: str = None
    authorEnglish: str = None
    printLocationEnglish: str = None
    displayNameEnglish: str = None
    source: str = None
    firstpage: dict = None  # seems to be a non-standard field
    pages: List[DictaPage] = None

    def __post_init__(self):
        self._root_path = f"{self.lib_path}/{self.fileName}"
        self._parsed_pages = []
        self.__load_pages()

    def __load_pages(self):
        try:
            with open(f"{self._root_path}/pages.json", "r") as fin:
                self.pages = [DictaPage(**page_dict) for page_dict in json.load(fin)]
        except FileNotFoundError:
            print(f"No directory for {self.displayName}")

    def parse(self):
        self.__create_index()
        parallels = self.__create_version()
        return parallels

    def post(self, server):
        post_index(self.index, server=server)
        post_text(self.index['title'], self.version, server=server, skip_links=True)

    def __create_index(self):
        # TODO using fileName as stand-in for English title for now
        en_title = self.fileName.capitalize()
        categories = ["Responsa"]
        root = JaggedArrayNode()
        root.add_primary_titles(en_title, self.displayName)
        root.add_structure(["Daf", "Paragraph"], address_types=['Integer', 'Integer'])
        root.key = en_title
        root.validate()
        self.index = {
            "title": en_title,
            "categories": categories,
            "schema": root.serialize()
        }

    def __create_version(self):
        version_notes = """This text was digitized and released into the public domain by <a href="https://dicta.org.il">Dicta: The Israel Center for Text Analysis</a>, using a state-of-the-art OCR pipeline leveraging a custom-built transformer-based language model for Rabbinic Hebrew. Nikud (Vocalization) marks were auto-generated by <a href="https://nakdanlive.dicta.org.il">Dicta's Nakdan system</a>."""
        parsed_pages = []
        all_parallels = []
        for page in tqdm(self.pages, desc=self.fileName):
            paragraphs, index, parallels = page.parse(self._root_path)
            all_parallels += parallels
            while len(parsed_pages) < index:
                parsed_pages += [[]]
            parsed_pages += [paragraphs]
        self.version = {
            "text": parsed_pages,
            "versionTitle": "Dicta Library",
            "versionSource": "https://library.dicta.org.il",
            "language": "he",
            "versionNotes": version_notes
        }
        return all_parallels


def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("book", help='name of book to parse')
    parser.add_argument("-s", "--server", dest="server", help="server to post to")
    return parser


if __name__ == '__main__':
    parser = init_argparse()
    args = parser.parse_args()
    dicta = DictaLibraryManager(DICTA_LIBRARY_PATH)
    dicta.parse_and_post_book(args.book, args.server, post=True)

# https://ste.cauldron.sefaria.org