import django
django.setup()
from sefaria.model import *
from sources.functions import post_link

bachur = 'Animadversions by Elias Levita on Sefer HaShorashim'
shorashim = 'Sefer HaShorashim'
entries = LexiconEntrySet({'parent_lexicon': bachur})
links = []
for entry in entries:
    try:
        sref = Ref(f'{shorashim}, {entry.headword}')
    except:
        continue
    links.append({'type': 'commentary',
                  'refs': [f'{sref.normal()}:1', f"{Ref(f'{bachur}, {entry.headword}').normal()}:1"],
                  'auto': True,
                  'generated_by': 'shorashim-bachur linker'})
    entry.refs.append(sref.normal())
    entry.save()
    sentry = LexiconEntry().load({'parent_lexicon': shorashim, 'headword': entry.headword})
    sentry.save()
post_link(links, server='http://localhost:9000', skip_lang_check=False, VERBOSE=False)
