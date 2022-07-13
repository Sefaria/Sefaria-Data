import django
django.setup()

from sefaria.helper.schema import insert_first_child, library, TextChunk, \
    JaggedArrayNode, Ref


def create_intro():
    intro = JaggedArrayNode()
    intro.add_structure(["Paragraph"])
    intro.add_shared_term("Introduction")
    intro.key = "Introduction"
    intro.validate()
    return intro


i = library.get_index("Beit Yosef")
intro = create_intro()
insert_first_child(intro, i.nodes)

by_intro_list = []
with open("introduction_beit_yosef.txt",'r') as f:
    for line in f:
        by_intro_list.append(line.rstrip())

by_ref = Ref("Beit Yosef, Introduction")
by_text_chunk = TextChunk(by_ref, lang="he", vtitle="Tur Orach Chaim, Vilna, 1923")
by_text_chunk.text = by_intro_list
by_text_chunk.save()
