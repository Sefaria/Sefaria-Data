#encoding=utf-8
from sefaria.model import *
from sources.functions import *
from sefaria.helper.schema import *
if __name__ == "__main__":
    title = "Malbim on Job"
    index = library.get_index(title)
    convert_simple_index_to_complex(index)
    VersionState(title).refresh()
    intro = JaggedArrayNode()
    intro.add_shared_term("Introduction")
    intro.add_structure(["Paragraph"])
    intro.key = "intro"
    parent_node = library.get_index(title).nodes
    insert_first_child(intro, parent_node)


    nodes = []
    with open("alt.txt") as f:
        for line in f:
            num = line.split(")")[0]
            he_title = line.replace("כלל", "")
            num = getGematria(num.replace("כלל", ""))
            ref = "Responsa Rosh {}.1.1".format(num)
            en_title = "Klal {}".format(num)
            node = ArrayMapNode()
            node.depth = 0
            node.add_primary_titles(en_title, he_title)
            node.wholeRef = ref
            node.refs = []
            nodes.append(node.serialize())

    index = get_index_api("Responsa Rosh", server="http://proto.sefaria.org")
    index['alt_structs'] = {"Index": {"nodes": nodes}}
    post_index(index, server="http://proto.sefaria.org")