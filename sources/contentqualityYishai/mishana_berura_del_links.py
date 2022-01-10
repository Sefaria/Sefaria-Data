import django
django.setup()
from sefaria.model import *

index = library.get_index('Mishnah Berurah')
for ref in Ref('Mishnah Berurah 497-523').all_segment_refs():
    if any(str(siman) in ref.tref for siman in [504,507,511,522]):
        continue
    links = ref.linkset()
    links = [l for l in links if l.generated_by == 'dibur_hamatchil_matcher.py']
    if len(links) > 1:
        for l in links:
            for r in l.refs:
                if r.startswith('Shulchan Arukh, Orach Chayim') and r.endswith(':1'):
                    l.delete()
                    break
