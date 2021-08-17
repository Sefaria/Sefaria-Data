import django, re, requests, json
django.setup()
from research.quotation_finder.dicta_api import *
from research.quotation_finder.citation_inserts import *
import pstats
from pstats import SortKey
from sefaria.model import *
import cProfile


def links_ys_torah():
    title = "Yalkut Shimoni on Torah"
    ys_peared = get_zip_ys()
    peared = []
    [peared.extend(e) for e in ys_peared] # beacuse ys_peared returned a list of lists (per chumash)
    priority = dict([(r.normal(),item[0]) for item in peared if item[1] for r in item[1].all_segment_refs()])
    run_offline(title, 'Midrash', min_thresh=25, post=False, mongopost=True, priority_tanakh_chunk_type=priority, max_word_number=None)
    log.close()


def links_ys_Nach(title):
    title = title
    peared = get_zip_alt_struct(title, 'Book')
    priority = dict([(r.normal(), item[0]) for item in peared if item[1] for r in item[1].all_segment_refs()])
    run_offline(title, 'Midrash', min_thresh=25, post=False, mongopost=True, priority_tanakh_chunk_type=priority,
                max_word_number=None)
    log.close()


def citation_inserts_and_post_links(title, vtitle, ref_title, cat, min_score=25, prefix_char_range=30):
    new_texts_dict = dict()
    all_links = []
    range_ref = Ref(ref_title)
    path = os.getcwd()
    base_file = f'{path}/offline/text_mappings/{cat}/{title}.json'
    base_file_dict = get_from_file(base_file)
    v = Version().load({'title': title, 'versionTitle': vtitle})
    cnt = 0
    if isinstance(ref_title, list):
        [citation_inserts_and_post_links(title=title, vtitle=vtitle, ref_title=sub_ref, cat=cat, min_score=min_score, prefix_char_range=prefix_char_range) for sub_ref in ref_title]
    else:
        for r in range_ref.all_segment_refs():  # base_file_dict.keys():
            # r = Ref(ref)
            text_dict, links = get_segment(r, score=min_score, link_source='quotation_DB', prefix_char_range=prefix_char_range,
                                           from_file=base_file_dict)
            new_texts_dict.update(text_dict)
            all_links.extend([l.to_post() for l in links])
            only_sidebar_links = get_links_to_post_not_to_embed(r, score=min_score, from_file=base_file_dict)
            all_links.extend(only_sidebar_links)
            cnt += 1
            print(f"seg {cnt}")
            # new_texts_dict.update(get_local_seg(r))
        try:
            post_link(all_links, server="http://localhost:8000")
        except ConnectionError:
            pass
        modify_text_localy(range_ref.index.title, v, new_texts_dict, server="http://localhost:8000")

    # push_text_w_citations(v.versionTitle, v.versionSource, new_texts_dict)
    # post_text()


def post_quotation_links(title, server=SEFARIA_SERVER, q=None):
    if not q:
        q = {"refs": {"$regex": f"{title}.*"},
         "$or": [{"type": "quotation_auto"}, {"type": "dibur_hamatchil"}]}
    ls = LinkSet(q)
    print(f"num of quotation_auto and dibur_hamatchil links {ls.count()}")
    post_link([l.contents() for l in ls], server=server)


if __name__ == '__main__':
    def singal_arg(arg):
        args = re.split("\|", arg)
        citation_inserts_and_post_links(*args)
    cProfile.run('singal_arg("Alshich on Torah|Torat Moshe, Warsaw, 1875|Alshich on Torah, Deuteronomy|tanakh_comm")')
 # #    arg = "Yalkut Shimoni on Torah|Yalkut Shimoni on Torah|Yalkut Shimoni on Torah|Midrash"
 # #    # singal_arg("Yalkut Shimoni on Nach|Yalkut Shimoni on Nach|Yalkut Shimoni on Nach|Midrash")
 # #    nodes = ['First Day',
 # # 'Second Day',
 # # 'Third Day',
 # # 'Fourth Day',
 # # 'Fifth Day',
 # # 'Sixth Day',
 # # 'Seventh Day',
 # # 'Erev Rosh Hashana',
 # # 'Fast of Gedaliah',
 # # 'Second Day of the Ten Days of Penitence',
 # # 'Third Day of the Ten Days of Penitence',
 # # 'Fourth Day of the Ten Days of Penitence',
 # # 'Fifth Day of the Ten Days of Penitence',
 # # 'Yom Kippur Eve']
 # #    for n in nodes:
 # #        citation_inserts_and_post_links('Selichot Nusach Ashkenaz Lita','Selichot Nusach Lita -- Wikisource', f'Selichot Nusach Ashkenaz Lita, {n}', 'Liturgy')
 #
 #    # cProfile.run('singal_arg("Yalkut Shimoni on Torah|Yalkut Shimoni on Torah|Yalkut Shimoni on Torah 1-162|Midrash")','restats')
 #    # p = pstats.Stats('restats')
 #    # p.sort_stats(SortKey.CUMULATIVE).print_stats(20)
 #    # links_ys_Nach("Yalkut Shimoni on Nach")
 #    singal_arg("Yalkut Shimoni on Torah|Yalkut Shimoni on Torah|Yalkut Shimoni on Torah|Midrash")

    # run_offline("Alshich on Torah", 'tanakh_comm', min_thresh=25, post=False, mongopost=True, priority_tanakh_chunk_type='perek',
    #             max_word_number=None)

