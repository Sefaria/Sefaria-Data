# -*- coding: utf-8 -*-
import django
django.setup()

from sefaria.model import *
from sources.functions import add_term
#
# ind = library.get_index("Yalkut Shimoni on Torah")
# old_d = ind.alt_structs
# new_d = {"alt_structs": {"Chapters": old_d["Chapters"], "Parasha":old_d["Parsha"]}}
# ind.update_from_dict(new_d)
# ind.save()
#
#
# ind = library.get_index("Yalkut Shimoni on Nach")
# old_d = ind.alt_structs
# new_d = {"alt_structs": {"Book":old_d["Books"]}}
# ind.update_from_dict(new_d)
# ind.save()

# ind = library.get_index("Sifrei Devarim")
# old_d = ind.alt_structs
# new_d = {"alt_structs": {"Chapters": old_d["Chapters"], "Parasha":old_d["Parsha"]}}
# ind.update_from_dict(new_d)
# ind.save()

def find_nodes_without_Term():
    tofix = []
    for ind_name in library.get_index_forest():
        ind = ind_name.index
        if ind.has_alt_structures():
            alt_titles = ind.alt_structs.keys()
            problematic = [(ind.title, term_title) for term_title in alt_titles if not Term().load({"name": f"{term_title}"})]
            if problematic:
                for term_title in problematic:
                    option = Term().load({"titles.text":f"{term_title[1]}"})
                    if option:
                        print(problematic[0][0], problematic[0][1], option.name)
                        tofix.append((problematic[0][0], problematic[0][1], option.name))
                    else:
                        print(problematic)
    print("done find_func")
    return tofix


def fix_alt_structs_spelling(book, wrong="Parsha", right="Parasha"):
    ind = library.get_index(book)
    old_d = ind.alt_structs
    # try:
    #     assert len(list(old_d.keys())) == 1, f"book {book} has more than one alt_struct"
    # except AssertionError:
    #     print(f"alt structs are: {ind.alt_structs}")
    #     return
    # new_d = {"alt_structs": {right: old_d[wrong]}}
    new_d = old_d.copy()
    if wrong not in list(old_d.keys()):
        return
    new_d[f"{right}"] = old_d.get(wrong)
    del new_d[f'{wrong}']
    ind.update_from_dict({"alt_structs":new_d})
    ind.save()
    test = library.get_index(book)
    key_names = list(test.alt_structs.keys())
    if right in key_names and wrong not in key_names:
        print(f"{book} term spelling {wrong} changed to {right}")


if __name__ == '__main__':
    # tofixs = find_nodes_without_Term()
    # for tofix in tofixs:
    #     fix_alt_structs_spelling(tofix[0])
    # fix_alt_structs_spelling('Sefer HaKana', 'Titles', 'Topic')
    # fix_alt_structs_spelling
    trios1 =[('Rabbeinu Bahya', 'By Parasha', 'Parasha'),
            ('Psalms',"Books","Book"),
    ('Messilat Yesharim', "Contents", "Topic"),
    ('Ben Ish Hai', 'Subject',"Topic"),
    ('Torat Netanel', 'Simanim', "Siman"),
    ('Teshuvot HaRosh', 'Index',"Contents"),
    ('Chokhmat Adam', 'Shaar', "Gate"),
    ('Rav Peninim on Proverbs', 'Houses', "Chamber")]
    trios = [('Messilat Yesharim', "Contents", "Topic")]
    for trio in trios:
        fix_alt_structs_spelling(*trio)
