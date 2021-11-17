
__author__ = 'stevenkaplan'
from sources.functions import *
from sefaria.model import *
from data_utilities.XML_to_JaggedArray import XML_to_JaggedArray
from sefaria.helper.schema import *
import bleach

SERVER = "https://ste.cauldron.sefaria.org"

def reorder_modify(text):
    return bleach.clean(text, strip=True)

def tester(x):
    return x.tag == "h1"

if __name__ == "__main__":
	post_info = {}
	volume = 2
	post_info["language"] = "en"
	post_info["server"] = SERVER
	allowed_tags = ["volume", "book", "ack", "intro", "preface", "bibl", "part", "chapter", "p", "ftnote", "title", "ol", "footnotes", "appendix"]
	allowed_attributes = ["id"]
	p = re.compile("\d+a?\.")

	post_info["versionTitle"] = "Commentary on Song of Songs"
	post_info["versionSource"] = "https://www.sefaria.org"
	title = "Commentary on Song of Songs"

	with open("Commentary_On_The_Song_Of_Songs.xml") as f:
		file = f.read()
		parser = XML_to_JaggedArray(title, file, allowed_tags, allowed_attributes, post_info, change_name=True,
																titled=True, print_bool=True)
		parser.set_funcs(reorder_modify=reorder_modify, reorder_test=tester)
		parser.run()

	post_info["versionTitle"] = "Commentary on Lamentations"
	post_info["versionSource"] = "https://www.sefaria.org"
	title = "Commentary on Lamentations"

	with open("lamentations.xml") as f:
		file = f.read()
		parser = XML_to_JaggedArray(title, file, allowed_tags, allowed_attributes, post_info, change_name=True,
																titled=True, print_bool=True)
		parser.set_funcs(reorder_modify=reorder_modify, reorder_test=tester)
		parser.run()

	post_info["versionTitle"] = "Commentary on Genesis"
	post_info["versionSource"] = "https://www.sefaria.org"
	title = "Commentary on Genesis"

	with open("saragossa.xml") as f:
		file = f.read()
		parser = XML_to_JaggedArray(title, file, allowed_tags, allowed_attributes, post_info, change_name=True,
																titled=True, print_bool=True)
		parser.set_funcs(reorder_modify=reorder_modify, reorder_test=tester)
		parser.run()