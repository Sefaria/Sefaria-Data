__author__ = 'stevenkaplan'

from data_utilities.XML_to_JaggedArray import *

def create_schema():
    pass

def reorder_modify(text):
    return bleach.clean(text, strip=True)

if __name__ == "__main__":
    SERVER = "http://ste.sefaria.org"
    for i in range(6):
        create_schema()
        post_info = {}
        post_info["language"] = "en"
        post_info["server"] = SERVER
        allowed_tags = ["book", "intro", "part", "chapter", "p", "ftnote", "title", "ol", "footnotes", "appendix"]
        allowed_attributes = ["id"]
        p = re.compile("\d+a?\.")

        post_info["versionTitle"] = "Contemporary halakhic problems; by J. David Bleich, 1977-2005"
        post_info["versionSource"] = "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001100271"
        title = "Contemporary Halakhic Problems Volume {}".format(i+1)
        file_name = "ContemporaryHalakhicProblems-Vol{}.xml".format(i+1)

        parser = XML_to_JaggedArray(title, file_name, allowed_tags, allowed_attributes, post_info, change_name=True, image_dir="./images")
        parser.set_funcs(reorder_test=lambda x: x.tag == "title" and x.text.find("<bold>") == 0, reorder_modify=reorder_modify)
        parser.run()