import django, re, requests, json
django.setup()
from research.quotation_finder.dicta_api import *
from sefaria.settings import *
from sefaria.system.database import *
from sefaria.model import *
from sefaria.system.exceptions import *
import unicodecsv as csv

def make_csv(list_dict):

    with open('current_ref_stats.csv', 'a') as csv_file:
        writer = csv.DictWriter(csv_file, ['title', 'refs', 'tanakh_refs', 'inline_refs', 'word_count'])
        writer.writeheader()
        writer.writerows(list_dict)

def by_seg_count(title):
    base_file = f'{title}.json'
    base_file_dict = get_from_file(base_file)
    base_file_dict.keys()
    sum_text_words = 0
    for r in base_file_dict.keys():
        text_words = TextChunk(Ref(r), 'he').word_count()
        sum_text_words += text_words
    return sum_text_words


def get_cat_stats(cat = "tanakh_comm"):
    tanakh_books_reg = "^(Amos|Daniel|Deuteronomy|Ecclesiastes|Esther|Exodus|Ezekiel|Ezra|Genesis|Habakkuk|Haggai|Hosea|I Chronicles|I Kings|I Samuel|II Chronicles|II Kings|II Samuel|Isaiah|Jeremiah|Job|Joel|Jonah|Joshua|Judges|Lamentations|Leviticus|Malachi|Micah|Nahum|Nehemiah|Numbers|Obadiah|Proverbs|Psalms|Ruth|Song of Songs|Zechariah|Zephaniah) .*"
    d = dict()
    os.chdir(f'offline/text_mappings/{cat}')
    title_list = os.listdir(os.getcwd())
    titles = [re.split('.json', t)[0] for t in title_list]
    for title in titles:
        refs_query = {"refs": {"$regex": f"{title}.*"}}
        inline_refs_query = {"refs": {"$regex": f"{title}.*"}, "inline_citation": True}
        tanakh_refs_query = {"$and":[{"refs": {"$regex": f"{title}.*"}}, {"refs": {"$regex": tanakh_books_reg}}]}
        number_refs = db.links.count_documents(refs_query)
        number_inline_links = db.links.count_documents(inline_refs_query)
        number_tanakh_refs = db.links.count_documents(tanakh_refs_query)
        try:
            sum_text_words = TextChunk(Ref(title), 'he').word_count()
        except InputError:
            sum_text_words = by_seg_count(title)
        stat_inline = number_inline_links*100/sum_text_words
        stat_tanakh = number_tanakh_refs*100/sum_text_words
        d.update({'title': title,
                  'refs': number_refs,
                 'tanakh_refs': number_tanakh_refs,
                'inline_refs': number_inline_links,
                'word_count': sum_text_words
                })
        print(f"title: {title}, refs: {number_refs}, inline_refs: {number_inline_links}, tanakh_refs: {number_tanakh_refs}, text_words:{sum_text_words}")
    print(d)
    make_csv(d)
    return d

if __name__ == '__main__':
    get_cat_stats("Chasidut")