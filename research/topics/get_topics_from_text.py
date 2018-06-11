# -*- coding: utf-8 -*-

import re
import django
import codecs
import json
from collections import defaultdict
django.setup()
from sefaria.model import *

def get_topics_in_2d_text(cat, cutoff, outfile):
    topics_dict = {}

    for ind in library.get_indexes_in_category(cat, full_records=True):
        for seg in ind.all_segment_refs():
            tref = seg.normal()
            tc = TextChunk(seg, "en")
            for m in re.finditer(ur"<i>(.+?)</i>", tc.text):
                topic = m.group(1).strip().lower()
                topic = re.sub(ur"[,.!?'’]", u"", topic)
                if topic in topics_dict:
                    temp_topic_dict = topics_dict[topic]
                    temp_topic_dict["count"] += 1
                else:
                    temp_topic_dict = {"count": 1, "refs": [], "he": u""}
                    topics_dict[topic] = temp_topic_dict
                temp_topic_dict["refs"] += [tref]

    topics_dict = filter(lambda x: x[1]["count"] > cutoff, topics_dict.items())
    with codecs.open(outfile, 'wb', encoding='utf8') as fout:
        json.dump(topics_dict, fout, ensure_ascii=False, indent=4)


get_topics_in_2d_text("Mishna", 10, "mishnah_topics.json")
get_topics_in_2d_text("Bavli", 20, "talmud_topics.json")