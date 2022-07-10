import re
import django
django.setup()
from sefaria.model import *
from data_utilities.dibur_hamatchil_matcher import match_ref
from sources.functions import post_link, add_term

links = []
for page in Index().load({'title': 'Chiddushei HaRambam on Rosh Hashanah'}).all_section_refs():
    base = Ref(page.normal().replace('Chiddushei HaRambam on ', '')).text('he', vtitle='Wikisource Talmud Bavli')
    comments = page.text('he')
    base_tokenizer = lambda x: x.split()
    dh_extract_method = lambda x: re.sub('<.*?>', '', ' '.join(x.split('</b>')[0].split()[:7]))
    matches = match_ref(base, comments, base_tokenizer, dh_extract_method=dh_extract_method)
    for baseref, commentref in zip(matches['matches'], page.all_segment_refs()):
        if baseref:
            links.append({'refs': [baseref.normal(), commentref.normal()],
                          'type': 'commentary',
                          'auto': True,
                          'generated_by': 'rambam rosh hashanah linker'})
post_link(links, server='http://localhost:9000', skip_lang_check=False)

add_term('Chiddushei HaRambam', 'חידושי הרמב"ם', server='https://pele.cauldron.sefaria.org')
