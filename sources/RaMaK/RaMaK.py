__author__ = 'stevenkaplan'
from XML_to_JaggedArray import XML_to_JaggedArray

'''Chapters first element should be its title.
    Titles can structure text
    Footnotes '''

if __name__ == "__main__":
    JA_array = [("intro", 1, False), ("part", 2, True), ("part", 2, True), ("part", 2, True), ("part", 2, True), ("part", 2, True)]
    JA_array += [("part", 2, True), ("part", 1, False), ("appendix", 2, True)]
    allowed_tags = ["book", "intro", "part", "appendix", "chapter", "p", "ftnote", "title"]
    allowed_attributes = ["id"]
    file_name = "../sources/DC labs/Robinson_MosesCordoveroIntroductionToKabbalah.xml"
    ramak = XML_to_JaggedArray(file_name, JA_array, allowed_tags, allowed_attributes)
    nodes = ramak.parse()
    print 'hi'
    #depth = ramak.parser().get_depth()
    #ramak.parser.convert_nodes_to_JA()