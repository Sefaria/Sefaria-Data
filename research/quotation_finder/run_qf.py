import django, re, requests, json
django.setup()
from research.quotation_finder.dicta_api import *
from research.quotation_finder.citation_inserts import *
import pstats
from pstats import SortKey
from sefaria.model import *
from sefaria.system.database import db
import cProfile
from tqdm import tqdm


def links_ys_torah():
    title = "Yalkut Shimoni on Torah"
    ys_peared = get_zip_ys()
    peared = []
    [peared.extend(e) for e in ys_peared]  # beacuse ys_peared returned a list of lists (per chumash)
    priority = dict([(r.normal(),item[0]) for item in peared if item[1] for r in item[1].all_segment_refs()])
    run_offline(title, 'Midrash', min_thresh=25, post=False, mongopost=True, priority_tanakh_chunk_type=priority, max_word_number=None)


def links_ys_Nach(title):
    title = title
    peared = get_zip_alt_struct(title, 'Book')
    priority = dict([(r.normal(), item[0]) for item in peared if item[1] for r in item[1].all_segment_refs()])
    run_offline(title, 'Midrash', min_thresh=25, post=False, mongopost=True, priority_tanakh_chunk_type=priority,
                max_word_number=None)


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
    to_post = [l.contents() for l in ls]
    n = len(to_post)
    i = 0
    for e in range(0, divmod(n, 300)[0]):
        print(i)
        post_link(to_post[i: min(i+300, n)], server=server)
        i +=300

def post_links_from_quotations_collection(title=None, q=None, mode = "tanakh", run_type=f"siddur pool run {mode}"):
    if not q:
        if not title:
            print("must put in title or query")
        q = {"refs": {"$regex": f"{title}.*"}}
    ls = db_qf.siddur_quotations.find(q)
    links = []
    for l in ls:
        del l['_id']
        link_json = l
        # link_json = {"type": type,
        #  "refs": [pasuk_ref.normal(), book_match.normal()],
        #  "auto": auto,
        #  "charLevelData": [],
        # "score": l["score"],
        #  "inline_citation": True,
        #  "qf_run_type": run_type  # don't remember what it was made for.
        #  }
        links.append(link_json)
    post_link(links)

def mishna_refinement():
    q = {"$and": [{"type": {"$regex": "^quotation_auto"}}, {"refs": {"$regex": "^Pirkei"}}]}#, "charLevelData.0.startWord": { "$ne" : 0 } }
    # c_mishna = db_qf.siddur_quotations.find(q)
    # q = {"$and": [{"refs":"Siddur Sefard, Weekday Shacharit, Amidah 13"}, {"type": {"$regex": "^quotation_auto"}}]}
    c_mishna = db.links.find(q)
    ls_mishna = list(c_mishna)
    print(len(ls_mishna))
    cnt=0
    for l in ls_mishna:
        good = False
        if l["type"] == "quotation_auto_mishna_good":
            continue
        # if Ref(l["refs"][0]).book in library.get_indexes_in_category("Mishnah") or Ref(l["refs"][1]).book in library.get_indexes_in_category("Mishnah"):
        try:
            if wl.calculate((Ref(l["refs"][1]).text('he').text), (Ref(l["refs"][0]).text('he').text), normalize=True)>80:
                print(f"new {cnt+1}\n localhost:8000/{re.sub(' ','_',l['refs'][1])}?lang=he&{re.sub(' ','_',l['refs'][0])}\n")
                Link().update({"refs": l["refs"]}, {"type": "quotation_auto_mishna_good"})
                cnt += 1
                good=True
        except TypeError:
            pass
        print(f"back to normal refs: {l['refs']}")
        start_m = l["charLevelData"][0]["startWord"]
        end_m = l["charLevelData"][0]["endWord"]
        all_words =  Ref(l["refs"][0]).word_count('he') # len(strip_nikkud(Ref(l["refs"][1]).text('he').text)) #
        m_percentage = (end_m-start_m)/all_words
        print(f"m_percentage: {m_percentage}")
        if not good and m_percentage > 0.5:
            print("m_good")
            print(f"m_percentage: {m_percentage}")
            print(f"localhost:8000/{re.sub(' ','_',l['refs'][1])}?lang=he&{re.sub(' ','_',l['refs'][0])}\n")
            Link().update({"refs":l["refs"]}, {"type": "quotation_auto_mishna_good"})
            good=True
            cnt+=1
        start_s = l["charLevelData"][1]["startChar"]
        end_s = l["charLevelData"][1]["endChar"]
        all_chars = len(Ref(l["refs"][1]).text('he').text)
        s_percentage = (end_s - start_s) / all_chars
        print(start_s, end_s, all_chars)
        print(f"segment_percentage: {s_percentage}")
        if not good and s_percentage > 0.7:
            print("s_good")
            print(f"segment_percentage: {s_percentage}")
            print(f"localhost:8000/{l['refs'][1]}?lang=he&{l['refs'][0]}\n")
            Link().update({"refs": l["refs"]}, {"type": "quotation_auto_mishna_good"})
            cnt+=1
            good=True
        if not good:
            Link().update({"refs": l["refs"]}, {"type": "quotation_auto_mishna"})

    print(cnt)


def siddur_tanakh_cleanup():
    q = { "$and" : [{ 'refs' :{"$regex":"^Siddur.*" }}, { 'generated_by' : None } ] }
    ls = LinkSet(q)
    cnt=0
    print(len(list(ls)))
    tanakh_links = []
    order_ref = lambda l: l.refs if re.match(l.refs[1], "^Siddur") else l.refs.reverse
    for l in ls:
        order_ref(l)
        if Ref(l.refs[0]).book in library.get_indexes_in_category("Tanakh"):
            tanakh_links.append(l)
            print(l.refs)
            cnt+=1
    print(cnt)

if __name__ == '__main__':
    # def singal_arg(arg):
    #     args = re.split("\|", arg)
    #     citation_inserts_and_post_links(*args)
    # cProfile.run('singal_arg("Alshich on Torah|Torat Moshe, Warsaw, 1875|Alshich on Torah, Deuteronomy|tanakh_comm")')
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

    run_offline("Noam Elimelech", 'Chasidut', min_thresh=0, post=True, mongopost=True, priority_tanakh_chunk_type='parasha',
                max_word_number=None, offline=True)

    # post_quotation_links('^Siddur', server=SEFARIA_SERVER)
    # post_links_from_quotations_collection(q={"qf_run_type": "siddur pool run tanakh", "refs":{"$regex":"^Siddur Ashkenaz.*"}})
    # post_links_from_quotations_collection(q={"qf_run_type": "siddur pool run", "refs":{"$regex":"^Siddur Ashkenaz.*"}})

    # lsa = LinkSet({"type": "quotation_auto_tanakh", "generated_by": "quotation_finder_ranged_preciselink_override"})
    # print(len(lsa))
    # # lsa = list(lsa)
    # # lsa.reverse()
    # i=0
    # cnt = 0
    # while i< len(lsa):
    #     print(i)
    #     increment = 300
    #     ls = lsa[i:i+increment]
    #     links=[]
    #     for l in tqdm(ls):
    #         l=l.contents()
    #         l["inline_citation"] = False
    #         l["type"] = "quotation_auto_tanakh"
    #         if Ref(l["refs"][0]).is_range() or Ref(l["refs"][1]).is_range():
    #             links.append(l)
    #             cnt+=1
    #     post_link(links,  override_preciselink=True)
    #     i += increment
    #     print(cnt)
    #     sleep(20)
    # print("done")
    # mishna_refinement()