from sources.functions import *
from sefaria.helper.link import add_links_from_text
print(library.get_refs_in_string("Found in (Berakhot 3-4)", "en", citing_only=True))
# print(library.get_refs_in_string("ברכות ב", "he", citing_only=True))
add_links_from_text(Ref("Genesis 2"), "en", "Hello (Berakhot 3)", 1, 1)
# Link({"refs": ["Berakhot 2a", "Exodus 2:1"], "generated_by": "steve", "type": "", "auto": True}).save()
# Link({"refs": ["Genesis 2", "Exodus 2:1"], "generated_by": "steve", "type": "", "auto": True}).save()
