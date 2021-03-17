from rif_utils import tags_map
from tags_fix_and_check import tags_by_criteria
for masechet in tags_map:
    if masechet in ['Nedarim']:continue
    a=tags_by_criteria(masechet,value=lambda x:x['used']==False)
    print(masechet,a)
    print('******',masechet,set(a[k]['referred text'] for k in a))
