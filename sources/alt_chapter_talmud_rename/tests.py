import django
import pytest

django.setup()

from sefaria.model import *
from alt_toc_repopulate import retrieve_new_chapter_names, retrieve_babylonian_talmud_masechtot

@pytest.fixture
def new_names_data():
    return retrieve_new_chapter_names()

@pytest.fixture
def masechtot():
    return retrieve_babylonian_talmud_masechtot()
def title_changed(new_names_data, masechet):
    masechet_index = Ref(masechet).index

    chap_num = 0
    for node in masechet_index.alt_structs['Chapters']['nodes']:
        chap_num += 1
        new_title = new_names_data[f"{masechet} {chap_num}"]
        chapter_title_list = node["titles"]
        for title in chapter_title_list:
            if title['lang'] == 'en':
                assert title['text'] == new_title


def test_all_titles_changed(new_names_data, masechtot):
    for masechet in masechtot:
        title_changed(new_names_data, masechet)

def test_bava_kamma_hebrew():
    bk_index = Ref("Bava Kamma 2").index
    assert bk_index.alt_structs["Chapters"]["nodes"][1]["titles"][1]["text"] == "כיצד הרגל"