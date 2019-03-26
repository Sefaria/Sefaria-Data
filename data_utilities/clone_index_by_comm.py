import django
django.setup()
from sefaria.model import *
from sources.functions import *
import sys
from sefaria.system.exceptions import BookNameError
def verify_input(original, new):
    assert library.get_index(original), "{} doesn't exist".format(original)
    try:
        library.get_index(new)
        raise Exception("{} already exists".format(new))
    except BookNameError:
        pass

    assert original.split(" on ")[0] == new.split(" on ")[0], "Not same commentator: {} and {}".format(original, new)





if __name__ == "__main__":
    ## This clones indexes the following way:
    #./run ../Sefaria-Data/data_utilities/clone_index_by_commentary.py "Midrash Lekach Tov on Ruth" "Midrash Lekach Tov on Song of Songs"
    #The first text already exists and the second should follow the exact same structure as the first
    original = sys.argv[1]
    new = sys.argv[2]
    server = "https://www.sefaria.org"

    #assert original exists and new doesn't exist
    verify_input(original, new)

    #find base text of new commentary and old
    book = library.get_index(new.split(" on ")[-1])
    new_en_title = book.title
    new_he_title = book.get_title('he')

    book = library.get_index(original.split(" on ")[-1])
    old_en_title = book.title
    old_he_title = book.get_title('he')

    index = get_index_api(original, server)
    index["key"] = index["title"] = index['schema']['key'] = new
    good_titles = []
    for i, title in enumerate(index['schema']["titles"]):
        text = index['schema']['titles'][i]['text']
        orig_text = text
        text = text.replace(old_en_title, new_en_title)
        text = text.replace(old_he_title, new_he_title)
        if orig_text == text:
            print "WARNING: {} is the same as from {}, not keeping title".format(orig_text, text)
        else: #keep title
            index['schema']['titles'][i]['text'] = text
            good_titles.append(index['schema']['titles'][i])

    index["schema"]["titles"] = good_titles
    post_index(index, SEFARIA_SERVER)





