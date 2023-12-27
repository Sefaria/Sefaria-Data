import django
django.setup()
from sefaria.model import *
def custom_func(item):
    return item.get_primary_title('en').replace("Ḥ", "H")

k = Topic.init('kabbalah')
k.isTopLevelDisplay = True
k.displayOrder = 85
k.save()
# for t in TopicSet({'titles.text': {"$regex": "\(Kabbalah"}}):
#     for i, title in enumerate(t.titles):
#         t.titles[i]['disambiguation'] = "Kabbalah"
#         t.titles[i]['text'] = t.titles[i]['text'].replace(" (Kabbalah)", "")
#     t.save()

for t in TopicSet({'titles.disambiguation': 'Kabbalah'}):
    link = {"toTopic": "kabbalah", "fromTopic": t.slug, "linkType": "displays-under", "dataSource": "sefaria"}
    if IntraTopicLink().load(link) is None:
        print(f"Creating new link {t.slug}")
        new_link = IntraTopicLink(link)
        new_link.save()

topics = TopicSet({'titles.disambiguation': 'Kabbalah'}).array()
topics.sort(key=custom_func)
for i, t in enumerate(topics):
    print(t.slug)
    t.displayOrder = i * 10
    t.save()
