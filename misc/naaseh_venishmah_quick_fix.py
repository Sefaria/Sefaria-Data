import django

django.setup()

from sefaria.model import *


def fix_nvn():
    nvn_topic_stub = Topic({"slug": "naaseh-venishmah",
                            "titles": [{"lang": "en", "primary": True, "text": "naaseh-venishmah"}]}).save()
    existing_nvn_topic = Topic().load({"slug": "naaseh-venishma"})
    # Delete broken link which interferes with merge (the Ref is invalid and does not exist)
    broken_link = RefTopicLink().load({"toTopic": "naaseh-venishmah", "ref": "Ner Mitzvah, The Kingdom of Greece wishes to uproot the bond between Israel and God 11"})
    broken_link.delete()
    existing_nvn_topic.merge(nvn_topic_stub)


if __name__ == '__main__':
    fix_nvn()
