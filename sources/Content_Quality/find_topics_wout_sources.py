import django
django.setup()
from sefaria.model import *
from tqdm import tqdm
all_topics = []
def get_all_children(x, flattened):
    if 'children' in x:
        for y in x['children']:
            get_all_children(y, flattened)
    else:
        flattened.append(x['slug'])

topics = library.get_topic_toc_json_recursive()
flattened = []
for x in topics:
    get_all_children(x, flattened)
actual_cases = []
for x in tqdm(flattened):
    rs = [x.ref for x in RefTopicLinkSet({'toTopic': x}).array() if not x.ref.startswith("Sheet")]
    if len(rs) == 0:
        actual_cases.append(x)
for x in tqdm(actual_cases):
    links = IntraTopicLinkSet({"toTopic": {"$exists": True}, "fromTopic": x, "linkType": "displays-under"})
    assert len(links) == 1
    link = links[0]
    if link.toTopic != "authors":
        print(x)
        link.delete()
        pass
    # else:
    #     books = IndexSet({'authors': x})
    #     if books.count() == 0:
    #         t = Topic.init(x)  # deal with subclass and check books
    #         if hasattr(t, 'subclass'):
    #             del t.subclass
    #         t.save()
    #         link.delete()
    #         print(f'didnt find books for {x}')
    #     else:
    #         print(f'found books for {x}')

