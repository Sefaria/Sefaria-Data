#encoding=utf-8
from sefaria.model import *
if __name__ == "__main__":

    library.get_toc(rebuild=True)

    print "Creating categories: Rav Kook and Rav Kook/Commentary"
    c = Category()
    c.path = ["Philosophy", "Rav Kook Works"]
    c.add_primary_titles("Rav Kook Works", u"כתבי הרב קוק")
    c.save()

    c2 = Category()
    c2.path = ["Philosophy", "Rav Kook Works", "Commentary"]
    c2.add_shared_term("Commentary")
    c2.save()

    print "Moving books from old categories to new ones"
    books = list(IndexSet({"authors": {"$regex": "Kook"}}))
    commentaries = [library.get_index("Footnotes on Orot")]
    for book in books:
        book.categories = c.path
        book.save()

    for book in commentaries:
        book.categories = c2.path
        book.save()

    print "Deleting empty category Philosophy/Commentary/Footnotes"
    library.rebuild_toc() #reset it here because otherwise it's impossible to delete the category
    c = Category().load({"path": ["Philosophy", "Commentary", "Footnotes"]})
    c.delete()

    print "Resetting cache and toc"
    library.rebuild()
    library.rebuild_toc()



