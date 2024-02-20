import django

django.setup()

from sefaria.model import *


# The goal of this script is to remove the "parent" categories from the following
# topics (represented below by their URLs).
# Topics do not have categories the way that Indices do. Topic categories
# are controlled by the TopicLinks, a topic fromTopic x toTopic y, with a class of "intraTopic"
# and a linkType of dependent indicates that x is under parent y.
# To remove x from y "category", we simply remove the link between the two.

def remove_parent_topic_category(from_topic_slug, to_topic_slug=None):
    # Remove "categories" (i.e. parent links) for the slugs
    query = {'fromTopic': from_topic_slug,
             'class': 'intraTopic',
             'linkType': 'displays-under'}

    if to_topic_slug:
        # Add specific parent if specified
        query['toTopic'] = to_topic_slug

    tls = IntraTopicLinkSet(query)
    if tls:
        topic_link = tls[0]
        print(topic_link)
        topic_link.delete()
        print(f"Deleting category for {from_topic_slug}")


if __name__ == '__main__':

    slugs = [
        "festivals",
        "jewish-calendar2",
        "kaddish-and-kedushah",
        "lifecycle",
        "losses",
        "united-states-law",
        "festivals",
        "moses-prayer",
        "moses-prayer-for-himself",
        "praise-of-god",
        "priestly-blessing"
    ]

    # Remove all parents for these slugs
    for s in slugs:
        remove_parent_topic_category(from_topic_slug=s)

    # Specifically remove Sefirot from Beliefs, and no other
    # parent categories (i.e. "Kabbalah").
    remove_parent_topic_category(from_topic_slug='sefirot',
                                 to_topic_slug='beliefs')
