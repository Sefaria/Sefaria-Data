import django

django.setup()

superuser_id = 171118
# import statistics
# import csv
from sefaria.model import *
# from sefaria.helper.schema import insert_last_child, reorder_children
# from sefaria.helper.schema import remove_branch
# from sefaria.tracker import modify_bulk_text
# from sefaria.helper.category import create_category
# from sefaria.system.database import db
# from sefaria.utils.talmud import daf_to_section, section_to_daf
# from bs4 import BeautifulSoup
# import re
# import copy



# {
#     "refs": [
#       "Abarbanel on Guide for the Perplexed, Introduction, Letter to R Joseph son of Judah 2",
#       "Guide for the Perplexed, Introduction, Letter to R Joseph son of Judah 3"
#     ],
#     "generated_by": "Yachin Parse Script",
#     "type": "commentary",
#     "auto": Frue
#   }
def create_new_link(ref0, ref1, generated_by, auto):
    l = Link({
         "refs": [
      ref0,
      ref1
    ],
    "generated_by": generated_by,
    "type": "commentary",
    "auto": auto
  })
    return l

def fix_yachin_links():
    query = {
        "$and": [
            {"$or": [
                {"refs.0": {"$regex": "Yachin"}},
                {"refs.1": {"$regex": "Yachin"}}
            ]},
            {"type": "commentary"}
        ]
    }
    links = LinkSet(query).array()
    # filtered_links = [l for l in links if l.refs[1].endswith("Mishnah Berakhot 1:4") or l.refs[0].endswith("Mishnah Berakhot 1:4")]
    filtered_links = links
    updated_links = []
    for l in filtered_links:
        updated_links.append(
            create_new_link(Ref(l.refs[0]).as_ranged_segment_ref().tref, Ref(l.refs[1]).as_ranged_segment_ref().tref, l.generated_by, l.auto))
    for l in filtered_links:
        l.delete()
    for l in updated_links:
        try:
            l.save()
        except Exception as e:
            print(f"Error saving link: {e}")
def create_boaz_links():
    all_yachin_commentary_links = LinkSet({
        "$and": [
            {"$or": [
                {"refs.0": {"$regex": "Yachin"}},
                {"refs.1": {"$regex": "Yachin"}}
            ]},
            {"type": "commentary"}
        ]
    }).array()
    boaz_query = {
        "$and": [
            {"$or": [
                {"refs.0": {"$regex": "Boaz"}},
                {"refs.1": {"$regex": "Boaz"}}
            ]},
            {"type": "commentary"}
        ]
    }
    links = LinkSet(boaz_query).array()
    filtered_links = [l for l in links if l.refs[1].startswith("Yachin") or l.refs[0].startswith("Yachin")]
    new_links = []
    for l in filtered_links:
        if l.refs[1].startswith("Yachin"):
            # print(l.refs[0])
            mishnah_ref = [yl.refs for yl in all_yachin_commentary_links if yl.refs[0] == l.refs[1] or yl.refs[1] == l.refs[1]][0]
            if mishnah_ref[0].startswith("Mishnah"):
                mishnah_ref = mishnah_ref[0]
            else:
                mishnah_ref = mishnah_ref[1]
            new_links.append(create_new_link(l.refs[0], mishnah_ref, l.generated_by, l.auto))

    for l in new_links:
        try:
            l.save()
        except Exception as e:
            print(f"Error saving link: {e}")

if __name__ == '__main__':
    print("hello world")
    # fix_yachin_links()
    create_boaz_links()
    print("end")











