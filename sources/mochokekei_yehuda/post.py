import csv
import os
import re
import django
django.setup()
from sefaria.model import *
from sources.functions import post_index, post_text, post_link, add_term
from sefaria.utils.hebrew import encode_hebrew_numeral, gematria

server = 'http://localhost:8000'
server = 'https://new-shmuel.cauldron.sefaria.org'
title = 'Mechokekei Yehudah'
# def change_tag(segment, chap_num):
#     for tag in re.findall('data-order="([^\d]*?)"', segment):
#         segment = segment.replace(f'data-order="{tag}"', f'data-order="{gematria(tag)}"')
#     segment = re.sub(f'data-commentator="(?!{title})([^"]*)"', rf'data-commentator="{title}; \1"', segment)
#     return segment
# ibn_text = Version().load({'title': 'Ibn Ezra on Genesis', 'versionTitle': 'Piotrkow, 1907-1911'}).contents()
# ibn_text['text'] = [[[change_tag(s, c) for s in v] for v in chap] for c, chap in enumerate(ibn_text['chapter']['default'], 1)]
# # post_text('Ibn Ezra on Genesis', ibn_text, server=server)
#
# he_title = 'מחוקקי יהודה'
# chumashim = library.get_indexes_in_category('Torah')
# ibn_ezras = [f'Ibn Ezra on {c}' for c in chumashim]
# ibn_ezras = [x for x in ibn_ezras if x != 'Ibn Ezra on Exodus'] #+ ['Ibn Ezra HaKatzar on Exodus', 'Ibn Ezra on Exodus; Perush HaArokh']
# books = {'yahel': {'en': 'Yahel Ohr', 'he': 'יהל אור'}, 'karnei': {'en': 'Karnei Ohr', 'he': 'קרני אור'}}
links = []
# for book in books:
#     name = f'{title}; {books[book]["en"]}'
#     he_name = f'{he_title}; {books[book]["he"]}'
#     # add_term(name, he_name, server=server)
#     schema = {
#         'nodes': [
#             {
#                 'nodeType': "JaggedArrayNode",
#                 'depth': 1,
#                 'addressTypes': [
#                     "Integer"
#                 ],
#                 'sectionNames': [
#                     "Paragraph"
#                 ],
#                 'titles': [
#                     {
#                         'primary': True,
#                         'text': "Introduction",
#                         'lang': "en"
#                     },
#                     {
#                         'primary': True,
#                         'text': "הקדמה",
#                         'lang': "he"
#                     }
#                 ],
#                 'key': "Introduction"
#             },
#             {
#                 'nodeType': "JaggedArrayNode",
#                 'depth': 3,
#                 'addressTypes': [
#                     "Perek",
#                     "Integer", "Integer"
#                 ],
#                 'sectionNames': [
#                     "Chapter",
#                     "Comment", "Paragraph"
#                 ],
#                 'titles': [
#                     {
#                         'primary': True,
#                         'text': "Genesis",
#                         'lang': "en"
#                     },
#                     {
#                         'primary': True,
#                         'text': "בראשית",
#                         'lang': "he"
#                     }
#                 ],
#                 'key': "Genesis"
#             },
#             {
#                 'nodeType': "JaggedArrayNode",
#                 'depth': 3,
#                 'addressTypes': [
#                     "Perek",
#                     "Integer", "Integer"
#                 ],
#                 'sectionNames': [
#                     "Chapter",
#                     "Comment", "Paragraph"
#                 ],
#                 'titles': [
#                     {
#                         'primary': True,
#                         'text': "Exodus",
#                         'lang': "en"
#                     },
#                     {
#                         'primary': True,
#                         'text': "שמות",
#                         'lang': "he"
#                     }
#                 ],
#                 'key': "Exodus"
#             },
#             {
#                 'nodeType': "JaggedArrayNode",
#                 'depth': 3,
#                 'addressTypes': [
#                     "Integer",
#                     "Integer", "Integer"
#                 ],
#                 'sectionNames': [
#                     "Chapter",
#                     "Comment", "Paragraph"
#                 ],
#                 'titles': [
#                     {
#                         'primary': True,
#                         'text': "Leviticus",
#                         'lang': "en"
#                     },
#                     {
#                         'primary': True,
#                         'text': "ויקרא",
#                         'lang': "he"
#                     }
#                 ],
#                 'key': "Leviticus"
#             },
#             {
#                 'nodeType': "JaggedArrayNode",
#                 'depth': 3,
#                 'addressTypes': [
#                     "Integer",
#                     "Integer", "Integer"
#                 ],
#                 'sectionNames': [
#                     "Chapter",
#                     "Comment", "Paragraph"
#                 ],
#                 'titles': [
#                     {
#                         'primary': True,
#                         'text': "Numbers",
#                         'lang': "en"
#                     },
#                     {
#                         'primary': True,
#                         'text': "במדבר",
#                         'lang': "he"
#                     }
#                 ],
#                 'key': "Numbers"
#             },
#             {
#                 'nodeType': "JaggedArrayNode",
#                 'depth': 3,
#                 'addressTypes': [
#                     "Integer",
#                     "Integer", "Integer"
#                 ],
#                 'sectionNames': [
#                     "Chapter",
#                     "Comment", "Paragraph"
#                 ],
#                 'titles': [
#                     {
#                         'primary': True,
#                         'text': "Deuteronomy",
#                         'lang': "en"
#                     },
#                     {
#                         'primary': True,
#                         'text': "דברים",
#                         'lang': "he"
#                     }
#                 ],
#                 'key': "Deuteronomy"
#             }
#         ],
#         'nodeType': "SchemaNode",
#         'titles': [{
#             'text': he_name,
#             'lang': "he",
#             'primary': True
#             },
#             {
#             'text': name,
#             'lang': "en",
#             'primary': True
#             }],
#         'key': name
#     }
#     if book == 'karnei':
#         schema['nodes'].pop(0)
#     index = {
#         'title': name,
#         'categories': ["Tanakh", "Acharonim on Tanakh"],
#         'schema': schema,
#         'dependence': "commentary",
#         'base_text_titles': chumashim + ibn_ezras,
#         'collective_title': name,
#     }
#     # post_index(index, server=server)
#
#     text = []
#     with open(next(f for f in os.listdir() if f.startswith(books[book]["en"]))) as fp:
#         for row in csv.DictReader(fp):
#             if row['chapter']:
#                 text.append([])
#             row_text = row['text']
#             text[-1].append([row_text])
#     text_dict = {
#         'language': 'he',
#         'title': name,
#         'versionTitle': 'Piotrkow, 1907-1911',
#         'versionSource': 'https://www.nli.org.il/he/books/NNL_ALEPH990020973480205171/NLI'
#     }
#     if book == 'yahel':
#         text_dict['text'] = ['א']
#         # post_text(f'{name}, Introduction', text_dict, server=server)
#     text_dict['text'] = text
#     # post_text(f'{name}, Genesis', text_dict, server=server)
#
#     #links
#     for c, chapter in enumerate(text, 1):
#         for s, segment in enumerate(text[c-1], 1):
#             check_second = False
#             c_ = c if c != 27 or (book == 'karnei' and s != 25) or (book == 'yahel' and s < 124) else c+1
#             ibn = Ref(f'Ibn Ezra on Genesis {c_}')
#             ref = f'{name}, Genesis {c}:{s}:1'
#             for ibn_segment in ibn.all_segment_refs():
#                 ibn_text = ibn_segment.text('he', 'Piotrkow, 1907-1911').text
#                 letter = re.findall('^[\[\(]([א-ת]+)[\]\)]', Ref(ref).text('he').text)[0]
#                 if letter != ''.join(sorted(re.sub('[׳״]', '', encode_hebrew_numeral(s)))[::-1]):
#                     if c in [25, 47]:
#                         pass
#                     else:
#                         print(f'chapter {c} in {book}: segment {s} has letter {letter}')
#                 if f'data-commentator="{name}" data-order="{gematria(letter)}"' in ibn_text:
#                     if letter != ''.join(sorted(re.sub('[׳״]', '', encode_hebrew_numeral(s)))[::-1]):
#                         if c in [25, 47]:
#                             if (c == 25 and (book == 'yahel' and s < 89) or (book == 'karnei' and s < 29)) or c == 47:
#                                 check_second = not check_second
#                     if check_second:
#                         continue
#                     ibn_segment = ibn_segment.normal()
#                     break
#             if isinstance(ibn_segment, Ref):
#                 print(f'problem with finding {ref} in base text {ibn}', letter, s, check_second)
#                 continue
#             base_ref = ':'.join(' '.join(ibn_segment.split()[-2:]).split(':')[:-1])
#             get_link = lambda r: {
#                 'refs': [ref, r],
#                 'type': 'commentary',
#                 'auto': True,
#                 'generated_by': f'{title} linker',
#             }
#             # links += [get_link(base_ref), get_link(ibn_segment)]
#             # links[-1]['inline_reference'] = {'data-order': gematria(letter), 'data-commentator': name}

book = 'Yahel Ohr'
name = f'{title}; {book}'
yahel_seg = 1
for segment in Ref('Ibn Ezra on Genesis, Introduction').all_segment_refs():
    tc = segment.text('he', 'Piotrkow, 1907-1911')
    text = tc.text
    for i in re.findall('data-order="(\d*)"', text):
        links.append({
            'refs': [segment.normal(), f'{name}, Introduction {yahel_seg}'],
            'type': 'commentary',
            'auto': True,
            'generated_by': f'{title} linker',
            'inline_reference': {'data-order': yahel_seg, 'data-commentator': name, 'data-label': i}
        })
        tc.text = tc.text.replace(f'data-order="{i}">', f'data-order="{yahel_seg}" data-label="{i}">', 1)
        yahel_seg += 1
    tc.save()


post_link(links, server=server)
