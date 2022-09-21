import re
import django
django.setup()
from sefaria.model import *

aug = [{'hw': x.headword, 'sn': x.strong_number} for x in LexiconEntrySet({'parent_lexicon': 'BDB Augmented Strong'})]
new = [{'hw': x.headword, 'sn': x.strong_numbers, 'pl': x.parent_lexicon} for x in LexiconEntrySet({'parent_lexicon': {'$regex': 'BDB.*?Dict'}})]
for wf in WordFormSet({'lookups': {'$elemMatch': {'parent_lexicon': 'BDB Augmented Strong'}}}):
    new_looks = []
    for look in wf.lookups:
        if look['parent_lexicon'] != 'BDB Augmented Strong':
            continue
        hw = look['headword']
        hw = re.sub('[I\d⁰¹²³⁴⁵⁶⁷⁸⁹]', '', hw)
        aug_les = [x for x in aug if x['hw'] == hw]
        if len(aug_les) == 0:
            print(11111, hw)
            continue
        strongs = []
        for aug_le in aug_les:
            strongs.append(aug_le['sn'])
        if not strongs:
            print(2222, hw)
        new_les = [x for x in new if any(num in x['sn'] for num in strongs)]
        if len(new_les) == 0:
            new_les = [x for x in new if re.search(f'^{hw}[⁰¹²³⁴⁵⁶⁷⁸⁹]?', x['hw'])]
            if len(new_les) == 0:
                print(33333, hw, strongs)
                continue
        new_looks += [{'parent_lexicon': le['pl'], 'headword': le['hw']} for le in new_les]
    wf.lookups += new_looks
    wf.save()
