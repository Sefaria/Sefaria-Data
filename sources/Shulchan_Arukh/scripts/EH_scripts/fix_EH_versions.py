# encoding=utf-8

import re
import os
import django
django.setup()
from sefaria.model import *
from data_utilities.splice import SegmentSplicer
from sefaria.helper.schema import migrate_to_complex_structure

merging_refs = [
    Ref("Shulchan Arukh, Even HaEzer 169:57"),
    Ref("Shulchan Arukh, Even HaEzer 154:25"),
    Ref("Ba'er Hetev on Shulchan Arukh, Even HaEzer 169:52"),
    Ref("Beit Shmuel 90:5"),
    Ref("Beit Shmuel 156:15")
]
for r in merging_refs:
    for version in r.version_list():
        print u'{}:'.format(version['versionTitle'])
        print r.text(lang=version['language'], vtitle=version['versionTitle']).text.rstrip()
        tc = r.text(lang=version['language'], vtitle=version['versionTitle'])
        if not re.search(u'<br>$', tc.text):
            print "Fixing {}".format(version['versionTitle'])
            new_text = tc.text.rstrip()
            new_text += u'<br>'
            tc.text = new_text
            tc.save()
        else:
            print "Skipping {}".format(version['versionTitle'])

for r in merging_refs:
    splicer = SegmentSplicer()
    splicer.splice_this_into_next(r)
    splicer.execute()

    ls = r.linkset()
    for l in ls:
        new_ls = LinkSet({'refs': l.refs})
        if new_ls.count() > 1:
            print u"Duplicate link found for {}. Deleting".format(l.refs)
            l.delete()

total_refs = len(Ref("Shulchan Arukh, Even HaEzer 169").all_segment_refs())
moving_refs = Ref("Shulchan Arukh, Even HaEzer 169:57-{}".format(total_refs)).all_segment_refs()
conversion_map = [(r.normal(), "Shulchan Arukh, Even HaEzer, Seder Halitzah {}".format(i+1))
                  for i,r in enumerate(moving_refs)]
total_refs = len(Ref("Shulchan Arukh, Even HaEzer 154").all_segment_refs())
moving_refs = Ref("Shulchan Arukh, Even HaEzer 154:25-{}".format(total_refs)).all_segment_refs()
conversion_map.extend([(r.normal(), "Shulchan Arukh, Even HaEzer, Seder HaGet {}".format(i+1))
                       for i,r in enumerate(moving_refs)])

e_schema = library.get_index("Shulchan Arukh, Even HaEzer").schema
for i in conversion_map[-20:]:
    print i


def move_segment(ref_from, ref_to):
    old_ref_obj, new_ref_obj = Ref(ref_from), Ref(ref_to)
    versions = old_ref_obj.versionset()
    for version in versions:
        old_tc = old_ref_obj.text(version.language, version.versionTitle)
        new_tc = new_ref_obj.text(version.language, version.versionTitle)
        new_tc.text = old_tc.text
        new_tc.save()
        old_tc.text = ''
        old_tc.save()
    for link_obj in old_ref_obj.linkset():
        for i, r in enumerate(link_obj.refs):
            if Ref(r).normal() == old_ref_obj.normal():
                link_obj.refs[i] = new_ref_obj.normal()
        link_obj.save()


for conversion in conversion_map:
    move_segment(*conversion)

"""
Complexify Ba'er Hetev - requires a node for Seder Halitzah. Move 169:52-end
"""
old_bh_index = library.get_index(u"Ba'er Hetev on Shulchan Arukh, Even HaEzer")
old_bh_alt_titles = [x for x in old_bh_index.nodes.get_titles_object() if not x.get(u'primary', False)]
bh_schema_root = SchemaNode()
bh_schema_root.add_primary_titles(old_bh_index.nodes.primary_title('en'), old_bh_index.nodes.primary_title('he'))
default_node = JaggedArrayNode()
default_node.default = True
default_node.key = u'default'
default_node.add_structure([u'Siman', u'Seif Katan'])
bh_schema_root.append(default_node)
halitzah_node = JaggedArrayNode()
halitzah_node.add_primary_titles(u"Seder Halitzah", u"סדר חליצה")
halitzah_node.add_structure([u"Seif Katan"])
bh_schema_root.append(halitzah_node)
bh_schema_root.validate()

# move all refs from 169:52 onward to seder halitzah
reflist = Ref(u"Ba'er Hetev on Shulchan Arukh, Even HaEzer 169").all_segment_refs()[51:]
conversion_map = {r.normal(): u"Ba'er Hetev on Shulchan Arukh, Even HaEzer, Seder Halitzah {}".format(i+1)
                  for i, r in enumerate(reflist)}
all_refs = [r.normal() for r in old_bh_index.all_segment_refs()]
reg_refs = {r: r for r in all_refs if not conversion_map.get(r)}
conversion_map.update(reg_refs)
migrate_to_complex_structure(u"Ba'er Hetev on Shulchan Arukh, Even HaEzer", bh_schema_root.serialize(), conversion_map)
new_bh_index = library.get_index(u"Ba'er Hetev on Shulchan Arukh, Even HaEzer")
for title in old_bh_alt_titles:
    new_bh_index.nodes.add_title(**title)

if os.path.exists("./output_Ba'er Hetev on Shulchan Arukh, Even HaEzer_.txt"):
    os.remove("./output_Ba'er Hetev on Shulchan Arukh, Even HaEzer_.txt")
