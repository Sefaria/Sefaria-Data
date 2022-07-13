import django

django.setup()
from sefaria.helper.schema import *
import re


def create_intro():
    intro = JaggedArrayNode()
    intro.add_structure(["Paragraph"])
    intro.add_shared_term("Introduction")
    intro.key = f"Introduction"
    intro.validate()
    return intro


i = library.get_index("Tur")
# Convert to Schema nodes
for ja_node in i.nodes.children:
    convert_jagged_array_to_schema_with_default(ja_node)

for schema_node in i.nodes.children:
    intro = create_intro()
    insert_first_child(intro, schema_node)

chelek_map = {
    "אורח חיים": "Orach Chaim",
    "יורה דעה": "Yoreh Deah",
    "אבן העזר": "Even HaEzer",
    "חושן משפט": "Choshen Mishpat"
}
tur_intros = {}
with open("introductions_tur.txt", 'r') as f:
    for line in f:
        line = re.sub(r"@", "", line)
        is_chelek = re.findall(r"טור (.*) הקדמה", line)

        if is_chelek:
            cur_chelek = is_chelek[0]
            tur_intros[cur_chelek] = []
        else:
            tur_intros[cur_chelek].append(line.rstrip())


for chelek in tur_intros:
    chelek_ref = Ref(f"Tur, {chelek_map[chelek]}, Introduction")
    version =f"Tur {chelek_map[chelek]}, Vilna, 1923" if chelek_map[chelek] == "Orach Chaim" else f"{chelek_map[chelek]}, Vilna, 1923"
    tur_text_chunk = TextChunk(chelek_ref, lang="he", vtitle=version)
    tur_text_chunk.text = tur_intros[chelek]
    tur_text_chunk.save()
