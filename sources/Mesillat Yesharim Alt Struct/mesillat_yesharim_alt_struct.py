__author__ = 'stevenkaplan'
from sefaria.model import *
from BeautifulSoup import *
from sources.functions import *
if __name__ == "__main__":
    contents = BeautifulSoup(open("alt_struct.xml")).contents[2].contents[3]
    nodes = []
    contents = filter(lambda x: type(x) is not NavigableString, contents)
    for count, each in enumerate(contents):
        en, he = each.attrs[0][1].split(" / ")
        node = ArrayMapNode()
        node.add_primary_titles(en, he)
        node.depth = 0
        if count == 0:
            node.wholeRef = "Mesillat Yesharim, Introduction"
        else:
            node.wholeRef = "Mesillat Yesharim {}".format(count)
        node.refs = []
        nodes.append(node.serialize())



    index = get_index("Mesillat Yesharim", server="http://www.sefaria.org")
    index['alt_structs'] = {"Subject": {"nodes": nodes}}
    post_index(index, server="http://www.sefaria.org")
