import csv
import django
import time
from functools import reduce
django.setup()
from sefaria.model import *
from sefaria.utils.talmud import section_to_daf
from sefaria.system.exceptions import InputError
from sefaria.helper.schema import convert_simple_index_to_complex, attach_branch, cascade


def relocate_one(orig, dest, delete_links=True):
    #move the text with all links to new destination
    #delete all text and links in desitnation!
    print(f'moves {orig} to {dest}')
    rorig = Ref(orig)
    if not rorig.version_list():
        print('no text in origin')
        return
    if rorig.is_segment_level():
        empty = ''
    else:
        ver = rorig.version_list()[0]
        depth = rorig.text(ver['language'], ver['versionTitle']).ja().depth()
        empty = reduce(lambda x, y: [x], [[] for _ in range(depth)])
    rdest = Ref(dest)
    for v in rdest.version_list():
        t = rdest.text(v['language'], v['versionTitle'])
        t.text = empty
        t.save()
    if delete_links:
        rdest.linkset().delete()
    cascade(orig, lambda x: dest if x == orig else x)
    for v in rorig.version_list():
        new_text = rdest.text(v['language'], v['versionTitle'])
        old_text = rorig.text(v['language'], v['versionTitle'])
        new_text.text = old_text.text
        new_text.save()
        old_text.text = empty
        old_text.save()

def step_ref(ref, step):
    if type(ref) == str:
        ref = Ref(ref)
    book = ref.book
    sections = ref.sections[:]
    sections[-1] += step
    for i, sec in enumerate(sections):
        sections[i] = section_to_daf(sections[i]) if ref.index_node.addressTypes[i] == 'Talmud' else str(sections[i])
    return f'{book} {":".join(sections)}'

def parent_ref(ref):
    if type(ref) == str:
        ref = Ref(ref)
    book, sections = ref.book, ref.sections[:]
    for i, sec in enumerate(sections):
        sections[i] = section_to_daf(sections[i]) if ref.index_node.addressTypes[i] == 'Talmud' else str(sections[i])
    return Ref(f'{book} {":".join(sections[:-1])}').normal()

def last_ref_in_same_level(ref):
    if type(ref) == str:
        ref = Ref(ref)
    book, sections = ref.book, ref.sections[:]
    sections[-1] = len(Ref(parent_ref(ref)).all_subrefs())
    for i, sec in enumerate(sections):
        sections[i] = section_to_daf(sections[i]) if ref.index_node.addressTypes[i] == 'Talmud' else str(sections[i])
    return f'{book} {":".join(sections)}'

def indent_refs(step, tref_start, tref_end=None, delete_links=True):
    #move the text with all links to new destination
    #delete all what exists in the new desitnation!
    #:param: tref_start the tref to start the move.
    #:param: tref_end the tref to end the move. if None, until the end of the section
    #:param: step - int. steps to move (>0 for foreward and <0 to previous)
    if not tref_end:
        tref_end = last_ref_in_same_level(tref_start)
    units_num = Ref(tref_end).sections[-1] - Ref(tref_start).sections[-1] + 1

    assert len(Ref(tref_start).sections) == len(Ref(tref_end).sections)
    assert units_num > 0
    assert Ref(tref_start).sections[0] + step > 0


    if step > 0:
        curr = tref_end
        substep = -1
    else:
        curr = tref_start
        substep = 1

    for _ in range(units_num):
        relocate_one(curr, step_ref(curr, step), delete_links=delete_links)
        curr = step_ref(curr, substep)

def split_ref(ref, indexes):
    #split segment or section
    #:param: ref - the ref that should be devided
    #:param: indexes - the indexes for devision. in segment, it's the index of the words in string (which says that if there're different versions it can be problemaatic)
    #e.g split_ref('Genesis 1', [3, 7]) will make Genesis 1:1-3 to be Genesis 1, Genesis 1:4-7 to be Genesis 2,
    #Genesis 1:8-end to be Genesis 3, Genesis 2 to be Geness 4, etc.
    #can't split Daf addressType. it seems the only current case is splitting Zohar parts (it can split accross page of talmud or zohar)

    next_ref = step_ref(ref, 1)
    indent_refs(len(indexes), next_ref)

    parent = parent_ref(ref)
    ref = Ref(ref)
    ref.index.versionState().refresh()
    main_sec = ref.sections[-1]
    is_daf = ref.index_node.addressTypes[len(ref.sections)-1] == 'Talmud'
    if ref.is_segment_level():
        indexes = [0] + indexes + [None]
        for v in ref.version_list():
            text = ref.text(v['language'], v['versionTitle']).text.split()
            texts = []
            for inds in zip(indexes, indexes[1:]):
                texts.append(' '.join(text[slice(*inds)]))
            for seg in range(len(texts)):
                text_chunck = Ref(f'{parent}:{main_sec+seg}').text(v['language'], v['versionTitle'])
                text_chunck.text = texts.pop(0)
                text_chunck.save()
    else:
        indexes += [len(ref.all_subrefs())]
        for sec, inds in enumerate(zip(indexes, indexes[1:]), 1):
             for seg in range(inds[1]-inds[0]):
                 new_sec = main_sec + sec
                 if is_daf:
                     new_sec = section_to_daf(new_sec)
                 orig = f'{ref}:{inds[0]+seg+1}'
                 dest = f'{parent}:{new_sec}:{seg+1}'
                 relocate_one(orig, dest)


if __name__ == '__main__':
    name = 'Pele Yoetz'
    ind = Index().load({'title': name})

    indent_refs(-18, f'{name} 307', f'{name} 403')
    ind.versionState().refresh()

    #new issues - move and cascade
    news = [(244, 'נדה'), (276, 'עזות'), (287, 'עדות'), (324, 'ציבור'), (367, 'שכן'), (375, 'שופטים ושוטרים'), (399, 'תוספת')]
    news.reverse()
    for siman, issue in news:
        if siman > 300:
            siman -= 18
        r = Ref(f'{name} {siman}')
        t = r.text('he', 'Torat Emet')
        for s, seg in enumerate(t.text, 1):
            indexes = []
            if issue in seg:
                if seg.strip().endswith(issue):
                    print(siman, issue, s)
                    indexes = [s]
                    add_head = True
                    t.text[s-1] = t.text[s-1].replace(issue, '').strip()
                    t.save(force_save=True)
                else:
                    indexes = [s-1]
                    add_head = False
                break
        split_ref(f'{name} {siman}', indexes)
        ind.versionState().refresh()
        if add_head:
            text_chunk = Ref(f'{name} {siman+1}:1').text('he', 'Torat Emet')
            text_chunk.text = f'{issue} - {text_chunk.text}'
            text_chunk.save()

    # #migrate to complex and add intro node and supplement node and migrate text to it
    convert_simple_index_to_complex(ind)
    time.sleep(30)
    ind = Index().load({'title': name})
    parent = ind.nodes
    node = JaggedArrayNode()
    node.add_primary_titles('Introduction', 'הקדמה')
    node.add_structure(['Paragraph'])
    node.serialize()
    attach_branch(node, parent)
    node = JaggedArrayNode()
    node.add_primary_titles('Supplement', 'נספח')
    node.add_structure(['Paragraph'])
    node.serialize()

    attach_branch(node, parent, len(parent.children))
    r = Ref(f'{name} 392')
    for v in r.version_list():
        old = r.text(v['language'], v['versionTitle'])
        new = Ref(f'{name}, Supplement').text(v['language'], v['versionTitle'])
        new.text = old.text
        new.save()
        old.text = []
        old.save()

    en_letters = ['Letter Alef',
                'Letter Bet',
                'Letter Gimel',
                'Letter Dalet',
                'Letter He',
                'Letter Vav',
                'Letter Zayin',
                'Letter Chet',
                'Letter Tet',
                'Letter Yod',
                'Letter Kaf',
                'Letter Lamed',
                'Letter Mem',
                'Letter Nun',
                'Letter Samekh',
                'Letter Ayin',
                'Letter Peh',
                'Letter Tzadi',
                'Letter Kof',
                'Letter Resh',
                'Letter Shin',
                'Letter Tav']

    #attach alts
    with open('pele.csv', encoding='utf-8', newline='') as fp:
        data = list(csv.DictReader(fp))
    alts = [{'nodeType': "ArrayMapNode",
                    'depth': 0,
                    'wholeRef': f"{name}, Introduction",
                   'titles': [{'text': 'Introduction',
                        'lang': "en",
                        'primary': True},
                              {'text': 'הקדמה',
                               'lang': "he",
                               'primary': True}
                              ]}]
    for i, row in enumerate(data, 1):
        if row['letter']:
            try: #end node
                letter['wholeRef'] += f'{i-1}'
                alts.append(letter)
            except NameError:
                pass
            letter = {'nodeType': "ArrayMapNode",
                    'depth': 0,
                    'nodes': [],
                    'wholeRef': f"{name} {i}-",
                   'titles': [{'text': en_letters.pop(0),
                           'lang': "en",
                           'primary': True},
                            {'text': row['letter'],
                            'lang': "he",
                            'primary': True}
                          ]}
        letter['nodes'].append({'nodeType': "ArrayMapNode",
                    'depth': 0,
                    'wholeRef': f"{name} {i}",
                    'titles': [{'text': f'{i}',
                        'lang': "en",
                        'primary': True},
                       {'text': row['issue'],
                        'lang': "he",
                        'primary': True}
                       ]})
    letter['wholeRef'] += f'{i - 1}'
    alts.append(letter)
    alts.append({'nodeType': "ArrayMapNode",
                    'depth': 0,
                    'wholeRef': f"{name} 393",
                    'titles': [{'text': 'נספח',
                        'lang': "he",
                        'primary': True},
                       {'text': 'Supplement',
                        'lang': "en",
                        'primary': True}]})
    ind = Index().load({'title': name})
    ind.alt_structs = {'Topic': {'nodes': alts}}
    ind.default_struct = 'Topic'
    ind.save()
