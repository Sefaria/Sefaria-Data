import django

django.setup()
from sefaria.model import *
from django_topics.models import Topic as DjangoTopic
from sefaria.helper.schema import *
import csv

topic_10_slugs = [
    "abortion", "adams-sin-and-his-punishment", "al-hanisim", "avodat-hashem", "bal-tashchit",
    "balaam", "bar-mitzvah", "beit-midrash", "ben-sorer-umoreh", "birkot-hashachar", "compassion",
    "curses", "daughters-of-zelophehad", "demons", "dinah", "distinctions-of-the-land-of-israel",
    "elisha-ben-abuya", "faith", "food", "forgiveness", "forgiveness-(מחילה)", "free-will", "friendship",
    "gabriel-the-angel", "gehinnom", "giving", "gods-blessing-and-promise-to-abraham", "gog-and-magog",
    "gratitude", "hannah", "hate", "hillel", "hope", "humility", "israel", "jerusalem", "jewish-unity",
    "justice", "kehillah", "kiddush", "kindness", "lashon-hara", "leadership", "leviathan", "lilith",
    "love", "love-of-god1", "machloket-lshem-shamayim", "mah-tovu", "matzah", "metatron",
    "nachshon-ben-aminadav", "nephilim", "noah", "non-jews", "oils1", "olam-haba", "parah-adumah",
    "pirkei-avot", "plague-of-blood", "plague-of-darkness", "plague-of-frogs", "plague-of-hail",
    "plague-of-the-firstborn", "plague-of-wild-animals", "rabban-gamliel", "rabban-yochanan-b-zakkai",
    "rabbi-eliezer-b-hyrcanus", "rabbi-meir", "rabbi-yehoshua-b-levi", "reincarnation", "responsibility",
    "revenge", "samael", "serah-the-daughter-of-asher", "shacharit", "shalom-bayit", "shalosh-regalim",
    "shemini-atzeret", "shemoneh-esrei", "shimon-bar-yochai", "silence", "splitting-of-the-red-sea",
    "tashlich", "the-exodus-from-egypt", "the-four-rivers", "the-prophecy-of-ezekiel", "the-tree-of-knowledge",
    "tikkun", "tikkun-olam", "torah-scrolls", "tower-of-babel", "truth", "unity", "vahavta", "values", "wars",
    "welcoming-guests", "yirat-shamayim", "yom-haatzmaut", "yom-hashoah"
]


def list_to_csv(data, filename):
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)

        for row in data:
            writer.writerow(row)

def get_no_description_slugs_csv():
    no_description_slugs = []
    library_topics_slugs = list(DjangoTopic.objects.get_topic_slugs_by_pool("library"))
    library_topics = TopicSet(query={"slug": {"$in": library_topics_slugs}}).array()
    for topic in library_topics:
        if not getattr(topic,"description", {}).get('en') or len(topic.description.get('en', '')) < 20:
            no_description_slugs.append(topic.slug)

    list_to_csv([[slug] for slug in no_description_slugs], "no_description_slugs.csv")
def get_no_description_top_slugs_csv():
    no_description_top_slugs = []
    top_topics = TopicSet(query={"slug": {"$in": topic_10_slugs}}).array()
    for topic in top_topics:
        if not getattr(topic,"description", {}).get('en') or len(topic.description.get('en', '')) < 20:
            no_description_top_slugs.append(topic.slug)
    list_to_csv([[slug] for slug in no_description_top_slugs], "no_description_top_slugs.csv")

if __name__ == '__main__':
    get_no_description_top_slugs_csv()
    print("hi")
