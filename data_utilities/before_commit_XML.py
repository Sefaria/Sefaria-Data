'''
How to convert XML tree into JaggedArray
User provides in order the names of the JaggedArrayNodes for the given text and the depths for each one.
Then
User gives a level of depth to go to and then xpath("string()") on that depth to return a jagged array of that depth.
'''
import bleach
from lxml import etree
from sources.functions import *
from sefaria.model import *
import re
from BeautifulSoup import BeautifulSoup

class XML_to_JaggedArray:


    def __init__(self, title, file, allowedTags, allowedAttributes, post_info, array_of_names=[], deleteTitles=True, change_name=False, assertions=False, image_dir=None):
        self.title = title
        self.post_info = post_info
        self.file = file
        self.parse_dict = {}
        self.allowedTags = allowedTags
        self.allowedAttributes = allowedAttributes
        self.result_dict = {}
        self.pages = {}
        self.alt_struct = True
        self.footnotes = {}
        self.array_of_names = array_of_names
        self.deleteTitles = deleteTitles
        self.prev_footnote = ""
        self.change_name = change_name
        self.assertions = assertions
        self.image_dir = image_dir


    def set_title(self, title):
        self.title = title

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
            if self.array_of_names:
                child.text = str(self.array_of_names[count])

            child = self.reorder_structure(child, False)

        results = self.go_down_to_text(self.root)
        self.interpret_and_post(results, self.title)


    def cleanNodeName(self, text):
        text = bleach.clean(text, strip=True)
        bad_chars = [".", ",", "'", '"']
        for bad_char in bad_chars:
            text = text.replace(bad_char, "")
            " ".join(text.split())
        return text.title()



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
            print "Not Posting...."
            assert Ref(ref)
            tc = TextChunk(Ref(ref), lang=self.post_info["language"], vtitle=self.post_info["versionTitle"])
            tc.text = text
            tc.save()

    def parse(self, text_arr, footnotes):
        footnote_pattern = '<xref.*?>.*?</xref>'
        def extractIDsAndSupNums(text):
            ft_ids = []
            ft_sup_nums = []
            xrefs = BeautifulSoup(text).findAll('xref')
            for xref in xrefs:
                ft_ids.append(xref['rid'])
                ft_sup_nums.append(xref.text)

            return ft_ids, ft_sup_nums

        def getPositions(text):
            pos = []
            all = re.findall(footnote_pattern, text)
            for each in all:
                pos.append(text.find(each))
            return pos

        def removeNumberFromStart(text):
            if text[0].isdigit():
                return " ".join(text.split(" ")[1:])
            return text

        def buildFtnoteText(num, text):
            text = text.replace("<sup>", "").replace("</sup>", "")
            if text[0].isdigit():
                text = " ".join(text.split()[1:])
            return u'<sup>{}</sup><i class="footnote">{}</i>'.format(num, text)

        def convertIMGBase64(text):
            tags = re.findall("<img.*?>", text)
            for tag in tags:
                filename = BeautifulSoup(tag).findAll("img")[0]['src']
                filetype = filename.split(".")[1]
                file = open("./{}".format(filename))
                data = file.read()
                file.close()
                data = data.encode("base64")
                new_tag = '<img src="data:image/{};base64,{}">'.format(filetype, data)
                text = text.replace(tag, new_tag)
            return text

        #parse code begins...
        key_of_xref = 'rid'
        assert type(text_arr) is list
        ftnote_texts = []
        for index, text in enumerate(text_arr):
            text_arr[index] = removeNumberFromStart(text_arr[index])
            text_arr[index] = text_arr[index].replace("<sup><xref", "<xref").replace("</xref></sup>", "</xref>")
            ft_ids, ft_sup_nums = extractIDsAndSupNums(text_arr[index])

            ft_pos = getPositions(text_arr[index])

            assert len(ft_ids) == len(ft_sup_nums) == len(ft_pos), "id={},sups={},pos={},index={}".format(ft_ids, ft_sup_nums, ft_pos, index)

            for i in range(len(ft_ids)):
                reverse_i = len(ft_ids) - i - 1
                ftnote_text = footnotes[ft_ids[reverse_i]]
                text_to_insert = buildFtnoteText(ft_sup_nums[reverse_i], ftnote_text)
                pos = ft_pos[reverse_i]
                text_arr[index] = u"{}{}{}".format(text_arr[index][0:pos], text_to_insert, text_arr[index][pos:])

            all = re.findall(footnote_pattern, text_arr[index])
            for each in all:
                text_arr[index] = text_arr[index].replace(each, "")
            text_arr[index] = text_arr[index].replace("<bold>", "<b>").replace("<italic>", "<i>").replace("</bold>", "</b>").replace("</italic>", "</i>")
            text_arr[index] = text_arr[index].replace("<li>", "<br>").replace("</li>", "")
            text_arr[index] = text_arr[index].replace("</title>", "</b>").replace("<title>", "<b>")
            text_arr[index] = convertIMGBase64(text_arr[index])


        return text_arr

    def grab_title(self, element, delete=True, test_lambda=lambda x: False, change_name=True):
        '''
        Get the name return it and delete the first element
        '''
        if test_lambda(element):
            name = bleach.clean(element[0].text, strip=True)
            if change_name:
                element.text = name
            if delete:
                element.remove(element[0])
            return name
        return ""


    def go_down_to_text(self, element):
        text = {}
        text["text"] = []
        text["subject"] = []
        for index, child in enumerate(element):
            if len(child) > 0:
                if child.text.isdigit():
                    if child.tag != "title":
                        self.grab_title(child, delete=self.deleteTitles, test_lambda=self.grab_title_lambda, change_name=False)
                    text["text"].append(self.go_down_to_text(child))
                else:
                    if child.tag != "title":
                        self.grab_title(child, delete=self.deleteTitles, test_lambda=self.grab_title_lambda, change_name=self.change_name)
                    child.text = self.cleanNodeName(child.text)
                    text[child.text] = self.go_down_to_text(child)
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


    def interpret_and_post(self, node, running_ref, prev="string"):
        if self.assertions:
            assert Ref(running_ref), running_ref
        for key in node:
            if key != "text" and key != "subject":
                new_running_ref = "%s, %s" % (running_ref, key)
                if self.assertions:
                    assert Ref(new_running_ref)
                self.interpret_and_post(node[key], new_running_ref, "string")
            elif key == "subject" and len(node[key]) > 0:
                continue
                if self.assertions:
                    assert Ref(running_ref)
                new_running_ref = running_ref + ",_Subject"
                if self.assertions:
                    assert Ref(new_running_ref)
                text = self.parse(node[key])
                self.post(new_running_ref, text)
            elif key == "text" and len(node[key]) > 0: #if len(node.keys()) == 2 and "text" in node.keys() and "subject" in node.keys() and len(node['text']) > 0:
                if self.assertions:
                    assert Ref(running_ref)
                text = self.convertManyIntoOne(node["text"])
                if ref == "Ibn Ezra on Isaiah":
                    pass
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
                child.text = self.reorder_modify(child.text)
                if next_will_be_children == True:
                    for new_child in children:
                        new_child = self.reorder_structure(new_child)
                        parent.append(new_child)
                    children = []
                parent = child
                next_will_be_children = True
            elif child.tag == "ftnote" and next_will_be_children:
                if move_footnotes:
                    children.append(child)
            elif next_will_be_children == True:
                children.append(child)

            if index == orig_length:
                for new_child in children:
                    new_child = self.reorder_structure(new_child)
                    parent.append(new_child)

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