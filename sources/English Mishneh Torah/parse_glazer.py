__author__ = 'stevenkaplan'

from data_utilities.XML_to_JaggedArray import *
SERVER = "http://draft.sefaria.org"

def reorder_modify(text):
    return bleach.clean(text, strip=True)

def reorder_test(x):
    return x.tag == "h1"


def fix_vt_and_vs(old_vtitle, old_vsource, arr_books, vt, vs):
    for book in arr_books:
        i = library.get_index(book)
        for v in i.versionSet():
            if v.versionTitle == old_vtitle:
                print book
                print v.versionTitle
                print v.versionSource
                print "found it\n"
                v.versionTitle = vt
                v.versionSource = vs
                try:
                    v.save()
                except:
                    pass


if __name__ == "__main__":

    hyamson = ['Mishneh Torah, Circumcision', 'Mishneh Torah, Fringes', 'Mishneh Torah, Prayer and the Priestly Blessing', 'Mishneh Torah, Tefillin, Mezuzah and the Torah Scroll', 'Mishneh Torah, Reading the Shema', 'Mishneh Torah, Foreign Worship and Customs of the Nations', 'Mishneh Torah, Torah Study', 'Mishneh Torah, Human Dispositions', 'Mishneh Torah, Foundations of the Torah']
    glazer = ['Mishneh Torah, Torah Study', "Mishneh Torah, Repentance", 'Mishneh Torah, Foundations of the Torah', 'Mishneh Torah, Foreign Worship and Customs of the Nations', 'Mishneh Torah, Human Dispositions']
    str = """./run scripts/move_draft_text.py "{}" -l "0" -v "en:The Mishneh Torah by Maimonides. trans. by Moses Hyamson, 1937-1949" -d "https://www.sefaria.org" -k "kAEw7OKw5IjZIG4lFbrYxpSdu78Jsza67HgR0gRBOdg" """
    for each in hyamson:
        print str.format(each)


    hyamson_vs = "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002108865"
    hyamson_vt = "The Mishneh Torah by Maimonides. trans. by Moses Hyamson, 1937-1949"
    hyamson_old_vt = u'The Mishneh Torah / by Maimonides ; edited according to the Bodleian (Oxford) Codex with introduction, Biblical and Talmudical references, notes and English translation by Moses Hyamson.'
    glazer_vt = "Mishnah Torah, Yod ha-hazakah, trans. by Simon Glazer, 1927"
    glazer_vs = "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001922235"


    '''
    post_info = {}
    post_info["language"] = "en"
    post_info["server"] = SERVER
    allowed_tags = ["book", "table", "intro", "ol", "h1", "h2", "h3", "h4", "h5", "part", "chapter", "p", "ftnote", "title", "footnotes", "appendix"]
    allowed_attributes = ["id"]
    p = re.compile("\d+a?\.")
    files = ["Hyamson_Vol1", "Glazer_Vol1", "Hyamson_Vol2"]
    for file in ["Hyamson_Vol2"]:
        title = file
        if file.startswith("Hyamson"):
            post_info["versionSource"] = "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002108865"
            post_info["versionTitle"] = "The Mishneh Torah by Maimonides. trans. by Moses Hyamson, 1937-1949"
        else:
            post_info["versionTitle"] = "Mishnah Torah, Yod ha-hazakah, trans. by Simon Glazer, 1927"
            post_info["versionSource"] = "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001922235"

        file_name = "Mishneh_Torah_{}.xml".format(file)
        parser = XML_to_JaggedArray(title, file_name, allowed_tags, allowed_attributes, post_info, change_name=True, image_dir="./images")
        parser.set_funcs(reorder_test=reorder_test, reorder_modify=reorder_modify,
                     grab_title_lambda=lambda x: len(x) > 0)
        parser.run()
    '''