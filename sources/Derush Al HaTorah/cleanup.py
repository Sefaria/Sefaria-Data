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
links = []
for i in [6, 7]:
    base_refs = {}
    for r in [Ref(f"Derush Al HaTorah {i}")]:#, Ref("Derush Al HaTorah 7")]:
        for ref in r.all_segment_refs():
            nums = re.findall('<i data-commentator="Notes by Rabbi Yehoshua Hartman" data-label="(\d+)"></i>', ref.text('he').text)
            assert len(nums) - len(ref.linkset()) in [-1, 0, 1]
            nums = [int(x) for x in nums]
            base_refs[ref.normal()] = nums
    for r in [Ref(f"Notes by Rabbi Yehoshua Hartman on Derush Al HaTorah {i}")]:#, Ref("Notes by Rabbi Yehoshua Hartman on Derush Al HaTorah 7")]:
        for ref in r.all_segment_refs():
            LinkSet(ref).delete()
            if ref.text('he').text == "":
                continue
            nums = re.findall("\((\d+)\)", ref.text('he').text)
            assert len(nums) == 1
            num = int(nums[0])
            for x in base_refs:
                if num in base_refs[x]:
                    l = Link({"refs": [x, ref.normal()], "generated_by": "derush_al_hatorah_refactor", "auto": True, "type": "Commentary"})
                    l.inline_reference = {"data-commentator": "Notes by Rabbi Yehoshua Hartman", "data-order": num}
                    l.save()
                    break
