# encoding=utf-8

import re
import bleach
import codecs
import django
django.setup()
from sefaria.model import *


def assemble_text():
    def traverse(text_list):
        for t in text_list:
            if isinstance(t, basestring):
                yield t
            else:
                for sub_t in traverse(t):
                    yield sub_t

    otzar = library.get_index("Otzar Midrashim")
    all_text = [j.ref().text(lang='he').text for j in otzar.nodes.get_leaf_nodes()]
    return [i for i in traverse(all_text)]


def assemble_regex():
    def get_title_list(node, store=None):
        if store is None:
            store = []
        title = node.get_primary_title('he')
        if title == u'' or title == u'הקדמה':
            pass
        else:
            store.append(title)
        for child in node.children:
            get_title_list(child, store)
        return store
    otzar = library.get_index("Otzar Midrashim")
    title_list = sorted([re.escape(t) for t in get_title_list(otzar.nodes)], key=lambda x: len(x), reverse=True)
    return re.compile(u'|'.join(title_list))


def find_references(jnode, full_title_regex, local_title_regex):
    assert isinstance(jnode, JaggedArrayNode)
    segments = jnode.ref().all_segment_refs()
    store = {'refs': [], 'texts': []}
    for segment in segments:
        s_text = segment.text(lang='he').text
        if full_title_regex.search(s_text) and not local_title_regex.search(s_text):
            s_text = re.sub(full_title_regex, u'|\g<0>|', s_text)
            store['refs'].append(segment)
            store['texts'].append(s_text)
    return store


def walk_through_tree(node, full_regex, text_storage=None, title_store=None):
    if title_store is None:
        title_store = []
    if text_storage is None:
        text_storage = {'refs': [], 'texts': []}
    title_store.append(node.get_primary_title('he'))

    if isinstance(node, JaggedArrayNode):
        local_regex = re.compile(u'|'.join([re.escape(t) for t in title_store]))
        interesting = find_references(node, full_regex, local_regex)
        text_storage['refs'].extend(interesting['refs'])
        text_storage['texts'].extend(interesting['texts'])

    else:
        for child in node.children:
            walk_through_tree(child, full_regex, text_storage, title_store)
    title_store.pop()
    return text_storage


# my_text = assemble_text()
my_regex = assemble_regex()
otzar = library.get_index("Otzar Midrashim")
cool_texts = walk_through_tree(otzar.nodes, my_regex)
with codecs.open('otzar_test.txt', 'w', 'utf-8') as fp:
    for seg_ref, seg_text in zip(cool_texts['refs'], cool_texts['texts']):
        fp.write(u'{}\n'.format(seg_ref.normal()))
        fp.write(u'https://www.sefaria.org/{}\n'.format(seg_ref.url()))
        fp.write(u'{}\n\n'.format(bleach.clean(seg_text, strip=True, tags=[])))


