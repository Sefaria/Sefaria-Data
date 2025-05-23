# -*- coding: utf-8 -*-

__author__ = 'stevenkaplan'
import django
django.setup()
import sys
from sefaria.system.exceptions import *
from sefaria.model import *
from sefaria.model.schema import TitleGroup
import csv
from sources.functions import *
'''
Take an index, serialize schema, travel through schema replacing every instance of old_title with new_title
and then load new index with this schema
'''

def verify_titles_and_return_contents(base_text_title, existing_index_title, new_index_title):
    '''
    Check that the existing index title exists and that the new index title does NOT exist.
    :param existing_index_title: Name of existing index who's structure will be cloned
    :param new_index_title: Name of new index
    :return:
    '''
    try:
        old_index = library.get_index(existing_index_title)
    except BookNameError:
        raise InputError("{} can't be found in library.".format(existing_index_title))

    base_text_match = False
    for base_title in old_index.base_text_titles:
        if library.get_index(base_text_title) == library.get_index(base_title):
            base_text_match = True

    if not base_text_match or (" on " in new_index_title and new_index_title.split(" on ")[-1] != base_text_title):
        raise InputError("The new index must comment on the same text as the existing index.")

    # assert that the new book already exists.  it should generate a BookNameError; otherwise, it already exists and
    # should not be created
    try:
        library.get_index(new_index_title)
        raise InputError("{} already exists.  You can clone the structure of {} only for a new index.".format(new_index_title, existing_index_title))
    except BookNameError:
        term_title = new_index_title.split(" on ")[0]
        term = Term().load({"name": term_title})
        if not term:
            raise InputError("Before adding the book {}, please add {} as a term.".format(new_index_title, term_title))

        return old_index.contents(v2=True)



def copy_keys(contents):
    keys_to_copy = ["base_text_titles", "base_text_mapping", "dependence", "addressTypes", "sectionNames", "depth"]
    new_contents = {key: contents[key] for key in contents if key in keys_to_copy}
    if "base_text_titles" in new_contents:
        base_text_titles = contents["base_text_titles"]
        new_contents["base_text_titles"] = [x['en'] for x in base_text_titles]
    return new_contents




def alter_contents(contents, new_index_title, book_term):
    new_contents = copy_keys(contents)

    new_contents["title"] = new_index_title

    new_heTerm = book_term.titles[0]["text"] if book_term.titles[0]["lang"] == "he" else book_term.titles[1]["text"]
    new_enTerm = book_term.titles[0]["text"] if book_term.titles[0]["lang"] == "en" else book_term.titles[1]["text"]
    old_heTerm = contents["heTitle"].split(" על ")[0]
    old_enTerm = contents["title"].split(" on ")[0]

    new_contents["heTitle"] = new_index_he_title = contents["heTitle"].replace(old_heTerm, new_heTerm)
    new_contents["collective_title"] = new_enTerm

    new_contents["schema"] = alter_schema(contents["schema"], new_index_title, new_index_he_title)

    new_contents["categories"] = [cat.replace(old_enTerm, new_enTerm) for cat in contents["categories"]]
    new_contents["titleVariants"] = []
    new_contents["heTitleVariants"] = []

    return new_contents


def alter_schema(schema, new_index_title, new_index_he_title):
    schema["key"] = schema["title"] = new_index_title
    schema["heTitle"] = new_index_he_title
    title_group = TitleGroup()
    title_group.add_title(new_index_title, 'en', primary=True)
    title_group.add_title(new_index_he_title, 'he', primary=True)
    title_group.validate()
    schema["titles"] = title_group.titles
    return schema

if __name__ == "__main__":
    '''
    Clone Index is a command-line tool used when we want to create a new commentary, say "Zeroa Yamin", a Pirkei Avot commentary,
    but we know it is going to be the same structure as other Pirkei Avot commentaries, such as "Magen Avot".
    In directory Sefaria-Project one can run:
    ./run ../Sefaria-Data/linking_utilities/clone_index.py [base_text] [existing_commentary] [new_commentary]
    and it will create a new Index that is a commentary on the base text and has the same structure as the
    existing commentary.
    For example,
    ./run ./Sefaria-Data/linking_utilities/clone_index.py "Pirkei Avot" "Magen Avot" "Zeroa Yamin"
    will create a new Pirkei Avot commentary called "Zeroa Yamin" and
    will have the exact same structure as "Magen Avot"
    Likewise:
    ./run ./Sefaria-Data/linking_utilities/clone_index.py "Genesis" "Rashi on Genesis" "Malbim on Genesis"
    will create "Malbim on Genesis" with the structure of "Rashi on Genesis".
    '''
    new_titles = []
    base_text_title = existing_index_title = ""
    if len(sys.argv) > 2:
        base_text_title = sys.argv[1]
        existing_index_title = sys.argv[2]
        new_titles = [(sys.argv[3], sys.argv[4])]
    else:
        csv_file = "../sources/Clone index CSVs/{}".format(sys.argv[1])
        csv_reader = csv.reader(open(csv_file))
        for i, row in enumerate(csv_reader):
            if i == 0:
                #first should be index to clone
                existing_index_title = row[1]
            elif i == 1:
                #second row should be base text that this is a commentary on
                base_text_title = row[1]
            else:
                row[1] = row[1].decode('utf-8')
                new_titles.append((row[0], row[1]))

    for new_title in new_titles:
        #get en and he titles and create Term
        new_index_title = new_title[0]
        he_title = new_title[1]
        term_title = new_index_title.split(" on ")[0]
        book_term = Term().load({"name": term_title})
        if not book_term:
            book_term = Term()
            book_term.name = term_title
            he_term_title = he_title.split(" על ")[0]
            book_term.add_primary_titles(term_title, he_term_title)
            book_term.save()

        #check that the book can be added: that it doesn't exist, that there is a base text, that is an index to clone and a Term object
        try:
            existing_index_contents = verify_titles_and_return_contents(base_text_title, existing_index_title, new_index_title)
        except InputError as e:
            print(e)
            continue
        if existing_index_contents:
            #alter the copy of the index we are cloning and save the new index
            new_index_contents = alter_contents(existing_index_contents, new_index_title, book_term)

            #new_index = Index(new_index_contents).save()
            #print new_index.contents(v2=True)
            add_category(term_title, new_index_contents["categories"])
            post_index(new_index_contents)
