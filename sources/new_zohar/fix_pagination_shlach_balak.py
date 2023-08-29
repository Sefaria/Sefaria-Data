import re
import django
django.setup()
from sefaria.model import *
from sefaria.utils.talmud import section_to_daf, daf_to_section

def minus_one(section):
    return section_to_daf(daf_to_section(section) - 1)

for parasha in ["Sh'lach.46.324-46.348", 'Korach', 'Chukat', 'Balak 1:1-20:271']:
    for vt in ['Vocalized Zohar, Israel 2013', 'Sulam Edition, Jerusalem 1945']:
        for segment in Ref(f'Zohar, {parasha}').all_segment_refs():
            tc = segment.text('he', vtitle=vt)
            text = tc.text
            parts = re.split('(\d{3}[ab])', text)
            for i in range(1, len(parts), 2):
                parts[i] = minus_one(parts[i])
            text = ''.join(parts)
            tc.text = text
            tc.save()
        tc = Ref('Zohar, Balak 21:279').text('he', vtitle=vt)
        tc.text = tc.text.replace('''(דף ר' ע"א) ''', '<i data-overlay="Vilna Pages" data-value="200a"></i>')
        tc.save()

index = library.get_index('Zohar')
alts = index.get_alt_structure('Daf')
for i in range(14, 18):
    node = alts.children[2].children[i]
    if i == 14:
        node.children[0].addresses = node.children[0].addresses[:-2] + [350, 351]
        delattr(node.children[2], 'skipped_addresses')
    else:
        try:
            node.startingAddress = minus_one(node.startingAddress)
        except:
            for j in range(len(node.children)):
                node.children[j].startingAddress = minus_one(node.children[j].startingAddress)
        if i == 17:
            node.refs = node.refs[:30] + ['Zohar, Balak 20:271-21:279', 'Zohar, Balak 21:279-23:288'] + node.refs[31:]

node = alts.children[2].children[5].children[0]
node.refs = ['Zohar, Achrei Mot 1:1-44', 'Zohar, Achrei Mot 1:4-2:12'] + node.refs[1:]
node.startingAddress = '55b'

node = alts.children[2].children[6].children[1]
node.skipped_addresses.pop(-1)

node = alts.children[2].children[7].children[1]
node.skipped_addresses.pop(0)

node = alts.children[2].children[13].children[1]
node.refs = ["Zohar, Beha'alotcha 13:72-14:77", "Zohar, Beha'alotcha 14:77-15:87", "Zohar, Beha'alotcha 15:87-16:94"]
node.startingAddress = '152b'

node = alts.children[2].children[18].children[0]
node.skipped_addresses = [x for x in node.skipped_addresses if x not in [447, 461, 463]]
node.refs = node.refs[:27] + ['Zohar, Pinchas 57:348-350', 'Zohar, Pinchas 57:350-357'] + node.refs[28:]

node = alts.children[2].children[18].children[1]
node.skipped_addresses = [x for x in node.skipped_addresses if x not in [462, 466]]
node.refs = node.refs[:27] + ['Zohar, Pinchas 69:402'] + node.refs[27:]

node = alts.children[2].children[-3]
node.addresses[4] = 592

index.set_alt_structure('Daf', alts)
index.save()
