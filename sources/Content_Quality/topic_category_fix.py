import django

django.setup()

from sefaria.model import *

import re

urls = [
    "https://www.sefaria.org.il/topics/festivals?tab=sources",
    "https://www.sefaria.org/topics/jewish-calendar2?tab=sheets",
    "https://www.sefaria.org/topics/kaddish-and-kedushah?tab=sources",
    "https://www.sefaria.org/topics/lifecycle?tab=sheets",
    "https://www.sefaria.org/topics/losses?tab=sources",
    "https://www.sefaria.org/topics/united-states-law?tab=sources",
    "https://www.sefaria.org.il/topics/festivals?tab=sources",
    "https://www.sefaria.org/topics/moses-prayer?tab=sources",
    "https://www.sefaria.org/topics/moses-prayer-for-himself?tab=sources",
    "https://www.sefaria.org.il/topics/praise-of-god?sort=Relevance&tab=sources",
    "https://www.sefaria.org.il/topics/priestly-blessing?tab=sources"
]

# Regular expression pattern
pattern = r"https://www\.sefaria\.org.*?/topics/(.*)\?"

# List to store extracted slugs
slugs = []

# Extract slugs from URLs
for url in urls:
    match = re.search(pattern, url)
    if match:
        slugs.append(match.group(1))

# Remove "categories" (i.e. parent links) for the slugs
for s in slugs:
    print(s)
    tls = IntraTopicLinkSet({'fromTopic': s,
                             'class': 'intraTopic',
                             'linkType': 'displays-under'})
    if tls:
        topic_link = tls[0]
        topic_link.delete()
    print()

# Switch Sefirot from being under both "Beliefs" and "Kabbalah"
# to just "Kaballah".
tls = IntraTopicLinkSet({'fromTopic': 'sefirot',
                         'class': 'intraTopic',
                         'linkType': 'displays-under',
                         'toTopic': 'beliefs'})

if tls:
    topic_link=tls[0]
    topic_link.delete()