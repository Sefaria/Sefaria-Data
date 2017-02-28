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


    def __init__(self, title, file, allowedTags, allowedAttributes, post_info, array_of_names=[], deleteTitles=True):
        self.title = title
        self.post_info = post_info
        self.file = file
        self.parse_dict = {}
        self.allowedTags = allowedTags
        self.allowedAttributes = allowedAttributes
        self.JA_nodes = {}
        self.pages = {}
        self.alt_struct = True
        self.footnotes = {}
        self.array_of_names = array_of_names
        self.deleteTitles = deleteTitles
        self.prev_footnote = ""



    def set_funcs(self, grab_title_lambda=lambda x: x[0].tag == "title", reorder_test=lambda x: False, reorder_modify=lambda x: x, modify_before=lambda x: x):
        self.modify_before = modify_before
        self.grab_title_lambda = grab_title_lambda
        self.reorder_test = reorder_test
        self.reorder_modify = reorder_modify


    def run(self):
        xml_text = ""
        for line in open(self.file):
            xml_text += line
        xml_text = self.modify_before(xml_text)
        xml_text = bleach.clean(xml_text, tags=self.allowedTags, attributes=self.allowedAttributes, strip=False)
        self.root = etree.XML(xml_text)

        for count, child in enumerate(self.root):
            name = self.grab_title(child, delete=self.deleteTitles, test_lambda=self.grab_title_lambda)
            if self.array_of_names:
                name = self.array_of_names[count]
            print name
            child = self.reorder_structure(child, False)
            this_ref = "{}, {}".format(self.title, name)
            self.JA_nodes[name] = self.go_down_to_text(name, child)
            self.interpret(self.JA_nodes[name], this_ref)

        if self.alt_struct:
            file = open("alt_struct.txt", "w")
            for ref in self.pages:
                for each_one in self.pages[ref]:
                    file.write(ref+"; ")
                    file.write(each_one+"\n\n")
            file.close()


    def getChildren(self, parent):
        titles = []
        for child in parent:
            titles.append(child.tag)
        return titles



    def post(self, ref, text):
        if self.post_info["server"] == "post":
            send_text = {
                    "text": text,
                    "language": self.post_info["language"],
                    "versionSource": self.post_info["versionSource"],
                    "versionTitle": self.post_info["versionTitle"]
                }
            post_text(ref, send_text)
        else:
            assert Ref(ref)
            tc = TextChunk(Ref(ref), lang=self.post_info["language"], vtitle=self.post_info["versionTitle"])
            tc.text = text
            tc.save()

    def parse(self, text_arr, footnotes):
        def extractIDsAndSupNums(text):
            ft_ids = []
            ft_sup_nums = []
            xrefs = BeautifulSoup.BeautifulSoup(text).findAll('xref')
            for xref in xrefs:
                ft_ids.append(xref['rid'])
                ft_sup_nums.append(xref.text)

            return ft_ids, ft_sup_nums

        def getPositions(text):
            pos = []
            all = re.findall('<sup><xref.*?>\d+</xref></sup>', text)
            for each in all:
                pos.append(text.find(each))
            return pos

        def buildFtnoteText(num, text):
            return u'<sup>{}</sup><i class="footnote">{}</i>'.format(num, text)

        #parse code begins...
        key_of_xref = 'rid'
        assert type(text_arr) is list
        ftnote_texts = []
        for index, text in enumerate(text_arr):
            text_arr[index] = text_arr[index].replace("<bold>", "<b>").replace("<italic>", "<i>").replace("</bold>", "</b>").replace("</italic>", "</i>")
            text_arr[index] = text_arr[index].replace("<li>", "<br>").replace("</li>", "")
            text_arr[index] = text_arr[index].replace("3465", "&lt;").replace("3467", "&gt;")

            ft_ids, ft_sup_nums = extractIDsAndSupNums(text_arr[index])

            ft_pos = getPositions(text_arr[index])

            assert len(ft_ids) == len(ft_sup_nums) == len(ft_pos)

            for i in range(len(ft_ids)):
                reverse_i = len(ft_ids) - i - 1
                ftnote_text = footnotes[ft_ids[reverse_i]]
                text_to_insert = buildFtnoteText(ft_sup_nums[reverse_i], ftnote_text)
                pos = ft_pos[reverse_i]
                text_arr[index] = u"{}{}{}".format(text_arr[index][0:pos], text_to_insert, text_arr[index][pos:])

            all = re.findall('<sup><xref.*?>\d+</xref></sup>', text_arr[index])
            for each in all:
                text_arr[index] = text_arr[index].replace(each, "")

        return text_arr

    def grab_title(self, element, delete=True, test_lambda=lambda x: False):
        '''
        Get the name return it and delete the first element
        '''
        if test_lambda(element):
            name = bleach.clean(element[0].text, strip=True)
            element.text = name
            if delete:
                element.remove(element[0])
            return name
        return ""


    def go_down_to_text(self, name, element):
        text = {}
        text["text"] = []
        text["subject"] = []
        for index, child in enumerate(element):
            if len(child) > 0:
                if child.tag != "title":
                    self.grab_title(child, delete=False, test_lambda=self.grab_title_lambda)
                    #above: take the title underneath, set it to text var,  so afterward, child.text will be the correct title
                if child.text.isdigit():
                    text["text"].append(self.go_down_to_text(child.text, child))
                else:
                    text[child.text] = self.go_down_to_text(child.text, child)
            else:
                if child.tag == "ftnote":
                    if "id" not in child.attrib:
                        assert len(self.prev_footnote) > 0
                        self.footnotes[self.prev_footnote] += "<br>" + child.xpath("string()")
                    else:
                        self.footnotes[child.attrib['id']] = child.xpath("string()")
                        self.prev_footnote = child.attrib['id']
                elif self.siblingsHaveChildren(element):
                    text["subject"] += [child.xpath("string()").replace("\n\n", " ")]
                else:
                    text["text"] += [child.xpath("string()").replace("\n\n", " ")]

        return text


    def siblingsHaveChildren(self, element):
        for index, child in enumerate(element):
            if len(child) > 0:
                print "Siblings have children: El {} has children".format(index)
                return True
        return False


    def convertManyIntoOne(self, ref):
        array = []
        for x in ref:
            if type(x) is dict:
                array.append(self.convertManyIntoOne(x['text']))
            else:
                array.append(x)
        if len(array) > 0 and type(array[0]) is not list:
            array = self.parse(array, self.footnotes)
        return array


    def interpret(self, node, running_ref, prev="string"):
        #assert Ref(running_ref), running_ref
        for key in node:
            if key != "text" and key != "subject":
                new_running_ref = "%s, %s" % (running_ref, key)
                #assert Ref(new_running_ref)
                self.interpret(node[key], new_running_ref, "string")
            elif key == "subject" and len(node[key]) > 0:
                #assert Ref(running_ref)
                new_running_ref = running_ref + ",_Subject"
                #assert Ref(new_running_ref)
                text = self.parse(node[key])
                self.post(new_running_ref, text)
        if len(node.keys()) == 2 and "text" in node.keys() and "subject" in node.keys() and len(node['text']) > 0:
            #assert Ref(running_ref)
            text = self.convertManyIntoOne(node["text"])
            print running_ref
            self.post(running_ref, text)


    def reorder_structure(self, element, move_footnotes=False):
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
        title = ""
        orig_length = len(element) - 1
        for index, child in enumerate(element):
            if self.reorder_test(child):
                child.text, title = (self.reorder_modify(child.text), child.text[3:])
                if next_will_be_children == True:
                    for new_child in children:
                        parent.append(new_child)
                    children = []
                parent = child
                next_will_be_children = True
            elif child.tag == "ftnote" and next_will_be_children:
                if move_footnotes:
                    children.append(child)
            elif next_will_be_children == True:
                if len(title) > 0:
                    child.text = "<b>" + title + "</b> " + child.text
                    title = ""
                children.append(child)

            if index == orig_length:
                for new_child in children:
                    parent.append(new_child)

        #for child in element:
        #    child = self.reorder_structure(child)

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


    def get_pages(self, text, ref):
        return text

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

'''