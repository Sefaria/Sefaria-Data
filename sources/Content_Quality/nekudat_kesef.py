import django
django.setup()
from sefaria.model import *
import re
from bs4 import BeautifulSoup

from tqdm import tqdm
from sefaria.helper.category import rename_category
from scripts.search_for_indexes_that_use_term import *
old_name = "Nekudat HaKesef"
new_name = new_title = "Nekudot HaKesef"

def create_new_term(old_name, new_name):
    old_t = Term().load({"name": old_name})
    old_he = old_t.get_primary_title('he')+'2'
    if Term().load({"name": new_name}) is None:
        new_t = Term()
        new_t.add_primary_titles(new_name, old_he)
        new_t.name = new_name
        new_t.save()
    else:
        new_t = Term().load({"name": new_name})
    return new_t

def modify_new_term():
    Term().load({"name": old_name}).delete()
    new_t = Term().load({"name": new_name})
    he = new_t.get_primary_title('he')[:-1]
    new_t.add_title(he, 'he', True, True)

def change_collective_titles(old_name, new_name):
    for b in library.get_indices_by_collective_title(old_name):
        print(f"Changing collective title: {b}")
        b = library.get_index(b)
        b.collective_title = new_name
        b.save()
        for r in b.all_section_refs():
            inline_links = []
            for l in r.linkset():
                inline_ref = getattr(l, 'inline_reference', None)
                if inline_ref:
                    inline_links.append(l)
            print(f"{len(inline_links)} inline links")
            for l in tqdm(inline_links):
                base_ref = l.refs[0] if l.refs[1].startswith(old_name) else l.refs[1]
                found = False
                for v in Ref(base_ref).versionset():
                    tc = TextChunk(Ref(base_ref), vtitle=v.versionTitle, lang=v.language)
                    if 'data-commentator' in tc.text:
                        found = True
                        new_text = tc.text.replace(f"""data-commentator='{old_name}'""", f"data-commentator='{new_name}'")
                        new_text = new_text.replace(f'data-commentator="{old_name}"', f'data-commentator="{new_name}"')
                        if new_text != tc.text:
                            tc.text = new_text
                            tc.save()
                if not found:
                    print(f"Warning: No data-commentator {old_name} found in {base_ref}")
                else:
                    l.inline_reference['data-commentator'] = new_name
                    l.save()

def change_book_titles(old_name, new_name):
    for comm in IndexSet({'dependence': "Commentary"}):
        if " on " in comm.title:
            if comm.title.split(" on ")[0] == old_name:
                old_comm_base = comm.title.split(" on ")[1]
                new_comm_title = f"{new_name} on {old_comm_base}"
                comm.set_title(new_comm_title)
                print("Changing book title")
                comm.save()


indices = library.all_index_records()
iterateNodes(indices, searchTerm=old_name)
new_term = create_new_term(old_name, new_name)
for c in CategorySet({"path": old_name}):
    rename_category(c, new_name, new_term.get_primary_title('he'))
library.rebuild(include_toc=True)
change_collective_titles(old_name, new_name)
change_book_titles(old_name, new_name)
modify_new_term()



