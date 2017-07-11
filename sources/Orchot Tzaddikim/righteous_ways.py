# -*- coding: utf-8 -*-

__author__ = 'stevenkaplan'

from sources.functions import *
from sefaria.model import *
from data_utilities.XML_to_JaggedArray import XML_to_JaggedArray
from sefaria.helper.schema import *
import bleach
from sefaria.utils.hebrew import *

SERVER = "http://proto.sefaria.org"


def reorder_modify(text):
    return bleach.clean(text, strip=True)

def get_he_gates():
    he_gates = []
    for num in range(28):
        if num == 0:
            he_gates.append(u"""שער הראשון - שער הגאווה""")
        else:
            he_gate = TextChunk(Ref("Orchot Tzadikim.{}".format(num+1)), lang='he').text[0]
            he_gate = bleach.clean(he_gate, strip=True, tags=[""])
            he_gates.append(he_gate)
    return he_gates

def set_alt_structs():
    he_gates = get_he_gates()
    gates = ['Chapter One: ON PRIDE', 'Chapter Two: ON MODESTY', 'Chapter Three: ON SHAME', 'Chapter Four: ON IMPUDENCE', 'Chapter Five: ON LOVE', 'Chapter Six: ON HATRED', 'Chapter Seven: ON MERCY', 'Chapter Eight: ON CRUELTY', 'Chapter Nine: ON JOY', 'Chapter Ten: ON WORRY', 'Chapter Eleven: ON REMORSE', 'Chapter Twelve: ON ANGER', 'Chapter Thirteen: ON GRACIOUSNESS', 'Chapter Fourteen: ON ENVY', 'Chapter Fifteen: ON ZEAL', 'Chapter Sixteen: ON LAZINESS', 'Chapter Seventeen: ON GENEROSITY', 'Chapter Eighteen: ON MISERLINESS', 'Chapter Nineteen: ON REMEMBERING', 'Chapter Twenty: ON FORGETFULNESS', 'Chapter Twenty One: ON SILENCE', 'Chapter Twenty Two: ON FALSEHOOD', 'Chapter Twenty Three: ON TRUTH', 'Chapter Twenty Four: ON FLATTERY', 'Chapter Twenty Five: ON GOSSIP', 'Chapter Twenty Six: ON REPENTANCE', 'Chapter Twenty Seven: ON TORAH', 'Chapter Twenty Eight: FEAR OF HEAVEN']
    nodes = []
    for count, gate in enumerate(gates):
        node = ArrayMapNode()
        node.add_primary_titles(gate, he_gates[count])
        node.depth = 0
        node.wholeRef = "Orchot Tzadikim.{}".format(count+1)
        node.refs = []
        nodes.append(node.serialize())

    index = get_index_api("Orchot Tzadikim", server="http://proto.sefaria.org")
    index['alt_structs'] = {"Gate": {"nodes": nodes}}
    post_index(index, server="http://proto.sefaria.org")

if __name__ == "__main__":
    set_alt_structs()
    post_info = {}
    post_info["language"] = "en"
    post_info["server"] = SERVER
    allowed_tags = ["book", "intro", "part", "chapter", "p", "ftnote", "title", "ol", "footnotes", "appendix"]
    allowed_attributes = ["id"]
    p = re.compile("\d+a?\.")

    post_info["versionTitle"] = "Orchot Tzaddikim, trans. Seymour J. Cohen, Ktav Pub House, 1982"
    post_info["versionSource"] = "http://www.worldcat.org/oclc/10084520"
    title = "Orchot Tzadikim"
    file_name = "The-Ways-of-the-Righteous_Cohen.xml"


    array_of_names = [str(x+1) for x in range(28)]
    array_of_names.insert(0, "Introduction")
    parser = XML_to_JaggedArray(title, file_name, allowed_tags, allowed_attributes, post_info, change_name=True,
                                titled=True, array_of_names=array_of_names)
    parser.set_funcs(reorder_test=lambda x: x.tag == "title" and x.text.find("<bold>") == 0, reorder_modify=reorder_modify)
    parser.run()