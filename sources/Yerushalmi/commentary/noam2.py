import django
django.setup()
from sefaria.model import *
import re
from linking_utilities.dibur_hamatchil_matcher import match_ref
import csv

def dh_extract_method(comment):
    dh = comment.split('.')[0]
    dh = re.sub('\([^)]*\)', '', dh)
    dh = re.sub('<b>(?:שם|עוד|ירושלמי|מתניתין|דף)[^>]*</b>', '', dh)
    dh = re.sub('</?b>', '', dh).strip()
    dh = re.sub('^שם', '', dh).strip()
    dh = re.sub('^בירושלמי', '', dh).strip()
    dh = re.sub("^בירו'", '', dh).strip()
    dh = re.sub('^מתניתין', '', dh).strip()
    dh = re.sub("^מתני'", '', dh).strip()
    dh = re.sub('^בירושלמי', '', dh).strip()
    return ' '.join(dh.split()[:7])

def match(base_ref, text):
    for vtitle in ['Venice Edition', 'Mechon-Mamre', 'The Jerusalem Talmud, edition by Heinrich W. Guggenheimer. Berlin, De Gruyter, 1999-2015']:
        match = match_ref(Ref(base_ref).text('he', vtitle), [text], lambda x: re.sub('[^\'" א-ת]', '', x).split(),
                            dh_extract_method=dh_extract_method)['matches'][0]
        if match:
            return match.normal()

if __name__ == '__main__':
    with open('Noam Yerushalm2.csv') as fp:
        r = csv.DictReader(fp)
        fieldnames = r.fieldnames
        rows = list(r)
    for row in rows:
        if row['base text ref'].endswith(':1'):
            base_ref = ':'.join(row['base text ref'].split(':')[:-1])
            for word in ["ובגמ'", "כו'", '.']:
                text = row['text'].split(word, 1)[-1]
                result = match(base_ref, text)
                if result and not result.endswith(':1'):
                    row['new'] = result
                    break

    with open('Noam Yerushalmi with links.csv', 'w') as fp:
        w = csv.DictWriter(fp, fieldnames=fieldnames+['new'])
        w.writeheader()
        for row in rows:
            w.writerow(row)
