# encoding=utf-8

from __future__ import print_function
import argparse
import unicodecsv
from extract_midreshet_sheets import MidreshetCursor, get_ref_for_resource_p, bleach_clean

import django
django.setup()
from sefaria.model import *

parser = argparse.ArgumentParser()
parser.add_argument("filename", help="file to parse refs from")
cmd_args = parser.parse_args()
input_filename = cmd_args.filename
print(input_filename)

with open(input_filename, 'r') as fp:
    entries = list(unicodecsv.DictReader(fp))

valid_refs = [entry for entry in entries if Ref.is_ref(entry['New Ref'])]
valid_ref_ids = set([entry['id'] for entry in valid_refs])
bad_refs = [entry for entry in entries if entry['id'] not in valid_ref_ids]
print("Num bad refs:", len(bad_refs))

cursor = MidreshetCursor()
for my_ref in valid_refs:
    cursor.execute('SELECT body FROM Resources WHERE id=?', (my_ref['id'],))
    result = cursor.fetchone().body

    sefaria_ref = get_ref_for_resource_p(my_ref['id'], my_ref['New Ref'], bleach_clean(result), replace=True)
    print(my_ref['New Ref'], sefaria_ref, sep='\n')
    cursor.execute('UPDATE RefMap SET SefariaRef = ? WHERE id = ?', (sefaria_ref, my_ref['id']))
    cursor.commit()

with open('interesting_unparsed_refs.csv') as fp:
    interesting_rows = [row for row in unicodecsv.DictReader(fp) if row['id'] not in valid_ref_ids]

with open('interesting_unparsed_refs.csv', 'w') as fp:
    writer = unicodecsv.DictWriter(fp, fieldnames=['id', 'Original Ref'])
    writer.writeheader()
    writer.writerows(interesting_rows)

