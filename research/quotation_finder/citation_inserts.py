import django, re, requests, json
django.setup()
from research.quotation_finder.dicta_api import *
import pymongo
from sefaria.settings import *

client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)  # (MONGO_ASPAKLARIA_URL)
db_qf = client.quotations

# read book segment links from DB (or while posting?)
# read book segment textChunk from DB
# find place in seg (CharLevelData)
# paste in the pasukRef in normal hebrew.

dummy_char = "█"


def get_links_for_citation_insert(ref, score, link_source):
    if isinstance(link_source, dict):  # link_source == dict
        # lls = [Link(l) for l in link_source if ref.normal() in l['refs'] and l['score'] >= score]
        lls = [Link(l) for l in link_source.get(ref.normal(), [{'score': -1}]) if l['score'] >= score]
        return lls if len(lls) > 0 else None
    elif link_source == 'quotation_DB':
        query = {"refs": ref.normal(), "score": {"$gte": score}}
        cursor = db_qf.quotations.find(query)
        cursor_len = db_qf.quotations.count_documents(query)
        links = [Link(l) for l in list(cursor)]
        links = dict([(link.charLevelData[1]['startChar'], link) for link in links]).values() # this line is to eliminate duplicates.
        return links if cursor_len > 0 else None
    else:  # link_source == 'Sefaria_DB'
        return list(LinkSet({"refs": ref.normal(), "type": "quotation_auto", "score": {"$gte": score}}))


def get_tc(tref, from_file=None):
    seg_text = ''
    if from_file:
       seg_text = from_file[tref]
    else:
        tc = Ref(tref).text('he')
        if tc.version():
            tc.vtitle = tc.version().versionTitle  # this makes some sense because it is always on a single segment
            seg_text = tc.text
        else:
            print(f"missing text in seg {tref}")
    return seg_text


def get_segment(ref, score=22, link_source=None):
    seg_text = get_tc(ref.normal())
    seg_text_list = list(re.sub('\s+', dummy_char, seg_text))
    lls = get_links_for_citation_insert(ref, score, link_source)
    if lls:
        text_w_citations = add_citations(lls, seg_text_list, ref.normal())
        # print(f"check {link2url(lls[0], sandbox='quotations')}")
    else:
        return {}
    return {ref.normal(): text_w_citations}

def ciation_inline_placing(link, base_ref):

    return place

def get_place_citation(link, color_score=None):
    # the following 2 assumptions about the placing in the refs list and the charLevelData list are based on the link testing\and changing if needed in add_citations link. we can make here another assertion but that seems redundant
    pasuk_ref = Ref(link.refs[0])
    place = link.charLevelData[1]['endChar']
    citation = f"{dummy_char}({pasuk_ref.normal('he')})"  # {dummy_char}"
    if color_score:
        if color_score[0] < link.score < color_score[1]:
            color = 1  # orange
        elif color_score[1] <= link.score < color_score[2]:
            color = 2  # green
        elif color_score[2] <= link.score:
            color = 3  # blue
        else:
            return []
        citation = f'<span class="ref-link-color-{color}">{citation}</span>'
        # citation = f'<sup><span class="ref-link-color-{color}">*</span></sup><i class="footnote">{citation}</i>'
    return [(place, citation)]


def to_be_embedded(ls, lls, seg_text_list, book_ref):
    """
    This function trims the links to imbed inline based on the inline links that are already present. shams. and trivial inline citation heuristics.
    :param ls: linkSet on this segment prior to quotations
    :param lls: linkSet of quotation finder (the set to be trimmed)
    :param seg_text_list: segment text
    :param book_ref: tref of the segment
    :return: left_links, text_to_delete: left_links: are the quotation links to be embedded. text_to_delete. (for shams and other text deletion in future)
    """

    toRef = lambda l: l.refs[0] if l.refs[1] == book_ref else l.refs[1]
    links_from_text_type = [toRef(l) for l in ls if l.type == 'add_links_from_text']
    tc = Ref(book_ref).text('he').text
    wrapped_text = library.get_wrapped_refs_string(tc)
    wrapped = re.findall('(<a.*?data-ref="(.*?)".*?a>)', wrapped_text)
    wrapped_trefs = [wrap[1] for wrap in wrapped]
    refs_in_db = [l for l in ls if l.type != "quotation_auto"]
    trivial = [toRef(l) for l in refs_in_db if l.type == 'commentary'] + [toRef(l) for l in lls if hasattr(l, "trivial")]
    quotation_refs = [toRef(l) for l in lls]
    def_not_needed = set(wrapped_trefs).intersection(set(quotation_refs))
    left_links = [l for l in lls if toRef(l) not in def_not_needed and toRef(l) not in trivial]
    text_to_delete = []
    for l in left_links:
        startPlace = l.charLevelData[1]['startChar']
        before = ')' in seg_text_list[startPlace-5:startPlace]
        if before:
            inline_options = re.findall("[(\[](.*)[)\]]", tc[startPlace-20:startPlace])
            for par in inline_options:
                if "שם" in par:
                    text_to_delete.append(par)
                    left_links.remove(l)
                    continue
                else:
                    print(f"{par} : {l.refs}")
                    db_qf.humaneye.insert_one({"refs": l.refs, "parenthesis": par})
        endPlace = l.charLevelData[1]['endChar']
        after = '(' in seg_text_list[endPlace:endPlace+5]
        if after:
            inline_options = re.findall("[(\[](.*)[)\]]", tc[startPlace+20:startPlace])
            for par in inline_options:
                if "שם" in par:
                    text_to_delete.append(par)
                    left_links.remove(l)
                else:
                    print(f"{par} : {l.refs}")
                    db_qf.humaneye.insert_one({"refs": l.refs, "parenthesis": par})
    return left_links, text_to_delete


def add_citations(lls, seg_text_list, book_ref):
    """

    :param lls: list of the links to be added in inline citations. (according to links that were created by quotation_finder)
    :param seg_text_list:
    :param book_ref:
    :return:
    """
    citation_list =[]
    cnt = 0
    ls = LinkSet(Ref(book_ref))
    trimmed_lls, _ = to_be_embedded(ls, lls, seg_text_list, book_ref)
    for l in trimmed_lls:
        # if l.charLevelData[1]['startChar'] <= 10 or (hasattr(l, 'dh') and l.dh):  # check for DH
        if l.type == 'dibur_hamatchil':
            continue
        if Ref(l.refs[1]).book != Ref(book_ref).book:
            print("needed reverse")
            l.refs.reverse()
            l.charLevelData.reverse()
        # todo: before placing the citation in, check what the text looks like, are there other citations or shamas inline already? is this a dh? or is there a diffrenet reason we don't want to add this l link?
          # or do we want to add it but in a different place?
        seg_citation_list = get_place_citation(l, color_score=[22, 30, 50])
        citation_list.extend(seg_citation_list)
    citation_list.sort()
    for p, c in citation_list:
        place = p+cnt
        seg_text_list.insert(place, c)
        cnt += 1
    text = ''.join(seg_text_list)
    text = re.sub(f'{dummy_char}+', ' ', text)
    # text = re.sub('(\(.*?\))(\s+)(\.|,)', '\g<1>\g<3>', text)
    # print(text)
    return text


def push_text_w_citations(version, new_texts_dict):
    # modify_bulk_text(UID, version, new_texts_dict)
    # tc.text = new_text
    # tc.save()
    for r, t in new_texts_dict.items():
        create_payload_and_post_text(r, t, 'he', version.versionTitle, version.versionSource)


def get_local_seg(ref):
    return {ref.normal(): ref.text('he').text}


def order_links_by_segments(links): #, base_book_title):
    from collections import defaultdict
    link_dict = defaultdict(list)
    pasuk_books = library.get_indexes_in_category('Tanakh')
    for l in links:
        if Ref(l['refs'][1]).book in pasuk_books:
            key_ref = l['refs'][0]
        else:
            # assert base_book_title in l['refs'][1]
            key_ref = l['refs'][1]
        link_dict[key_ref].append(l)
    return link_dict

if __name__ == '__main__':
    new_texts_dict = dict()
    range_ref = Ref('Yalkut_Shimoni_on_Torah.62.20-82.10')
    # links = get_links_from_file('Ramban_on_Numbers.31.23.json')
    # link_dict = order_links_by_segments(links)  #,"Selichot_Nusach_Ashkenaz_Lita")
    for r in range_ref.all_segment_refs():
        new_texts_dict.update(get_segment(r, score=25, link_source='quotation_DB'))
        # new_texts_dict.update(get_local_seg(r))
    push_text_w_citations(range_ref.text('he').version(), new_texts_dict)