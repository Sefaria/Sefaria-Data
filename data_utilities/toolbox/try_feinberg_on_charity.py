__author__ = 'stevenkaplan'

from data_utilities.XML_to_JaggedArray import *

if __name__ == "__main__":
    post_info = {}
    post_info["language"] = "en"
    post_info["server"] = "asdf"
    allowed_tags = ["book", "intro", "part", "chapter", "p", "ftnote", "title", "ol", "footnotes", "appendix"]
    allowed_attributes = ["id"]
    p = re.compile("\d+a?\.")

    post_info["versionTitle"] = "Responsa of Rav Moshe Feinstein, trans. by Moshe David Tendler; Vol. 1: Care of the Critically Ill, Hoboken, NJ: Ktav, 1996."
    post_info["versionSource"] = "http://www.ktav.com/index.php/responsa-of-rav-moshe-feinstein.html"
    title = "Care of the Critically Ill"
    file_name = "Feinberg_on_Charity.xml"

    parser = XML_to_JaggedArray(title, file_name, allowed_tags, allowed_attributes, post_info, change_name=True, image_dir="./images",
                                titled=True)
    parser.set_funcs(reorder_test=lambda x: x.tag == "title" and x.text.find("<bold>") == 0, reorder_modify=lambda text: bleach.clean(text, strip=True))
    parser.run()