import django, re, requests, json
django.setup()
from research.quotation_finder.dicta_api import *
# read book segment links from DB (or while posting?)
# read book segment textChunk from DB
# find place in seg (CharLevelData)
# paste in the pasukRef in normal hebrew.
dummy_char = "█"


def get_links_for_citation_insert(ref, score, link_source):
    if link_source:  # link_source = file_name:
        # lls = [Link(l) for l in link_source if ref.normal() in l['refs'] and l['score'] >= score]
        lls = [Link(l) for l in link_source.get(ref.normal(), [{'score': -1}]) if l['score'] >= score]
        return lls
    else: #link_source == 'DB'
        return list(LinkSet({"refs": ref.normal(), "type": "quotation_auto", "score": {"$gte": score}}))


def get_tc(tref, from_file=None):
    if from_file:
       seg_text = from_file[tref]
    else:
        tc = Ref(tref).text('he')
        tc.vtitle = tc.version().versionTitle  # this makes some sense because it is always on a single segment
        seg_text = tc.text
    return seg_text


def get_segment(ref, score=22, link_source=None):
    seg_text = get_tc(ref.normal())
    seg_text_list = list(re.sub('\s+', dummy_char, seg_text))
    lls = get_links_for_citation_insert(ref, score, link_source)
    if len(lls) > 0:
        text_w_citations = add_citations(lls, seg_text_list, ref.normal())
        print(f"check {link2url(lls[0], sandbox='quotations')}")
    else:
        return {}
    return {ref.normal(): text_w_citations}


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


def add_citations(lls, seg_text_list, book_ref):
    citation_list =[]
    cnt = 0

    for l in lls:
        if l.charLevelData[1]['startChar'] <= 10 or (hasattr(l, 'dh') and l.dh):  # check for DH
            continue
        if Ref(l.refs[1]).book != Ref(book_ref).book:
            print("needed reverse")
            l.refs.reverse()
            l.charLevelData.reverse()
        citation_list.extend(get_place_citation(l, color_score=[22, 30, 50]))
    citation_list.sort()

    for p, c in citation_list:
        place = p+cnt
        seg_text_list.insert(place, c)
        cnt += 1
    text = ''.join(seg_text_list)
    text = re.sub(f'{dummy_char}+', ' ', text)
    # text = re.sub('(\(.*?\))(\s+)(\.|,)', '\g<1>\g<3>', text)
    print(text)
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
    range_ref = Ref('Toledot_Yitzchak_on_Torah, Numbers.30')
    links = get_links_from_file('Toledot Yitzchak on Torah, Numbers.json')
    link_dict = order_links_by_segments(links)  #,"Selichot_Nusach_Ashkenaz_Lita")
    for r in range_ref.all_segment_refs():
        new_texts_dict.update(get_segment(r, score=22, link_source=link_dict))
        # new_texts_dict.update(get_local_seg(r))
    push_text_w_citations(range_ref.text('he').version(), new_texts_dict)