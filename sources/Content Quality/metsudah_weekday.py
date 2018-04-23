#encoding=utf-8


from sefaria.helper.schema import *
from sefaria.model import *

def add_JAs_to_schema_from_text(schemaNode, str, title_group_separator=u", ", en_he_separator=" / ", structure=["Paragraph"]):
    """
    Create new JaggedArrays from str and add them to node
    :param schemaNode: must be SchemaNode, for example SchemaNode("Mincha")
    :param str: for example, str = u"Ashrei / אשרי, Shemoneh Esrei / שמונה עשרה, Tachanun / תחנון, Aleinu / עלינו"
    :param title_group_separator: used to split up titles in str so that tha above will yield four distinct title groups
    :param en_he_separator: used to split up each title group into english and hebrew
    :param structure: structure of JAs
    :return:
    """
    assert isinstance(schemaNode, SchemaNode)
    titles = str.split(title_group_separator)
    for title in titles:
        en_title, he_title = title.split(en_he_separator)
        ja = JaggedArrayNode()
        ja.add_primary_titles(en_title, he_title)
        ja.add_structure(structure)
        schemaNode.append(ja)
    if schemaNode.index:
        schemaNode.index.save()

VersionState("Weekday Siddur Sefard Linear")
book = library.get_index("Siddur Sefard Linear")
nodes = book.nodes.children
mincha = [node for node in nodes if node.primary_title('en') == "Mincha"][0]
maariv = [node for node in nodes if node.primary_title('en') == "Maariv"][0]
selichot = SchemaNode()
selichot.add_primary_titles("Selichos", u"סליחות")
#convert_jagged_array_to_schema_with_default(mincha)
#convert_jagged_array_to_schema_with_default(maariv)
library.rebuild() #rebuild index mapping after conversion

add_to_mincha = u"Ashrei / אשרי, Shemoneh Esrei / שמונה עשרה, Tachanun / תחנון, Aleinu / עלינו"
add_to_maariv = u"Berachos Preceding Shema / ברכות לפני שמע, Shema / שמע, Berachos Following Shema / ברכות אחרי שמע, Shemoneh Esrei / שמונה עשרה, Motzei Shabbos Prayers / למוצאי שבת, Aleinu / עלינו"
add_to_selichot = u"Monday (1) / לשני קמא, Thursday / לחמישי, Monday (2) / לשני בתרא, Tenth of Teves / לעשרה בטבת, Fast of Esther / לתענית אסתר, Seventeenth of Tamuz / לשבעה עשר בתמוז"

add_JAs_to_schema_from_text(selichot, add_to_selichot)
add_JAs_to_schema_from_text(mincha, add_to_mincha)
add_JAs_to_schema_from_text(maariv, add_to_maariv)

for parent in [maariv, mincha]:
    assert parent.children[0].default
    remove_branch(parent.children[0])

nodes.append(selichot)
book.save()
library.rebuild(include_toc=True)
refresh_version_state(book.title)

