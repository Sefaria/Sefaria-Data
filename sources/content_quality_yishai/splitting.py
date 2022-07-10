import django
django.setup()
from pele_yoetz import split_ref
import traceback

for ref, inds in [('Rashi on Genesis 14', [4, 12]),('Berakhot 40a:1', [3, 5]),('Chidushei Halachot on Taanit 3a', [2]),('Zohar 1 50b', [1]),('Rashi on Berakhot 2a:1:1', [4, 10]),('Tosefta Berakhot (Lieberman) 1', [4, 7])]:
    print(ref,inds)
    try:
        split_ref(ref, inds)
    except:
        print(traceback.format_exc())
