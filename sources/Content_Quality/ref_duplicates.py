import django
django.setup()
from sefaria.model import *
refs = {}
from tqdm import tqdm
# words = set()
# for b in tqdm(IndexSet()):
#     try:
#         for w in b.title.split():
#             if w[0].islower():
#                 words.add(w)
#     except:
#         print(b)
# print(words)
print(Ref("Shir Hashirim 3").normal())
print(Ref("Song of Songs 3").normal())
print(Ref("Song Of Songs 3").normal())
print(Ref("Bereshit Rabbah 3").normal())
print(Ref("Bereshit rabbah 3").normal())