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


    def __init__(self, title, file, allowedTags, allowedAttributes, post_info, parse):
        self.title = title
        self.parse = parse
        self.post_info = post_info
        self.file = file
        xml_text = ""
        for line in open(self.file):
            xml_text += line
        xml_text = bleach.clean(xml_text, tags=allowedTags, attributes=allowedAttributes, strip=False)
        self.root = etree.XML(xml_text)
        self.JA_nodes = {}
        self.pages = {}
        self.alt_struct = True
        self.footnotes = {}


    def run(self):
        for count, child in enumerate(self.root):
            name = self.grab_title(child)
            child = self.reorder_structure(child, name)
            ref = self.title + ", Footnotes, " + name
            self.JA_nodes[name] = self.go_down_to_text(name, child, ref)
            ref = self.title + ", " + name
            self.interpret(self.JA_nodes[name], ref)
            if self.title == "Or Neerav" and name == "PART VII":
                 self.interpret_footnotes_partvii()
            else:
                self.interpret_footnotes(name)
            self.footnotes = {}

        if self.alt_struct:
            file = open("alt_struct.txt", "w")
            for ref in self.pages:
                for each_one in self.pages[ref]:
                    file.write(ref+"; ")
                    file.write(each_one+"\n\n")
            file.close()



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


    def go_down_to_text(self, name, element, base_ref):
        text = {}
        text["text"] = []
        for index, child in enumerate(element):
            if len(child) > 0:
                name_node = ""
                if child.tag != "title":
                    self.grab_title(child) #take the title underneath, set it to text var,  so afterward, child.text will be the correct title
                new_ref = base_ref+"."+child.text if child.text.isdigit() else base_ref+", "+child.text
                text[child.text] = self.go_down_to_text(child.text, child, new_ref)
            else:
                if child.tag == "ftnote":
                    if base_ref not in self.footnotes:
                        self.footnotes[base_ref] = []
                    self.footnotes[base_ref].append(child.xpath("string()"))
                else:
                    text["text"] += [child.xpath("string()").replace("\n\n", " ")]

        return text


    def interpret_footnotes_partvii(self):
        comments = self.footnotes.values()[0]
        for index, comment in enumerate(comments):
            poss_num = int(comment.split(".", 1)[0])
            comments[index] = comment.replace(str(poss_num)+". ", "")

        comments = self.parse(comments)
        send_text = {
                    "text": comments,
                    "language": self.post_info["language"],
                    "versionSource": self.post_info["versionSource"],
                    "versionTitle": self.post_info["versionTitle"]
                }
        print self.title+", Footnotes, Part VII"
        post_text(self.title+", Footnotes, PART VII", send_text)


    def interpret_footnotes(self, name):
        prev_num = 0
        header = "Chapter"
        chapter = 1
        text = []
        for ref in self.footnotes:
            comments = self.footnotes[ref]
            for index, comment in enumerate(comments):
                try:
                    poss_num = int(comment.split(".", 1)[0])
                except:
                    pdb.set_trace()
                comments[index] = comment.replace(str(poss_num)+". ", "")

            comments = self.parse(comments)
            send_text = {
                    "text": comments,
                    "language": self.post_info["language"],
                    "versionSource": self.post_info["versionSource"],
                    "versionTitle": self.post_info["versionTitle"]
                }
            post_text(ref, send_text)




    def interpret(self, node, running_ref, prev="string"):
        assert Ref(running_ref)
        len_node = len(node)
        for key in node:
            if key.isdigit():
                if prev == "int":
                    new_running_ref = "%s.%s" % (running_ref, key)
                else:
                    new_running_ref = "%s, %s." % (running_ref, key)

                assert Ref(new_running_ref)
                self.interpret(node[key], new_running_ref, "int")
            elif key != "text":
                new_running_ref = "%s, %s" % (running_ref, key)
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
                print running_ref
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
            pages = re.findall("\[\d+[a-z]+\]", text[index])
            for page in pages:
                if ref+"."+str(index+1) in self.pages:
                    self.pages[ref+"."+str(index+1)] += [page]
                else:
                    self.pages[ref+"."+str(index+1)] = [page]
                text[index] = text[index].replace(page, "")
        return text


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
            if child.text.find("<italic>") >= 0 and child.tag == "title" and name == "PART VII":
                child.text = child.text.replace("<italic>", "").replace("</italic>", "")
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


'''
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

    def convert_nodes_to_JA(self):
        for name in self.JA_nodes:
            each_node = self.JA_nodes[name]
            title = each_node[0]
            each_node.pop(0)
            depth = get_depth(each_node)
            key = name
            new_node = SchemaNode()
    def collapse_subtitles(self, name):
        collapse all the subtitle slots in the array to one; we start from negative one instead of 0,
            because we don't want to get rid of all of them, but to keep one that the rest collapse into
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
'''