import django

django.setup()

from sefaria.model import *


def fix_nvn():
    nvn_topic_stub = Topic({"slug": "naaseh-venishmah",
                            "titles": {"lang": "en", "primary": True, "text": "naaseh-venishmah"}})
    existing_nvn_topic = Topic().load({"slug": "naaseh-venishma"})
    existing_nvn_topic.merge(nvn_topic_stub)


if __name__ == '__main__':
    fix_nvn()
