# -*- coding: utf-8 -*-

import re, codecs, django, unicodecsv, json
django.setup()
from collections import defaultdict
from sefaria.model import *
from sefaria.utils.hebrew import has_cantillation

ROOT = "research/knowledge_graph/bootstrapper"
RAMBAM_ROW_INDEX = 4636
upper_level_mapping = {
    "relationship": "relational quality",
    "moment in time": "zero-dimensional temporal region",
    "span of time": "one-dimensional temporal region",
    "meta halacha": "meta-halacha",
    "part of a day": "part of day"
}
edge_types_dict = {}


class Node(object):

    def __init__(self, id, en_name=u"", he_name=u"", en_transliteration=None, bfo_id=None, wikidata_id=None,
                 according_to=None, jeLink=None, heWikiLink=None, enWikiLink=None,
                 generation=None):
        self.id = id
        self.en_name = en_name if len(en_name) > 0 else id
        self.en_transliteration = en_transliteration
        self.he_name = he_name
        self.edges = defaultdict(set)
        self.bfo_id = bfo_id
        self.wikidata_id = wikidata_id
        self.according_to = according_to
        self.alt_en = set()
        self.alt_he = set()
        self.jeLink = jeLink
        self.heWikiLink = heWikiLink
        self.enWikiLink = enWikiLink
        self.generation = generation
        self.source_sheet_tags = set()
        self.he_source_sheet_tags = set()
        self.description = u""

    def add_edge(self, type, to_node_id):
        self.edges[type].add(to_node_id)

    def serialize(self):
        ret = {
            u"id": self.id,
            u"en": self.en_name,
            u"he": self.he_name,
            u"edges": {
                k: list(v) for k, v in self.edges.items()
            },
        }
        if self.bfo_id is not None:
            ret[u"bfo_id"] = self.bfo_id
        if self.according_to is not None:
            ret[u"according_to"] = self.according_to
        if self.en_transliteration is not None:
            ret[u"en_transliteration"] = self.en_transliteration
        if len(self.alt_en) > 0:
            ret[u"alt_en"] = list(self.alt_en)
        if len(self.alt_he) > 0:
            ret[u"alt_he"] = list(self.alt_he)
        if len(self.source_sheet_tags) > 0:
            ret[u"source_sheet_tags"] = list(self.source_sheet_tags)
        if len(self.description) > 0:
            ret[u"description"] = self.description
        return ret

    def get_types(self, types=None):
        if types is None:
            types = {self.id}
        isas = self.edges.get('is a', set())
        types |= isas
        for to_node_id in isas:
            try:
                temp_node = node_set[to_node_id]
            except KeyError:
                continue
            temp_node.get_types(types)
        return types

    def __str__(self):
        return u"{} - {}".format(self.id, self.en_name)

    def __repr__(self):
        return "Node(u'{}')".format(self.en_name)


class NodeSet(object):

    def __init__(self):
        self.items = {}
        self.items_by_wid = {}
        self.items_by_talmud_name = {}

    def __setitem__(self, id, node):
        if id in self.items:
            print u"Node {} already exists with this id".format(self.items[id])
            #raise Exception(u"Node {} already exists with this id".format(self.items[id]))
        self.items[id] = node
        if node.wikidata_id is not None:
            self.items_by_wid[node.wikidata_id] = node

    def __getitem__(self, id):
        return self.items[id]

    def get_by_wid(self, wid):
        return self.items_by_wid[wid]

    def get_by_talmud_name(self, talmud_name):
        return self.items_by_talmud_name[talmud_name]

    def serialize(self):
        return [
            v.serialize() for _, v in self.items.items()
        ]

    def add_edge_inverses(self):
        for k, v in self.items.items():
            for type, to_nodes in v.edges.items():
                for to_node in to_nodes:
                    try:
                        to_node_obj = self.items[to_node]
                    except KeyError:
                        continue
                    to_node_obj.add_edge(edge_types_dict[type], v.id)

    def validate(self):
        dup_edges_dict = defaultdict(set)
        for node_id, node in self.items.items():
            for edge_type, to_node_id_set in node.edges.items():
                for to_node_id in to_node_id_set:
                    if to_node_id not in self.items:
                        # validate that to_node_id exists
                        print u"1{} -- 2{} --> 3{} NOT VALID".format(node_id, edge_type, to_node_id)
                        print u"{} does not exist".format(to_node_id)
                    else:
                        # validate that node_id and to_node_id don't share another edge
                        for temp_edge_type, temp_to_node_id_set in node.edges.items():
                            if temp_edge_type == edge_type:
                                continue
                            if to_node_id in temp_to_node_id_set:
                                normal_order = node_id < to_node_id
                                a, b = (node_id, to_node_id) if normal_order else (to_node_id, node_id)

                                dup_edges_dict[(a, b)].add(edge_type if normal_order else edge_types_dict[edge_type])
                                dup_edges_dict[(a, b)].add(temp_edge_type if normal_order else edge_types_dict[temp_edge_type])
                                print u"{} - {}".format(node_id, to_node_id)
                                print u"HAVE DUPLICATE EDGES {} AND {}".format(temp_edge_type, edge_type)
        print u"DUPLICATE EDGES {}".format(len(dup_edges_dict))
        with open("{}/duplicate_edges.csv".format(ROOT), "wb") as fout:
            csv = unicodecsv.DictWriter(fout, ["A", "Edge", "B"])
            csv.writeheader()
            for (a, b), edge_type_set in dup_edges_dict.items():
                for edge_type in edge_type_set:
                    csv.writerow({"A": a, "Edge": edge_type, "B": b})


def read_csv(filename):
    with open("{}/{}".format(ROOT, filename), "rb") as fin:
        csv = unicodecsv.DictReader(fin)
        rows = [row for row in csv]
    return rows


aspaklaria_nodes = read_csv("aspaklaria_nodes.csv")    # DONE
final_topic_names = read_csv("final_topic_names.csv")  # DONE
new_topics_edges = read_csv("new_topics_edges.csv")    # DONE
upper_level_nodes = read_csv("upper_level_nodes.csv")  # DONE
tanakh_matched = read_csv("tanakh_matched.csv")        # DONE
tanakh_unmatched = read_csv("tanakh_unmatched.csv")    # DONE
tanakh_edges = read_csv("tanakh_edges.csv")            # DONE
edge_types = read_csv("edge_types.csv")                # DONE
sefer_haagada = read_csv("sefer_haagada.csv")          # DONE
talmud_matched = read_csv("talmud_matched.csv")        # DONE
talmud_unmatched = read_csv("talmud_unmatched.csv")    # DONE
talmud_edges = read_csv("talmud_edges.csv")            # DONE
source_sheets = read_csv("source_sheets.csv")          # DONE
halachic_edges = read_csv("halachic_edges.csv")

node_set = NodeSet()
print "START UPPER LEVEL"
# UPPER LEVEL
for row in upper_level_nodes:
    nid = row["Node"].lower()
    n = Node(nid, row["Node"], bfo_id=row["BFO ID"])
    if len(row["isa"]) > 0:
        n.add_edge("is a", row["isa"].lower())
    node_set[nid] = n

print "START EDGE TYPES"
# EDGE TYPES
for row in edge_types:
    if len(row["Edge Inverse"]) > 0:
        edge_types_dict[row["Edge"]] = row["Edge Inverse"]
        edge_types_dict[row["Edge Inverse"]] = row["Edge"]

print "START ASPAKLARIA"
# ASPAKLARIA
for row in aspaklaria_nodes:
    n = Node(row["Topic"], according_to=(row["According to"] if len(row["According to"]) else None))
    isa = row["Is A Type Of"] if row["Is A Type Of"] not in upper_level_mapping else upper_level_mapping[row["Is A Type Of"]]
    n.add_edge("is a", isa)
    if len(row["Is a Type Of (2)"]) > 0:
        isa2 = row["Is a Type Of (2)"] if row["Is a Type Of (2)"] not in upper_level_mapping else upper_level_mapping[
            row["Is a Type Of (2)"]]

        n.add_edge("is a", isa2)
    node_set[row["Topic"]] = n

print "START TANAKH UNMATCHED"
# TANAKH UNMATCHED
for row in tanakh_unmatched:
    wid = re.findall(ur"Q\d+$", row["URL"])[0]
    n = Node(wid, row["English Name"], row["Hebrew Name"], wikidata_id=wid)
    n.add_edge("is a", "biblical person")
    node_set[wid] = n

print "START TALMUD UNMATCHED"
# TALMUD UNMATCHED
for row in talmud_unmatched:
    jeLink = row["jeLink"] if len(row["jeLink"]) > 0 else None
    heWikiLink = row["heWikiLink"] if len(row["heWikiLink"]) > 0 else None
    enWikiLink = row["enWikiLink"] if len(row["enWikiLink"]) > 0 else None

    n = Node(row["English Name"], row["English Name"], row["Hebrew Name"], generation=row["generation"], jeLink=jeLink,
             heWikiLink=heWikiLink, enWikiLink=enWikiLink)
    n.add_edge("is a", "mishnaic person" if row["Time Period"] == 'mishnah' else "talmudic person")
    node_set[row["English Name"]] = n
    node_set.items_by_talmud_name[row["English Name"]] = n

print "START RAMBAM"
# RAMBAM
with codecs.open(u"{}/../rambam/rambam_topic_hierarchy.json".format(ROOT), "rb", encoding="utf8") as fin:
    rambam = json.load(fin)
    for row in rambam:
        rid = "RAMBAM|{}".format(row["en"])
        n = Node(rid, row["en"])
        for p in row["parents"]:
            n.add_edge("is a", "RAMBAM|{}".format(p))
        if len(row["parents"]) == 0:
            n.add_edge("is a", "halacha")
        node_set[rid] = n

print "START SEFER HAAGADA MATCHED"
# SEFER HAAGADA MATCHED
for row in sefer_haagada:
    if len(row["Aspaklaria Topic"].strip()) > 0:
        n = node_set[row["Aspaklaria Topic"]]
        n.alt_he.add(row["Topic Name"])

print "START TOPIC NAMES"
# TOPIC NAMES
for irow, row in enumerate(final_topic_names):
    # TODO deal with Rambam and Sefer Ha'agada
    try:
        n = node_set[row["Topic"]]
    except KeyError:
        if irow >= RAMBAM_ROW_INDEX and len(row["English description"].strip()) > 0:
            n = node_set["RAMBAM|{}".format(row["English description"].strip())]
        elif irow >= RAMBAM_ROW_INDEX and has_cantillation(row["Topic"], detect_vowels=True):
            # Sefer Haagada
            n = Node(row["Topic"])
            n.add_edge("is a", row["Is A Type Of"])
            if len(row["Is a Type Of (2)"].strip()) > 0:
                n.add_edge("is a", row["Is a Type Of (2)"])
            node_set[row["Topic"]] = n
        else:
            continue
    description = u""
    final_english = row["Final English Translation"]
    if len(row["Is Paren Good Description"]) > 0:
        match = re.search(ur"^(.*)\(([^)]+)\)\s*$", final_english)
        final_english = match.group(1).strip()
        description = match.group(2)
    if len(row["According to:"]) > 0:
        if len(description) > 0:
            description += u". "
        description += u"Translated according to {}".format(row["According to:"])
    n.en_name = final_english
    n.description = description
    n.en_transliteration = row["Final English Transliteration"] if len(row["Final English Transliteration"]) else None
    n.he_name = row["Final Topic Name"].strip()

print "START TANAKH MATCHED"
# TANAKH MATCHED
for row in tanakh_matched:
    if len(row["Match Name"]) > 0:
        n = node_set[row["Name"]]
        alt_he = row["Match Name"]
        alt_en = row["Match En Name"]
        if len(n.en_name) == 0:
            n.en_name = alt_en
        else:
            n.alt_en.add(alt_en)
        if len(n.he_name) == 0:
            n.he_name = alt_he
        else:
            n.alt_he.add(alt_he)
        n.wikidata_id = row["Match ID"]
        node_set.items_by_wid[n.wikidata_id] = n

print "START TALMUD MATCHED"
# TALMUD MATCHED
for row in talmud_matched:
    if len(row["Match Name En"]) > 0:
        n = node_set[row["Name"]]
        alt_he = row["Match Name 1"]
        alt_en = row["Match Name En"]
        if len(n.en_name) == 0 and alt_en != n.en_transliteration:
            n.en_name = alt_en
        elif alt_en != n.en_name and alt_en != n.en_transliteration:
            n.alt_en.add(alt_en)
        if len(n.he_name) == 0:
            n.he_name = alt_he
        elif alt_he != n.he_name:
            n.alt_he.add(alt_he)
        try:
            yo = node_set[row["Match Name En"]]
            print u"{} EXISTS!!".format(row["Match Name En"])
        except KeyError:
            pass
        node_set.items_by_talmud_name[row["Match Name En"]] = n

print "START EDGES"
# EDGES
for row in new_topics_edges:
    if len(row["Topic"]) == 0 or len(row["Has Edge"]) == 0 or len(row["To Topic (Actual)"]) == 0:
        continue
    try:
        n = node_set[row["Topic"]]
    except KeyError:
        print u"KeyError: {}".format(row["Topic"])
        continue
    n.add_edge(row["Has Edge"], row["To Topic (Actual)"])

print "START TANAKH EDGES"
# TANAKH EDGES
male_female_dict = {
    "female": u"נקבה",
    "male": u"זכר"
}
# manually add king of israel / judah which are relevant to tanakh edges
n = Node(u"מלך יהודה", "King of Judah", u"מלך יהודה")
n.add_edge("is a", u"מלך מלכות")
node_set[u"מלך יהודה"] = n
n = Node(u"מלך ישראל", "King of Israel", u"מלך ישראל")
n.add_edge("is a", u"מלך מלכות")
node_set[u"מלך ישראל"] = n
for row in tanakh_edges:
    try:
        n = node_set.get_by_wid(row["ID"])
    except KeyError:
        # for some reason doesn't exist yet. create it
        n = Node(row["ID"], row["Name"], row["He Name"], wikidata_id=row["ID"])
        node_set[row["ID"]] = n
for row in tanakh_edges:
    try:
        n = node_set.get_by_wid(row["Value ID"])
    except KeyError:
        # for some reason doesn't exist yet. create it
        n = Node(row["Value ID"], row["Value"], wikidata_id=row["Value ID"])
        node_set[row["Value ID"]] = n
        print u"Created Value {}".format(row["Value ID"])
for row in tanakh_edges:
    n = node_set.get_by_wid(row["ID"])
    value = row["Value"]
    if row["Edge"] == "alternate spelling of":
        # just add the alt title
        if len(n.he_name) == 0:
            n.he_name = value
        else:
            n.alt_he.add(value)
    elif row["Edge"] == "has transliteration":
        if len(n.en_name) == 0:
            n.en_name = value
        else:
            n.alt_en.add(value)
    else:
        if value in male_female_dict:
            to_node_id = male_female_dict[value]
        else:
            if len(row["Value ID"]) == 0:
                to_node_id = value
            else:
                try:
                    to_node_id = node_set.get_by_wid(row["Value ID"]).id
                except KeyError:
                    print row["Value ID"]
                    continue
        n.add_edge(row["Edge"], to_node_id)

print "START TALMUD EDGES"
# TALMUD EDGES
for row in talmud_edges:
    try:
        n = node_set.get_by_talmud_name(row["Name"])
    except KeyError:
        person = Person().load({"key": row["Name"]})

        n = Node(row["Name"], row["Name"], person.primary_name('he'), jeLink=getattr(person, 'jeLink', None),
                 heWikiLink=getattr(person, 'heWikiLink', None), enWikiLink=getattr(person, 'enWikiLink', None))
        node_set[row["Name"]] = n
        node_set.items_by_talmud_name[row["Name"]] = n
    try:
        n = node_set.get_by_talmud_name(row["Value"])
    except KeyError:
        person = Person().load({"key": row["Value"]})

        n = Node(row["Value"], row["Value"], person.primary_name('he'), jeLink=getattr(person, 'jeLink', None),
                 heWikiLink=getattr(person, 'heWikiLink', None), enWikiLink=getattr(person, 'enWikiLink', None))
        node_set[row["Value"]] = n
        node_set.items_by_talmud_name[row["Value"]] = n

for row in talmud_edges:
    try:
        n = node_set.get_by_talmud_name(row["Name"])
    except KeyError:
        print row["Name"]
        print "NAME"
        continue
    try:
        to_node = node_set.get_by_talmud_name(row["Value"])
    except KeyError:
        print row["Value"]
        print "VALUE"
        continue
    n.add_edge(row["Edge"], to_node.id)

print "START SOURCE SHEETS"
# SOURCE SHEETS
for row in source_sheets:
    # if aspak -> if not synon -> else -> match it
    # else, if not isCat, -> is a "is a type of" else
    he = row["hebrew tag"]
    en = row["tag"]
    if len(row["aspaklaria topic"]) > 0 and len(row["not synonym"]) == 0:
        n = node_set[row["aspaklaria topic"]]
        if len(n.en_name) == 0 and en != n.en_transliteration:
            n.en_name = en
        elif len(en) > 0 and en != n.en_name:
            n.alt_en.add(en)
        if len(n.he_name) == 0:
            n.he_name = he
        elif len(he) > 0 and he != n.he_name:
            n.alt_he.add(he)
        n.source_sheet_tags.add(en)
    else:
        isa = row["is a type of"] if row["is a type of"] not in upper_level_mapping else upper_level_mapping[
            row["is a type of"]]
        n = node_set[isa]

        if row["is category"]:
            if len(n.en_name) == 0 and en != n.en_transliteration:
                n.en_name = en
            elif len(en) > 0 and en != n.en_name:
                n.alt_en.add(en)
            if len(n.he_name) == 0:
                n.he_name = he
            elif len(he) > 0 and he != n.he_name:
                n.alt_he.add(he)
            n.source_sheet_tags.add(en)
        else:
            _id = u"{}|{}".format(he, en)
            m = Node(_id, en, he)
            m.source_sheet_tags.add(en)
            m.add_edge("is a", n.id)
            node_set[_id] = m

print "START HALACHIC EDGES"
# HALACHIC EDGES
for row in halachic_edges:
    if len(row["rambam topic"]) > 0:
        n = node_set[row["topic"]]
        edge_type = "applies halacha" if "halachic process" in n.get_types() else "related to"
        n.add_edge(edge_type, "RAMBAM|{}".format(row["rambam topic"].strip()))






# CLEAN UP
node_set.add_edge_inverses()
node_set.validate()
final_nodes = node_set.serialize()
with codecs.open("{}/final_topics.json".format(ROOT), "wb", encoding="utf8") as fout:
    json.dump(final_nodes, fout, indent=2, ensure_ascii=False)

with open("{}/final_topic_edges.csv".format(ROOT), "wb") as fout:
    csv = unicodecsv.DictWriter(fout, ['A', 'Edge', 'B'])
    csv.writeheader()
    rows = []
    for n in final_nodes:
        for k, v in n['edges'].items():
            for to_node_id in v:
                rows += [{'A': n['id'], 'Edge': k, 'B': to_node_id}]
    csv.writeheader()
    csv.writerows(rows)
