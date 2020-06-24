import re
import django
django.setup()
from functools import partial
from sefaria.model import *
from rif_utils import segmented_rif_files, remove_metadata
from data_utilities.dibur_hamatchil_matcher import match_ref

def base_tokenizer(string):
    return re.sub(r'<.*?>', '', string).split()

for en_masechet, heb_masechet, file in segmented_rif_files:
    data = file.read()
    data = re.split(r'@20.*?\n', data)
    data.pop(0)
    gemara_text = Ref(heb_masechet + ' ב.').text('he')

    for page in data:
        page = page.split('\n')
        for section in page:
            print(remove_metadata(section, en_masechet))
            d = match_ref(gemara_text, [section], base_tokenizer, dh_extract_method=partial(remove_metadata, masechet=en_masechet))
            print(d, type(d))
            break
        break
    break
