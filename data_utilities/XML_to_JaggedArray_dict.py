'''
How to convert XML tree into JaggedArray
User provides in order the names of the JaggedArrayNodes for the given text and the depths for each one.
Then
User gives a level of depth to go to and then xpath("string()") on that depth to return a jagged array of that depth. 
'''
import pdb
import bleach
from lxml import etree
import sys
sys.path.append("../sources")
from functions import *
sys.path.append("../../Sefaria-Project")
from sefaria.model import *

class XML_to_JaggedArray:


    def __init__(self, title, file, JA_array, allowedTags, allowedAttributes, post_info):
        #depth is level at which tree has text
        self.title = title
        self.post_info = post_info
        self.file = file
        xml_text = ""
        for line in open(self.file):
            xml_text += line
        xml_text = bleach.clean(xml_text, tags=allowedTags, attributes=allowedAttributes, strip=False)
        self.root = etree.XML(xml_text)
        self.JA_array = JA_array
        self.JA_nodes = {}
        self.pages = {}


    def run(self):
        for count, child in enumerate(self.root):
            attrib = child.attrib
            depth = self.JA_array[count][1]
            has_subtitle = self.JA_array[count][2]
            name = self.grab_title(child)
            #child = self.reorder_structure(child, name)
            self.JA_nodes[name] = self.go_down_to_text(name, child, has_subtitle)
            ref = self.title + ", " + name
            assert Ref(ref)
            self.interpret(self.JA_nodes[name], ref)
        self.post()


    def post(self):
        for key in self.book_dict:
            post_text(key, self.book_dict[key])


    def grab_title(self, element, tag="bold", delete=True):
        '''
        Get the name return it and delete the first element
        '''
        if element[0].tag == tag or element[0].text.find("<bold>") >= 0:
            name = bleach.clean(element[0].text, strip=True)
            element.text = name
            if delete:
                element.remove(element[0])
            return name
        return ""


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


    def reorder_structure(self, element, name):
        '''
        We have something like this:
        A. Root
            1. Title node
            2. Str node
            3. Str node
            4. Title node
            5. Str node.
        This function returns the following:
        A. Root
            1. Title node
                a. Str node
                b. Str node
            2. Title node
                a. Str node
        '''
        next_will_be_children = False
        parent = None
        children = []
        orig_length = len(element) - 1
        for index, child in enumerate(element):
            if (child.text.find("<bold>") >= 0 or child.tag == "bold") and name == "Introduction":
                if next_will_be_children == True:
                    for new_child in children:
                        parent.append(new_child)
                    children = []
                parent = child
                next_will_be_children = True
            elif child.tag == "ftnote" and next_will_be_children:
                children.append(child)
            elif next_will_be_children == True:
                children.append(child)

            if index == orig_length:
                for new_child in children:
                    parent.append(new_child)

        for child in element:
            child = self.reorder_structure(child, name)

        return element


    def convert_nodes_to_JA(self):
        for name in self.JA_nodes:
            each_node = self.JA_nodes[name]
            title = each_node[0]
            each_node.pop(0)
            depth = get_depth(each_node)
            key = name
            new_node = SchemaNode()



    def go_down_to_text(self, name, element, has_subtitle=False):
        text = {}
        text["text"] = []
        #text[name] = {}
        for index, child in enumerate(element):
            if len(child) > 0:
                name_node = ""
                if child.tag != "title":
                    self.grab_title(child) #take the title underneath it so afterward, child.text will be the correct title
                if child.text.isdigit():
                    text
                text[child.text] = self.go_down_to_text(child.text, child, has_subtitle)
            else:
                text["text"] += [child.xpath("string()").replace("\n\n", " ")]

        return text



    def convert_into_schema(self):
        for name in self.JA_nodes:
            depth = self.JA_dict[name]
            process(name, self.JA_nodes[name], depth, 0)



    def process(self, name, dict, depth, level):
        node = SchemaNode()
        node.key = name
        name.add_title(name, "en", primary=True)
        for key in dict:
            process(key, dict[key], depth, level+1)


    def interpret(self, node, running_ref, prev="string"):
        len_node = len(node)
        for key in node:
            if key.isdigit():
                if prev == "int":
                    new_running_ref = "%s.%s" % (running_ref, key)
                else:
                    new_running_ref = "%s, %s." % (running_ref, key)
                try:
                    assert Ref(new_running_ref)
                except:
                    pdb.set_trace()
                assert Ref(new_running_ref)
                self.interpret(node[key], new_running_ref, "int")
            elif key != "text":
                new_running_ref = "%s, %s" % (running_ref, node[key])
                assert Ref(new_running_ref)
                self.interpret(node[key], new_running_ref, "string")
            elif key == "text" and len_node == 1:
                assert Ref(running_ref)
                node[key] = self.parse(node[key])
                text = self.get_pages(node[key], running_ref)
                send_text = {
                    "text": text,
                    "language": self.post_info["language"],
                    "versionSource": self.post_info["versionSource"],
                    "versionTitle": self.post_info["versionTitle"]
                }
                post_text(running_ref, send_text)
            elif key == "text":
                assert Ref(running_ref)
                new_running_ref = running_ref + ",_Subject"
                assert Ref(new_running_ref)
                node[key] = self.parse(node[key])
                text = self.get_pages(node[key], new_running_ref)
                send_text = {
                    "text": text,
                    "language": self.post_info["language"],
                    "versionSource": self.post_info["versionSource"],
                    "versionTitle": self.post_info["versionTitle"]
                }

                post_text(new_running_ref, send_text)


def get_pages(self, text, ref):
    print ref
    for index, each_line in enumerate(text):
        pages = re.findall("\[\d+[a-z]+\]", text)
        for page in pages:
            if ref+"."+str(index+1) in pages_dict:
                self.pages[ref+"."+str(index+1)] += [page]
            else:
                self.pages[ref+"."+str(index+1)] = [page]
            text[index] = text[index].replace(page, "")
    return text
'''
1. Need to remove pages from text before it gets posted
2. But also need to keep track of the Ref of every time there is a page
So when I have the text and the ref to post, I go through text adding every ref that has a page and the actual page itself
to a dict.
Then remove them.
Then post text
'''