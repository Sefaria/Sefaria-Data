#encoding=utf-8
'''
also
Footnotes on Orot
in Philosophy Commentary
'''
from sefaria.model import *
if __name__ == "__main__":
    result = library.get_toc(True)
    c = Category()
    c.path = ["Philosophy", "Rav Kook"]
    c.add_primary_titles("Rav Kook", u"רב קוק")
    c.save()

    c2 = Category()
    c2.path = ["Philosophy", "Rav Kook", "Commentary"]
    c2.add_shared_term("Commentary")
    c2.save()

    books = list(IndexSet({"authors": {"$regex": "Kook"}}))
    books.append(library.get_index("Midbar Shur"))
    commentaries = [library.get_index("Footnotes on Orot")]
    for book in books:
        book.categories = c.path
        book.save()

    for book in commentaries:
        book.categories = c2.path
        book.save()



