__author__ = 'stevenkaplan'
from sefaria.model import *
from BeautifulSoup import *
from sources.functions import *
if __name__ == "__main__":
    contents = BeautifulSoup(open("alt_struct.xml")).contents[2].contents[3]
    nodes = []
    contents = filter(lambda x: type(x) is not NavigableString, contents)
    for count, each in enumerate(contents):
        en, he = each.attrs[0][1].split(" / ")
        node = ArrayMapNode()
        node.add_primary_titles(en, he)
        node.depth = 0
        if count == 0:
            node.wholeRef = "Messilat Yesharim, Introduction"
        else:
            node.wholeRef = "Messilat Yesharim {}".format(count)
        node.refs = []
        nodes.append(node.serialize())



    index = get_index_api("Messilat Yesharim", server="http://www.sefaria.org")
    index['alt_structs'] = {"Subject": {"nodes": nodes}}
    post_index(index, server="https://www.sefaria.org")


lines = """חוש העין / The Sense of Sight
מדת הגאוה / The Quality of Pride
מדת השפלות / The Quality of Meekness
מדת הבושת / The Quality of Pudency
מדת העזות / The Quality of Impudence
חוש השמע / The Sense of Hearing
מדת האהבה / The Quality of Love
מדת השנאה / The Quality of Hate
מדת הרחמים / The Quality of Mercy
מדת האכזריות / The Quality of Hardheartedness
חוש הטעם / The Sense of Taste
מדת השמחה / The Quality of Joy
מדת הדאגה / The Quality of Sorrow
מדת הבטחון / The Quality of Tranquility
מדת החרטה / The Quality of Penitence
חוש הריח / The Sense of Smell
מדת הכעס / The Quality of Anger
מדת הרצון / The Quality of Goodwill
מדת הקנאה / The Quality of Jealousy
מדת החריצות / The Quality of Diligence
חוש המישוש / The Sense of Touch
מדת הנדיבות / The Quality of Generosity 
מדת הקמצנות / The Quality of Greed
מדת הגבורה / The Quality of Valor
מדת המורך / The Quality of Cowardice """


nodes = []
current_schema_node = None
part = 0
for line in lines.splitlines():
    if not line.startswith("  "):
        if current_schema_node:
            nodes.append(current_schema_node.serialize())
        current_schema_node = SchemaNode()
        en, he = line.strip().split(" / ")
        current_schema_node.add_primary_titles(en, he)
        ch = 0
        part += 1
    else:
        ch += 1
        en, he = line.split(" / ")
        node = ArrayMapNode()
        node.add_primary_titles(en, he)
        node.depth = 0
        node.wholeRef = "The Improvement of the Moral Qualities, {}:{}".format(part, ch)
        node.refs = []
        current_schema_node.append(node)

index = get_index_api("The Improvement of the Moral Qualities", server="http://proto.sefaria.org")
index['alt_structs'] = {"Chapter": {"nodes": nodes}}
post_index(index, server="http://proto.sefaria.org")


