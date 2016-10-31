__author__ = 'stevenkaplan'
from XML_to_JaggedArray import XML_to_JaggedArray

'''Every node whose first element is a title is the node's title.  Then remove these titles possibly.
  Every other title has structural significance if it has a bold tag as a child
    Titles can structure text
    Footnotes
    Also consider how to decipher JA_array or allowed_tags automatically
    '''

if __name__ == "__main__":
    JA_array = [("intro", 2, False), ("part", 2, True), ("part", 2, True), ("part", 2, True), ("part", 2, True), ("part", 2, True)]
    JA_array += [("part", 2, True), ("part", 1, False), ("appendix", 2, True)]
    allowed_tags = ["book", "intro", "part", "appendix", "chapter", "p", "ftnote", "title"]
    structural_tags = ["title"] #this is not all tags with structural significance, but just
                                #the ones we must explicitly mention, because it has no children,
                                #we want what comes after it until the next instance of it to be its children anyway
    allowed_attributes = ["id"]
    file_name = "../sources/DC labs/Robinson_MosesCordoveroIntroductionToKabbalah.xml"
    ramak = XML_to_JaggedArray(file_name, JA_array, allowed_tags, allowed_attributes)
    nodes = ramak.run()
    print 'hi'
    #depth = ramak.parser().get_depth()
    #ramak.parser.convert_nodes_to_JA()