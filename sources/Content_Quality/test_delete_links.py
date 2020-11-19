from sources.functions import *
link1 = {"refs": ["Genesis 6:23", "Eruvin 3a:4"], "type": "Commentary", "auto": True, "generated_by": "steve2"}
link2 = {"refs": ["Genesis 6:20", "Eruvin 2a:8"], "type": "Commentary", "auto": True, "generated_by": "steve2"}

post_link([link1, link2], skip_lang_check=True, server="http://localhost:8000")
link3 = {"refs": ["Genesis 6:2", "Eruvin 3a:1"], "type": "Commentary", "auto": True, "generated_by": "steve2"}
post_link(link3, server="http://localhost:8000")
# #
# first_try = delete_link("5c17b8cbb071e100bf4e3b54", server="http://localhost:8000")
# second_try = delete_link("Genesis 3000", server="http://localhost:8000")
# third_try = delete_link("5c17b8cbb071e100bf4e3b5", server="http://localhost:8000")
# fourth_try = delete_link("Genesis 30:5000", server="http://localhost:8000")
# #
# #
# # l = list(LinkSet(Ref("Genesis 19:10")))[2]
# # fifth_try = delete_link("Genesis 19:10", server="http://localhost:8000")
#
# l = list(LinkSet(Ref("Genesis 29:10")))[1]
# print(l._id)
#
# final = delete_link(str(l._id), server="http://localhost:8000")
