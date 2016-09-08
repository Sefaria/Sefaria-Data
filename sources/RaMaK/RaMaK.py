__author__ = 'stevenkaplan'
import XML_to_JaggedArray


class RaMaK:

    def __init__(self):
        self.nodes = []


    def parse(self):
        JA_array = [("intro", 1, False), ("part", 2, True), ("part", 2, True), ("part", 2, True), ("part", 2, True), ("part", 2, True)]
        JA_array += [("part", 2, True), ("part", 1, False), ("appendix", 2, True)]
        allowedTags = ["book", "intro", "part", "appendix", "chapter", "p", "ftnote", "title"]
        allowedAttributes = ["id"]
        parser = XML_to_JaggedArray("../sources/DC labs/Robinson_MosesCordoveroIntroductionToKabbalah.xml", JA_array, allowedTags, allowedAttributes)
        parser.run()
        self.nodes = parser.getNodes()


if __name__ == "__main__":
    ramak = RaMaK()

