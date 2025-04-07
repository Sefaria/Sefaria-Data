import django
django.setup()
from collections import defaultdict
from sefaria.model import *
from sefaria.helper.schema import *

if __name__ == '__main__':
    all_topics = TopicSet()
    all_slugs = [t.slug for t in all_topics]

    for slug in all_slugs:
        all_ref_links = RefTopicLinkSet({"toTopic": slug})
        #count how many times each lang is missing from curatedPrimacy
        removal_counts = defaultdict(int)

        for ref_link in all_ref_links:
            order = ref_link.order
            curated_primacy = order.get('curatedPrimacy', {})
            available_langs = order.get('availableLangs', [])

            for lang in available_langs:
                if lang not in curated_primacy:
                    available_langs = [lang for lang in available_langs if lang in curated_primacy]
                    removal_counts[lang] += 1
            # ref_link.save()
    print("Done updating all slugs.")
