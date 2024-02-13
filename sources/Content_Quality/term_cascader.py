import django
django.setup()
from sefaria.model import *
import re
from bs4 import BeautifulSoup
import sys
from tqdm import tqdm
from sefaria.helper.category import rename_category
from scripts.search_for_indexes_that_use_term import *
old_name = new_name = ""
changes = set()
def create_new_term():
    old_t = Term().load({"name": old_name})
    old_he = old_t.get_primary_title('he')+'2'
    if Term().load({"name": new_name}) is None:
        new_t = Term()
        new_t.add_primary_titles(new_name, old_he)
        new_t.name = new_name
        new_t.save()
    else:
        new_t = Term().load({"name": new_name})
    library.rebuild(include_toc=True)
    return new_t

def modify_new_term():
    Term().load({"name": old_name}).delete()
    new_t = Term().load({"name": new_name})
    he = new_t.get_primary_title('he')[:-1]
    new_t.add_title(he, 'he', True, True)
    new_t.save()
    library.rebuild(include_toc=True)

def change_collective_titles():
    for b in tqdm(library.get_indices_by_collective_title(old_name)):
        changes.add(f"Changing collective title: {b}")
        b = library.get_index(b)
        b.collective_title = new_name
        b.save()
        for r in b.all_section_refs():
            inline_links = []
            for l in r.linkset():
                inline_ref = getattr(l, 'inline_reference', None)
                if inline_ref:
                    inline_links.append(l)
            if len(inline_links) > 0:
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
                        changes.add(f"Warning: No data-commentator {old_name} found in {base_ref}")
                    else:
                        l.inline_reference['data-commentator'] = new_name
                        l.save()
    library.rebuild(include_toc=True)


def change_book_titles():
    books = IndexSet({'dependence': "Commentary", "title": {"$regex": f"^{old_name}"}})
    books = books.array()[:10]
    for comm in tqdm(books):
        if comm.title.split(" on ")[0] == old_name or f"{old_name} " in comm.title:
            new_comm_title = comm.title.replace(old_name, new_name, 1)
            comm.set_title(new_comm_title)
            changes.add("Changing book title")
            comm.save()

def change_topic_title():
    t = Topic().load({"titles.text": old_name})
    if t:
        changes.add("Changing topic title")
        t.add_title(new_name, 'en', True, True)
        t.save()

def change_all_categories():
    for path_len in list(range(7, 0, -1)):
        categories = CategorySet({"$and": [{"path": {"$size": path_len}}, {"lastPath": old_name}]})
        for c in categories:
            changes.add(f"Changing category: {c}")
            rename_category(c, new_name, new_term.get_primary_title('he'))
    library.rebuild(include_toc=True)


if __name__ == "__main__":
    # indices = library.all_index_records()
    # iterateNodes(indices, searchTerm=old_name)
    old_name = sys.argv[1]
    new_name = sys.argv[2]
    books_only = sys.argv[3] == "books_only"
    if not books_only:
        new_term = create_new_term()
        change_topic_title()
        change_all_categories()
        change_collective_titles()
        modify_new_term()
    else:
        change_book_titles()
    print("RESULTS ************************************")
    for x in changes:
        print(x)



