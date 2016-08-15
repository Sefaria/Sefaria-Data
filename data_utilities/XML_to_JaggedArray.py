'''
How to convert XML tree into JaggedArray
User provides in order the names of the JaggedArrayNodes for the given text and the depths for each one.
Then
User gives a level of depth to go to and then xpath("string()") on that depth to return a jagged array of that depth. 
'''
import pdb
import bleach
from lxml import etree

class XML_to_JaggedArray:


    def __init__(self, file, JA_array, allowedTags, allowedAttributes):
        #depth is level at which tree has text
        self.file = file
        xml_text = ""
        for line in open(self.file):
            xml_text += line
        xml_text = bleach.clean(xml_text, tags=allowedTags, attributes=allowedAttributes, strip=False)
        self.root = etree.XML(xml_text)
        self.JA_array = JA_array
        self.JA_nodes = {}


    def run(self):
        for count, child in enumerate(self.root):
            attrib = child.attrib
            name = attrib["id"] if len(attrib) > 0 else self.JA_array[count][0] #if I have an attribute identifying my name, use that, else use name user provided in JA_array
            depth = self.JA_array[count][1]
            has_subtitle = self.JA_array[count][2]
            self.JA_nodes[name] = self.goDownToText(child, 0, depth)
            subtitle = ""
            how_many_to_pop = -1 #collapse all the subtitle slots in the array to one; we start from negative one because we don't want to get rid of all of them, but to collapse them into one

            if has_subtitle:
                print name
                '''
                if there is a subtitle, this means add to subtitle every item that is a string not array, keep count, then collapse them into one
                '''
                for gchild_count, gchild in enumerate(self.JA_nodes[name]):
                    if type(gchild) is str:
                        subtitle += gchild
                        how_many_to_pop += 1

                pdb.set_trace()
                for i in range(how_many_to_pop):
                    self.JA_nodes[name].pop(0)

                self.JA_nodes[name][0] = subtitle

        pdb.set_trace()


    def goDownToText(self, element, level, depth):
        if level == depth:
            return element.xpath("string()").replace("\n\n", " ")
        else:
            text = []
            for child in element:
                result = self.goDownToText(child, level+1, depth)
                text.append(result)
            return text


    def getNodes(self):
        print 'hi'


if __name__ == "__main__":
    JA_array = [("intro", 1, False), ("part", 2, True), ("part", 2, True), ("part", 2, True), ("part", 2, True), ("part", 2, True)]
    JA_array += [("part", 2, True), ("part", 1, False), ("appendix", 2, True)]
    allowedTags = ["book", "intro", "part", "appendix", "chapter", "p", "ftnote", "title"]
    allowedAttributes = ["id"]
    parser = XML_to_JaggedArray("../sources/DC labs/Robinson_MosesCordoveroIntroductionToKabbalah.xml", JA_array, allowedTags, allowedAttributes)
    print parser.root
    parser.run()
    nodes = parser.getNodes()
    pdb.set_trace()
