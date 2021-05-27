import django, re, requests, json
django.setup()
from sources.functions import *
from sources.Scripts.pesukim_linking import link2url
from sefaria.tracker import modify_bulk_text

# read book segment links from DB (or while posting?)
# read book segment textChunk from DB
# find place in seg (CharLevelData)
# paste in the pasukRef in normal hebrew.
dummy_char = "█"

def get_segment(ref, score=22):
    tc = ref.text('he')
    tc.vtitle = tc.version().versionTitle  # this makes some sense because it is always on a single segment
    seg_text = tc.text
    seg_text_list = list(re.sub('\s+', dummy_char, seg_text))
    ls = LinkSet({"refs": ref.normal(), "type": "qutation", "score": {"$gte": score}})
    text_w_citations = add_citations(ls, seg_text_list, ref.normal())
    push_text_w_citations(Version().load({"title": "Yalkut Shimoni on Torah"}), {ref.normal(): text_w_citations})
    print(f"check {link2url(list(ls)[0], sandbox='quotations')}")


def get_place_citation(link):
    place = link.charLevelData["charLevelDataBook"]['endChar']
    pasuk_ref = Ref(link.refs[0])  # if link.refs[1] == book_ref else Ref(link.refs[1])
    citation = f"{dummy_char}({pasuk_ref.normal('he')}){dummy_char}"
    return place, citation


def add_citations(ls, seg_text_list, book_ref):
    citation_list =[]
    cnt = 0

    for l in list(ls):
        citation_list.append(get_place_citation(l))

    citation_list.sort()

    for p,c in citation_list:
        place = p+cnt
        seg_text_list.insert(place, c)
        cnt += 1
    text = ''.join(seg_text_list)
    text = re.sub(f'{dummy_char}+', ' ', text)
    print(text)
    return text


def push_text_w_citations(version, new_texts_dict):
    modify_bulk_text(UID, version, new_texts_dict)
    # tc.text = new_text
    # tc.save()


if __name__ == '__main__':
    get_segment(Ref('Yalkut Shimoni on Torah 730:1'))