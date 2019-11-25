import django
from functools import reduce
django.setup()
import re, unicodecsv, codecs, json, random
from collections import defaultdict
from sefaria.model import *
from sefaria.system.exceptions import InputError

# TODO add more commentaries (e.g. Rashi, Tosafot, Steinsaltz)

HALAKHIC_BOOKS = [
    "Tur",
    "Sefer Mitzvot Gadol",
    "Sefer HaChinukh"
] + library.get_indexes_in_category("Bavli") + library.get_indexes_in_category("Shulchan Arukh")

SA_COMMENTARIES = [
    "Ba'er Hetev",
    "Biur Halacha",
    "Kaf HaChayim",
    "Magen Avraham",
    "Mishnah Berurah",
    "Sha'arei Teshuvah",
    "Chokhmat Shlomo",
    "Eshel Avraham",
    "Yad Ephraim",
    "Pithei Teshuva",
    "Siftei Kohen",
    "Turei Zahav",
]

all_sa = list()
all_sa_map = {}
for index in library.get_indexes_in_category("Shulchan Arukh", full_records=True):
    for r in index.all_segment_refs():
        all_sa += [{"ref": r, "topics": set()}]
        all_sa_map[r.normal()] = len(all_sa) - 1


def is_halakic_link(l):
    if not any([Ref(r).index.title == "Sefer HaChinukh" for r in l.refs]) and (l.generated_by is None or not l.generated_by.startswith("Ein Mishpat Cluster")):
        return False
    for r in l.refs:
        try:
            if Ref(r).index.title in HALAKHIC_BOOKS:
                return True
        except InputError:
            continue
    return False


def is_topical_link_of_sa(l):
    for r in l.refs:
        try:
            rr = Ref(r)
            if getattr(rr.index, "collective_title", None) in SA_COMMENTARIES:
                if l.type == "commentary" and rr.primary_category == "Commentary":
                    # not quoting commentary
                    return True
        except InputError:
            continue
    return False


topic_hierarchy = []
topic_hierarchy_map = {}
leaf_topic_refs = defaultdict(set)
total = 0
with open("research/knowledge_graph/rambam/rambam_ontology.csv", "rb") as fin:
    csv = unicodecsv.DictReader(fin)

    for row in csv:
        mt = Ref("Mishneh Torah, {}".format(row["Chapter"]))
        curr_topic1 = row["Topic Level 1"].strip()
        curr_topic2 = row["Topic Level 2"].strip()
        curr_topic3 = row["Topic Level 3"].strip()
        curr_topic4 = row["Topic Level 4"].strip()
        curr_topic5 = row["Leaf Topic En"].strip()
        has_topic2 = curr_topic2 != "-" and len(curr_topic2) > 0
        has_topic3 = curr_topic3 != "-" and len(curr_topic3) > 0
        has_topic4 = curr_topic4 != "-" and len(curr_topic4) > 0
        topic2_parent = curr_topic1
        topic3_parent = curr_topic2 if has_topic2 else curr_topic1
        topic4_parent = curr_topic3 if has_topic3 else (curr_topic2 if has_topic2 else curr_topic1)
        topic5_parent = curr_topic4 if has_topic4 else (curr_topic3 if has_topic3 else (curr_topic2 if has_topic2 else curr_topic1))
        if len(row["Is Aspaklaria Topic"]) == 0:
            if curr_topic1 not in topic_hierarchy_map:
                topic_hierarchy += [{"en": curr_topic1, "parents": []}]
                topic_hierarchy_map[curr_topic1] = len(topic_hierarchy) - 1
            if curr_topic2 not in topic_hierarchy_map and has_topic2:
                topic_hierarchy += [{"en": curr_topic2, "parents": [topic2_parent]}]
                topic_hierarchy_map[curr_topic2] = len(topic_hierarchy) - 1
            elif curr_topic2 in topic_hierarchy_map and topic2_parent not in topic_hierarchy[topic_hierarchy_map[curr_topic2]]["parents"]:
                topic_hierarchy[topic_hierarchy_map[curr_topic2]]["parents"] += [topic2_parent]
            if curr_topic3 not in topic_hierarchy_map and has_topic3:
                topic_hierarchy += [{"en": curr_topic3, "parents": [topic3_parent]}]
                topic_hierarchy_map[curr_topic3] = len(topic_hierarchy) - 1
            elif curr_topic3 in topic_hierarchy_map and topic3_parent not in topic_hierarchy[topic_hierarchy_map[curr_topic3]]["parents"]:
                topic_hierarchy[topic_hierarchy_map[curr_topic3]]["parents"] += [topic3_parent]
            if curr_topic4 not in topic_hierarchy_map and has_topic4:
                topic_hierarchy += [{"en": curr_topic4, "parents": [topic4_parent]}]
                topic_hierarchy_map[curr_topic4] = len(topic_hierarchy) - 1
            elif curr_topic4 in topic_hierarchy_map and topic4_parent not in topic_hierarchy[topic_hierarchy_map[curr_topic4]]["parents"]:
                topic_hierarchy[topic_hierarchy_map[curr_topic4]]["parents"] += [topic4_parent]
            if curr_topic5 not in topic_hierarchy_map:
                topic_hierarchy += [{"en": curr_topic5, "parents": [topic5_parent]}]
                topic_hierarchy_map[curr_topic5] = len(topic_hierarchy) - 1
            elif curr_topic5 in topic_hierarchy_map and topic5_parent not in topic_hierarchy[topic_hierarchy_map[curr_topic5]]["parents"]:
                topic_hierarchy[topic_hierarchy_map[curr_topic5]]["parents"] += [topic5_parent]
        leaf_topic_refs[curr_topic5].add(mt.normal())
        links = list(filter(is_halakic_link, mt.linkset().array()))
        total += len(links)
        for l in links:
            for r in l.refs:
                rr = Ref(r)
                if not rr.index.title.startswith("Mishneh Torah"):
                    sa_index = all_sa_map.get(r, None)
                    if sa_index is not None:
                        sa_links = list(filter(is_topical_link_of_sa, rr.linkset().array()))
                        for sa_link in sa_links:
                            for sa_r in sa_link.refs:
                                sa_rr = Ref(sa_r)
                                if not sa_rr.index.title.startswith("Shulchan Arukh"):
                                    total += 1
                                    leaf_topic_refs[curr_topic5].add(sa_rr.normal())
                        all_sa[sa_index]["topics"] |= {curr_topic5}

                    leaf_topic_refs[curr_topic5].add(rr.normal())

for k, v in list(leaf_topic_refs.items()):
    temp_list = list(v)
    temp_list.sort(key=lambda x: Ref(x).order_id())
    leaf_topic_refs[k] = temp_list
with open("research/knowledge_graph/rambam/leaf_topic_refs.json", "wb") as fout:
    json.dump(leaf_topic_refs, fout, ensure_ascii=False, indent=2)
with codecs.open("research/knowledge_graph/rambam/rambam_topic_hierarchy.json", "wb", encoding="utf8") as fout:
    json.dump(topic_hierarchy, fout, ensure_ascii=False, indent=2)

num_simanim_with_more_than_one_topic = 0
num_simanim_with_no_topics = 0
num_simanim_with_one_topic = 0
num_simanim = 0


def get_topic_string_from_siman(oref):
    tc = TextChunk(oref, lang="he")
    match = re.match(r"<(?:strong|b)>([^<]+)</(?:strong|b)>", tc.text[0])
    if match:
        return match.group(1)
    return None


def deal_with_siman(siman):
    global num_simanim_with_no_topics, num_simanim_with_one_topic, num_simanim_with_more_than_one_topic, num_simanim
    num_simanim += 1
    topics = reduce(lambda a, b: a | b["topics"], siman, set())
    siman_not_complete = False
    if any([len(s["topics"]) == 0 for s in siman]):
        siman_not_complete = True
    if len(topics) == 0:
        num_simanim_with_no_topics += 1
    elif len(topics) == 1:
        num_simanim_with_one_topic += 1
        if siman_not_complete:
            print("SIMAN TOPIC {}".format(get_topic_string_from_siman(siman[0]["ref"].section_ref())))
            print("NOAHS TOPIC {}".format(list(topics)[0]))
    else:
        num_simanim_with_more_than_one_topic += 1


curr_siman = []
for sa in all_sa:
    if len(curr_siman) == 0 or curr_siman[-1]["ref"].sections[0] == sa["ref"].sections[0]:
        curr_siman += [sa]
    else:
        deal_with_siman(curr_siman)
        curr_siman = []
deal_with_siman(curr_siman)