from sources.functions import *

#
first_try = delete_link("5c17b8cbb071e100bf4e3b54", server="http://localhost:8000")
second_try = delete_link("Genesis 3000", server="http://localhost:8000")
third_try = delete_link("5c17b8cbb071e100bf4e3b5", server="http://localhost:8000")
fourth_try = delete_link("Genesis 30:5000", server="http://localhost:8000")
#
#
# l = list(LinkSet(Ref("Genesis 19:10")))[2]
# fifth_try = delete_link("Genesis 19:10", server="http://localhost:8000")

l = list(LinkSet(Ref("Genesis 29:10")))[1]
print(l._id)

final = delete_link(str(l._id), server="http://localhost:8000")
