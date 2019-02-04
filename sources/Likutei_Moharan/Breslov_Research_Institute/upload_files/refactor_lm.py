# encoding=utf-8

import django
django.setup()
from sefaria.model import *
from sefaria.helper.schema import refresh_version_state, handle_dependant_indices


def resize_node(ja_node, section_names):
    assert isinstance(ja_node, JaggedArrayNode)

    if hasattr(ja_node, 'lengths'):
        print 'WARNING: This node has predefined lengths!'
        return

    delta = len(section_names) - len(ja_node.sectionNames)
    assert delta >= 1
    address_types = ['Integer'] * len(section_names)
    ja_node.toc_zoom = 2
    ja_node.sectionNames = section_names
    ja_node.addressTypes = address_types
    ja_node.depth = len(section_names)
    ja_node._regexes = {}
    ja_node._init_address_classes()
    index = ja_node.index
    index.save(override_dependencies=True)
    print 'Index Saved'
    library.refresh_index_record_in_cache(index)
    # ensure the index on the ja_node object is updated with the library refresh
    ja_node.index = library.get_index(ja_node.index.title)

    vs = [v for v in index.versionSet()]
    print 'Updating Versions'
    for v in vs:
        assert isinstance(v, Version)
        if v.get_index() == index:
            chunk = TextChunk(ja_node.ref(), lang=v.language, vtitle=v.versionTitle)
        else:
            library.refresh_index_record_in_cache(v.get_index())
            ref_name = ja_node.ref().normal()
            ref_name = ref_name.replace(index.title, v.get_index().title)
            chunk = TextChunk(Ref(ref_name), lang=v.language, vtitle=v.versionTitle)
        ja = chunk.ja()
        if ja.get_depth() == 0:
            continue

        chunk.text = ja.resize(delta).array()
        chunk.save()

    library.rebuild()
    refresh_version_state(index.title)

    handle_dependant_indices(index.title)



my_node = Ref("Likutei Moharan").default_child_ref().index_node
print my_node.sectionNames
if len(my_node.sectionNames) == 2:
    resize_node(my_node, [u'Torah', u'Section', u'Comment'])
my_node = Ref("Likutei Moharan, Part II").index_node
print my_node.sectionNames
if len(my_node.sectionNames) == 2:
    resize_node(my_node, [u'Torah', u'Section', u'Comment'])
