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

            '''if I have an attribute identifying my name, use that, otherwise use name user provided in JA_array'''
            #name = attrib["id"] if len(attrib) > 0 else self.JA_array[count][0]


            depth = self.JA_array[count][1]
            has_subtitle = self.JA_array[count][2]
            name = self.get_name(child)
            child = self.reorder_structure(child)
#ISSUE IS WE LOSE THE NAME OF THE LEVEL 1 NODES LIKE "KABBALAH" in "INTRODUCTION"
            self.JA_nodes[name] = self.go_down_to_text(child, depth, 0, has_subtitle)

            if has_subtitle:
                self.collapse_subtitles(name)

        return self.JA_nodes


    def get_name(self, element):
        '''
        Get the name return it and delete the first element
        '''
        if element[0].tag == "title":
            name = element[0].text
            name = bleach.clean(name, strip=True)
            element.remove(element[0])
            return name

    def collapse_subtitles(self, name):
        '''collapse all the subtitle slots in the array to one; we start from negative one instead of 0,
            because we don't want to get rid of all of them, but to keep one that the rest collapse into'''
        how_many_to_pop = -1
        subtitle = ""
        for gchild_count, gchild in enumerate(self.JA_nodes[name]):
            if type(gchild) is not list:
                subtitle += gchild.encode('utf-8')
                how_many_to_pop += 1

        for i in range(how_many_to_pop):
            self.JA_nodes[name].pop(0)

        self.JA_nodes[name][0] = subtitle


    def get_depth(self, array):
        depth = 0
        while type(array) is list:
            array = array[1]
            depth += 1
        return depth


    def reorder_structure(self, element):
        next_will_be_children = False
        parent = None
        children = []
        for index, child in enumerate(element):
            if child.tag == "title":
                if next_will_be_children == True:
                    for new_child in children:
                        parent.append(new_child)
                    children = []
                parent = child
                next_will_be_children = True
            elif child.tag == "ftnote" and next_will_be_children:
                for new_child in children:
                    parent.append(new_child)
                return element
            elif next_will_be_children == True:
                children.append(child)
            if index == len(element) - 1:
                for new_child in children:
                    parent.append(new_child)
        return element


    def go_down_to_text(self, element, depth, level=0, has_subtitle=False):
        if level == depth:
            return element.xpath("string()").replace("\n\n", " ")
        else:
            text = {}
            name = "HI" #self.get_name(element)
            for child in element:
                result = self.go_down_to_text(child, depth, level+1, has_subtitle)
                text[name] = result
            if has_subtitle and len(element) == 0:
                text = element.xpath("string()")
            return text

    def convert_nodes_to_JA(self):
        for name in self.JA_nodes:
            each_node = self.JA_nodes[name]
            title = each_node[0]
            each_node.pop(0)
            depth = get_depth(each_node)
            key = name
            new_node = SchemaNode()


