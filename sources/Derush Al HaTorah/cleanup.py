from sources.functions import *
# existing = set()
# for l in LinkSet({"refs": {"$regex": "^Notes by Rabbi Yehoshua Hartman on Derush Al HaTorah"}}):
#     existing.add(tuple(l.refs))
#
# for l in LinkSet({"refs": {"$regex": "^Notes by Rabbi Yehoshua Hartman on Derush Al HaTorah"}}):
#     if tuple(l.refs) in existing:
#         existing.remove(tuple(l.refs))
#         l.delete()
# print(len(existing))
# print(LinkSet({"refs": "^Notes by Rabbi Yehoshua Hartman on Derush Al HaTorah"}).count())
"""

3. Delete all ch 6 and ch 7 links
4. Go through ch 6 and 7 in footnotes, and grab number (233) and link it 
5. Run inline ref script again on just the affected links"""
for r in [Ref("Notes by Rabbi Yehoshua Hartman on Derush Al HaTorah 6"), Ref("Notes by Rabbi Yehoshua Hartman on Derush Al HaTorah 7")]:
    for ref in r.all_segment_refs():
        #LinkSet(ref).delete()
        print()
