'''
How to convert XML tree into JaggedArray
User provides in order the names of the JaggedArrayNodes for the given text and the depths for each one.
Then
User gives a level of depth to go to and then xpath("string()") on that depth to return a jagged array of that depth. 
'''
import re

import bleach
import csv
from lxml import etree
from bs4 import BeautifulSoup, Tag
import PIL
from PIL import Image
from sefaria.helper.text import replace_roman_numerals
from num2words import *
from sources.functions import *
from sefaria.model import *
from base64 import b64decode, b64encode
from _collections import OrderedDict

class XML_to_JaggedArray:


    def __init__(self, title, xml_text, allowedTags, allowedAttributes, post_info=None,
                 dict_of_names={}, print_bool=False, array_of_names=[], deleteTitles=True,
                 change_name=False, assertions=False, image_dir=None, titled=False, remove_chapter=True,
                 versionInfo=[], use_fn=False, english=True):
        self.title = title
        self.writer = csv.writer(open("{}.csv".format(title), 'w'))
        self.post_info = post_info
        self.xml_text = xml_text
        self.parse_dict = {}
        self.allowedTags = allowedTags
        self.allowedAttributes = allowedAttributes
        self.result_dict = {}
        self.pages = {}
        self.alt_struct = True
        self.titled = titled
        self.footnotes = {}
        self.array_of_names = array_of_names
        self.dict_of_names = dict_of_names
        self.deleteTitles = deleteTitles
        self.prev_footnote = ""
        self.last_chapter = 0
        self.change_name = change_name
        self.assertions = assertions
        self.image_dir = image_dir #where to find images
        self.get_title_lambda = lambda el: el[0].text
        self.print_bool = print_bool
        self.footnotes_within_footnotes = {} #used in English Mishneh Torah translations for footnotes with Raavad being quoted
        self.word_to_num = WordsToNumbers()
        self.versionInfo = versionInfo
        self.remove_chapter_when_cleaning = remove_chapter
        self.word_count = 0
        self.use_fn = use_fn
        self.english = english

    def set_title(self, title):
        self.title = title

    def set_funcs(self, grab_title_lambda=lambda x: len(x) > 0 and x[0].tag in ["title", "h1", "h2"], reorder_test=lambda x: False,
                  reorder_modify=lambda x: x, modify_before_parse=lambda x: x, modify_before_post=lambda x: x, preparser=None):
        self.modify_before_parse = modify_before_parse
        self.grab_title_lambda = grab_title_lambda
        self.reorder_test = reorder_test
        self.reorder_modify = reorder_modify
        self.modify_before_post = modify_before_post
        self.preparser = preparser

    def convertIMGBase64(self, text):
        tags = re.findall("<img.*?>", text)
        for tag in tags:
            filename = BeautifulSoup(tag).findAll("img")[0]['src']
            filetype = filename.split(".")[1]
            img = Image.open("./" + filename)
            orig_height = img.size[1]
            orig_width = img.size[0]
            if orig_width > 550:
                percent = 550 / float(orig_width)
                height = int(float(orig_height) * float(percent))
                img = img.resize((550, height), PIL.Image.ANTIALIAS)
                img = img.save(filename)
            file = open("./{}".format(filename), 'rb')
            data = file.read()
            file.close()
            data = b64encode(data)
            new_tag = '<img src="data:image/{};base64,{}"></img>'.format(filetype, str(data)[2:-1])
            text = text.replace(tag, new_tag)
        return text

    def run(self):
        xml_text = self.xml_text
        #self.get_each_type_tag(BeautifulSoup(xml_text).contents)
        xml_text = self.modify_before_parse(xml_text)
        xml_text = bleach.clean(xml_text, tags=self.allowedTags, attributes=self.allowedAttributes, strip=False)
        xml_text = self.convertIMGBase64(xml_text)
        self.root = etree.XML(xml_text)

        self.root.text = self.title
        self.root = self.reorder_structure(self.root)

        if self.preparser:
            self.root = self.preparser(self.root)
        else:
            for count, child in enumerate(self.root):
                if self.array_of_names:
                    child.text = str(self.array_of_names[count])
                elif self.dict_of_names:
                    key = self.cleanNodeName(child[0].text)
                    child[0].text = self.dict_of_names[key]
                child = self.reorder_structure(child, False)

        results = self.go_down_to_text(self.root, self.root.text, True)
        #    results = self.handle_special_case(results)
        if self.print_bool:
            for row in self.versionInfo:
                self.writer.writerow(row)
        self.interpret_and_post(results, self.title)



    def move_title_to_first_segment(self, element):
        title = self.grab_title(element, delete=False, test_lambda=self.grab_title_lambda, change_name=False)
        if element[0].tag == "title":
            element[0].tag = "p"


    def get_each_type_tag(self, tags, root=True):
        tag_set = set()
        for tag in tags:
            if type(tag) is Tag:
                tag_set.add(tag.name)
                tags_below_me = self.get_each_type_tag(tag.contents, False)
                for each_tag in tags_below_me:
                    tag_set.add(each_tag)
        # if root:
        #     print("Set of tags not specified: {}".format(tag_set - set(self.allowedTags)))
        return tag_set

    def removeChapter(self, text):
        match = re.search("^(CHAPTER|chapter|Chapter|Part|PART) [a-zA-Z0-9]+(\.|\,|\:)?", text)
        if match:
            text = text.replace(match.group(1), "").strip()
        return text

    def cleanNodeName(self, text):
        if text.strip() == "":
            return ""
        text = self.cleanText(text)
        text = self.removeChapter(text)
        comma_chars = ['.']
        remove_chars = ['?']# + re.findall("[\u05D0-\u05EA]+", text)
        space_chars = ['-']
        while self.english and not any_english_in_str(text[-1]):
            text = text[0:-1]
        for char in comma_chars:
            if text.replace(char, " ").find("  "):
                text = text.replace(char, ",")
            else:
                text = text.replace(char, " ")
        for char in remove_chars:
            text = text.replace(char, "")
        for char in space_chars:
            text = text.replace(char, " ")
        text = bleach.clean(text, strip=True)
        if self.titled:
            text = make_title(text)
        return text

    def cleanText(self, text):
        things_to_replace = {"\xa0": ''}
        # things_to_replace = {
        #     '\xa0': '',
        #     '\u015b': 's',
        #     '\u2018': "'",
        #     '\u2019': "'",
        #     '\u05f4': '"',
        #     '\u201c': '"',
        #     '\u201d': '"',
        #     '\u1e93': 'z',
        #     '\u1e24': 'H'
        # }
        # if '\u201c' in text or chr(147) in text or "“" in text:
        #     for word in text.split():
        #         if'\u201c' in word or chr(147) in word or "“" in word:
        #             print('found')
        for key in things_to_replace:
            text = text.replace(key, things_to_replace[key])
        return text



    def getChildren(self, parent):
        titles = []
        for child in parent:
            titles.append(child.tag)
        return titles


    def write_text_to_file(self, ref, text):
        orig_ref = ref
        if type(text) is str or type(text) is str:
            self.word_count += self.cleanText(text).count(" ")
            text = self.cleanText(text)
            self.writer.writerow([ref, text])
        else:
            assert type(text) is list
            for count, element in enumerate(text):
                ref = "{}.{}".format(orig_ref, count+1)
                self.write_text_to_file(ref, element)


    def split_on_nums(self, text):
        lines = re.split("\d+\. ", text)
        lines = lines[1:]
        for count, line in enumerate(lines):
            lines[count] = "{}. {}".format(count+1, line)
        return lines

    def post(self, ref, text, not_last_key):
        text = self.modify_before_post(text)
        if self.print_bool:
            self.write_text_to_file(ref, text)
        elif self.post_info["server"] != "local":
            send_text = {
                    "text": text,
                    "language": self.post_info["language"],
                    "versionSource": self.post_info["versionSource"],
                    "versionTitle": self.post_info["versionTitle"]
                }
            if not_last_key:
                post_text(ref, send_text, server=self.post_info["server"])
            else:
                post_text(ref, send_text, server=self.post_info["server"], index_count="on")
        else:
            print("Not Posting....")
            assert Ref(ref)
            tc = TextChunk(Ref(ref), lang=self.post_info["language"], vtitle=self.post_info["versionTitle"])
            tc.text = text
            tc.save()

    def fix_html(self, line):
        line = line.replace("<bold>", "<b>").replace("<italic>", "<i>").replace("</bold>", "</b>").replace("</italic>", "</i>")
        line = line.replace("<li>", "<br>").replace("</li>", "")
        line = line.replace("</title>", "</b>").replace("<title>", "<b>")
        return line

    def parse(self, text_arr, footnotes, node_name):
        footnote_pattern = '<xref.*?>.*?</xref>'
        def extractIDsAndSupNums(text):
            ft_ids = []
            ft_sup_nums = []
            xrefs = re.findall(footnote_pattern, text) #BeautifulSoup("<p>"+text+"</p>").findAll("xref")
            xrefs = [BeautifulSoup("<p>"+text+"</p>").find("xref") for text in xrefs]
            for xref in xrefs:
                ft_ids.append(xref['rid'])
                ft_sup_nums.append(xref.text)

            return ft_ids, ft_sup_nums


        def getPositions(text):
            pos = []
            len_text_skipped = 0
            all = re.findall(footnote_pattern, text)
            for each in all:
                curr_pos = text.find(each)
                len_tag = len(each)
                absolute_pos = curr_pos+len_text_skipped
                pos.append(absolute_pos)
                text = text[curr_pos+len_tag:]
                len_text_skipped += curr_pos+len_tag
            return pos

        def removeNumberFromStart(text):
            if "Ibn Ezra" in node_name:
                return text
            if text[0].isdigit():
                return " ".join(text.split(" ")[1:])
            return text

        def buildFtnoteText(num, text, fn):
            sup_match = re.compile("^<sup>\d+</sup>").match(text)
            if sup_match:
                text = text.replace(sup_match.group(0), "")
            if text[0].isdigit():
                text = " ".join(text.split()[1:])
            if not self.use_fn:
                return '<sup>{}</sup><i class="footnote">{}</i>'.format(num, text)
            else:
                return '<sup>{}</sup><i class="footnote">{},{}</i>'.format(num, fn, text)

        #parse code begins...
        key_of_xref = 'rid'
        assert type(text_arr) is list
        ftnote_texts = []
        for index, text in enumerate(text_arr):
            if len(text) == 0:
                continue
            try:
                #text_arr[index] = removeNumberFromStart(text_arr[index])
                text_arr[index] = text_arr[index].replace("<sup><xref", "<xref").replace("</xref></sup>", "</xref>")
                ft_ids, ft_sup_nums = extractIDsAndSupNums(text_arr[index])

                ft_pos = getPositions(text_arr[index])

                assert len(ft_ids) == len(ft_sup_nums) == len(ft_pos), "id={},sups={},pos={},index={}".format(ft_ids, ft_sup_nums, ft_pos, index)

                footnotes_to_use = {}
                for x in footnotes.values():
                    footnotes_to_use.update(x)

                for i in range(len(ft_ids)):
                    reverse_i = len(ft_ids) - i - 1
                    ftnote_text = footnotes_to_use[ft_ids[reverse_i]]
                    text_to_insert = buildFtnoteText(ft_sup_nums[reverse_i], ftnote_text, ft_ids[reverse_i])
                    pos = ft_pos[reverse_i]
                    modified_text = u"{}{}{}".format(text_arr[index][0:pos], text_to_insert, text_arr[index][pos:])
                    text_arr[index] = modified_text

                all = re.findall(footnote_pattern, text_arr[index])
                for each in all:
                    text_arr[index] = text_arr[index].replace(each, "")


                text_arr[index] = self.fix_html(text_arr[index])
            except (IndexError, AttributeError) as e:
                if text_arr:
                    print(node_name)
                    # if isinstance(text_arr[0], unicode):
                    #     print "No chapter tag at the beginning"
                    # if isinstance(text_arr[-1], unicode):
                    #     print "No chapter tag at the end"
                    # if isinstance(text_arr[0], list) and isinstance(text_arr[-1], list):
                    #     print "No chapter tag somewhere in the middle"
                text_arr = []
        return text_arr


    def grab_title(self, element, delete=True, test_lambda=lambda x: False, change_name=True):
        '''
        Get the name return it and delete the first element
        '''
        if test_lambda(element):
            name = element[0].text
            ftnotes = re.findall("<sup>.*?</sup>", name)
            for ftnote in ftnotes:
                name = name.replace(ftnote, "")
            name = bleach.clean(name, strip=True)
            if change_name:
                element.text = name
            if delete:
                element.remove(element[0])
            return name
        return ""


    def fix_ol(self, element):
        text = element.xpath("string()")
        if text[0] == "\n":
            text = text[1:]

        text_arr = text.splitlines()
        for i, line in enumerate(text_arr):
            text_arr[i] = "{}. {}".format(i+1, line)
            text_arr[i] = text_arr[i].replace("<li>", "").replace("</li>", "").replace("<p>", "<br>")


        element.text = "<br>".join(text_arr)
        for child in element:
            element.remove(child)
        return element


    def print_table_info(self, element, index):
        print("{}, {}.{}".format(self.title, element.text, index))


    def handle_special_tags(self, element, child, index):
        if child.tag == "ol":
            child = self.fix_ol(child)
        elif child.tag == "table":
            self.print_table_info(element, index)
        elif child.tag == "volume":
            pass
        elif child.tag == "chapter" and child.text.startswith("CHAPITRE"):
            child.text = child.text.replace("PREMIER", "I").replace(".", "").strip()
            child.text = str(roman_to_int(child.text.split()[-1]))
        # if child.tag == "h1" and self.title == "Teshuvot Maharam":
        #     child.text = re.sub(" \(D.*?\)", "", child.text)
        elif child.tag in ["chapter"] and "CHAPTER " in child.text.upper():# and len(child.text.split(" ")) <= 3:
            tags = re.findall("<sup>.*?</sup>", child.text)
            if len(child.text.split()) == 2:
                child.text = child.text.split()[-1]
                #child.text = str(roman_to_int(child.text.split()[-1]))
            #child.text = str(self.word_to_num.parse(child.text.split(" ")[-1])) #  Chapter Two => 2

    def go_down_to_text(self, element, parent, element_is_root=False):
        text = OrderedDict() if element_is_root else {}
        text["text"] = []
        text["subject"] = []
        prev_footnote = False #need this flag for when footnote is broken up into ftnote tags and p tags
        still_titles = False #need this flag so that the headers and titles at the beginning of a section
                             #do not get their own segment but are attached to the beginning of the first paragraph

        for index, child in enumerate(element):
            self.handle_special_tags(element, child, index)
            if len(child) > 0:
                if child.text is None:
                    assert child[0].tag == "img"
                    img_src = child[0].attrib["src"]
                    text["text"].append("<img src='{}' />".format(img_src))
                elif child.text.isdigit():
                    while int(child.text) > len(text["text"]) + 1:
                        text["text"].append({"text": []})
                    text["text"].append(self.go_down_to_text(child, element))
                else:
                    child.text = self.cleanNodeName(child.text)
                    text[child.text] = self.go_down_to_text(child, element)
            else:
                if child.tag == "ftnote" or prev_footnote:
                    self.add_footnote(parent, element, child)
                    prev_footnote = True
                # elif self.siblingsHaveChildren(element) > 0:
                #     self.siblingsHaveChildren(element)
                #     text["subject"] += [self.cleanText(child.xpath("string()").replace("\n\n", " "))]
                else:
                    if index == 0 and (child.tag == "title" or child.tag == "h1"):
                        still_titles = True
                        text['text'] = [""]
                    if still_titles and (child.tag == "title" or child.tag == "h1"):
                        text["text"][-1] += self.cleanText(child.xpath("string()").replace("\n\n", " ")) + "<br/>"
                    elif still_titles:
                        still_titles = False
                        text["text"][-1] += self.cleanText(child.xpath("string()").replace("\n\n", " "))
                    else:
                        new_line = self.cleanText(child.xpath("string()").replace("\n\n", " "))
                        if re.search("h\d+", child.tag):
                            new_line = "<b>"+new_line+"</b>"
                        text["text"] += [new_line]
        return text


    def add_footnote(self, parent, element, child):
        xpath_result = str(child.xpath("string()"))
        if element.text.isdigit():
            key = parent.text + " " + element.text
        else:
            key = element.text
        if key not in self.footnotes:
            self.footnotes[key] = {}
        if "id" not in child.attrib:
            assert len(self.prev_footnote) > 0 and len(self.footnotes[key]) > 0
            self.footnotes[key][self.prev_footnote] += "<br>" + xpath_result
        else:
            child_id = child.attrib['id']
            if self.title == "Pirkei DeRabbi Eliezer" and element.text == '10':
                child_id = "fn" + str(int(child_id[2:]) - 1)
            self.footnotes[key][child_id] = xpath_result
            self.prev_footnote = child_id


    def siblingsHaveChildren(self, element):
        len_first = len(element[0])
        for index, child in enumerate(element):
            if index > 0 and len(child) != len_first:
                return index
        return 0


    def convertManyIntoOne(self, text, node_name):
        array = []
        prev_num = 0
        found_any_numbers = False
        num_dicts_found = 0
        for count, x in enumerate(text):
            if type(x) is dict:
                num_dicts_found += 1
                array.append(self.convertManyIntoOne(x['text'], "{} {}".format(node_name, num_dicts_found)))
            else:
                # num_and_text = re.search("^(\d+)\.? (.*?)$", x)
                # if num_and_text:
                #     found_any_numbers = True
                #     num = int(num_and_text.group(1))
                #     for i in range(num-prev_num-1):
                #         array.append("")
                #     if num <= prev_num:
                #         raise AssertionError
                #     prev_num = num
                #     text = num_and_text.group(2)
                #     array.append(text)
                # elif not array:
                #     array.append(x)
                # elif not x[0].isdigit() and found_any_numbers:
                #     array[-1] += u"<br/>{}".format(x)
                # else:
                array.append(x)


        if len(array) > 1 and not isinstance(array[0], list) and isinstance(array[1], list): #array[0] is title
            array = array[1:]

        if len(array) > 0 and type(array[0]) is not list: #not list in other words string or unicode
            #array = self.pre_parse(array, node_name)
            array = self.parse(array, self.footnotes, node_name)
            self.any_problems(array, node_name)
        return array

    def any_problems(self, array, node_name):
        found = False
        for x in array:
            if "xref" in x:
                found = True
                print(x)
        # if found:
        #     print("PROBLEM IN")
        #     print(node_name)

    def pre_parse(self, text_arr, node_name):
        p = re.compile("(\d+)[\)|\s+\)]+")
        content = []
        prev = 1
        found_blockquote = 0
        multiple_numbering = 0
        lines_with_no_small_or_numbers = 0 #dont fit into either scheme
        found = []
        prev_had_number = False
        # If number already exists, don't remove it and append it to prev number
        intro_text = ""
        for count, line in enumerate(text_arr):
            matches = re.findall("^\d+[\)|\s+\)]+", line)
            if len(matches) >= 1:
                assert not "<small>" in line
                if matches[0] not in found:
                    match = matches[0]
                    found.append(match)
                    content.append(line.replace(match, "", 1))
                else:
                    #this is not an actual numbered comment since the number already appeared, we can assume
                    content.append(line)
                    multiple_numbering += 1
                if intro_text:
                    content[-1] = intro_text + "<br>" + content[-1]
                    intro_text = ""
            elif len(matches) == 0:
                found_blockquote += 1
                if "<small>" not in line and not line.startswith("Preface"):
                    lines_with_no_small_or_numbers += 1
                if len(content) > 0:
                    #this is when an intro to a segment occurs in the middle of a chapter
                    if intro_text:
                        intro_text += "<br>"
                    intro_text += line
                else:
                    #this is when intro is first paragraph of chapter
                    intro_text += line
        still_has_intro_text = intro_text != "" # intro_text should have been inserted into a comment

        if still_has_intro_text:
            print("{} still has intro text.".format(node_name))
        if multiple_numbering:
            print("{} now has {} paragraphs that have multiple numbers".format(node_name, multiple_numbering))
        if found_blockquote:
            print("{} now has {} paragraphs that are small".format(node_name, found_blockquote))
        if lines_with_no_small_or_numbers:
            print("{} now has {} paragraphs that are not small or numbered".format(node_name, lines_with_no_small_or_numbers))
        return content



    def interpret_and_post(self, node, running_ref, prev="string"):
        if self.assertions:
            assert Ref(running_ref), running_ref
        not_last_key = True
        for i, key in enumerate(node.keys()):
            if key == '\n':
                continue

            if key != "text" and key != "subject":
                new_running_ref = "%s, %s" % (running_ref, key)
                if self.assertions:
                    assert Ref(new_running_ref)
                self.interpret_and_post(node[key], new_running_ref, "string")

            elif key == "subject" and len(node[key]) > 0:
                if self.assertions:
                    assert Ref(running_ref)
                new_running_ref = running_ref + ",_Prelude"
                if self.assertions:
                    assert Ref(new_running_ref)
                #text = self.parse(node[key], self.footnotes, )
                #self.post(new_running_ref, text, not_last_key)

            elif key == "text" and len(node[key]) > 0: #if len(node.keys()) == 2 and "text" in node.keys() and "subject" in node.keys() and len(node['text']) > 0:
                if self.assertions:
                    assert Ref(running_ref)
                text = self.convertManyIntoOne(node["text"], running_ref.rsplit(", ", 1)[-1])
                self.post(running_ref, text, not_last_key)

    def handle_special_case(self, results):
        #normalize dictionary keys to be Parsha names
        torah_book = self.title.split(" ")[-1]
        torah_book = library.get_index(torah_book)
        parshiot_dicts = torah_book.alt_structs["Parasha"]["nodes"]
        parshiot = [el["sharedTitle"] for el in parshiot_dicts]
        old_results = dict(results)
        for parsha in list(results.keys()):
            parsha = parsha.decode('utf-8')
            if parsha in parshiot:
                continue
            match = find_almost_identical(parsha, parshiot)
            if match:
                results[match] = results[parsha]
            results.pop(parsha, None)

        #create an array that goes in order instead of an unordered dictionary
        parshiot_in_order = {"text": []}
        for parsha_dict in parshiot_dicts:
            parsha_title = parsha_dict["sharedTitle"]
            for line in results[parsha_title]["text"]:
                parshiot_in_order["text"].append(line)

        #structure into depth 3
        text_dict = {}
        for line in parshiot_in_order["text"]:
            orig_line = line
            if line.startswith("<bold>"):
                perek_and_verse = re.findall("<bold>(\d+,\d+\.?).*?</bold>", line)
                assert len(perek_and_verse) in [0,1]
                if len(perek_and_verse) == 1:
                    perek, verse = perek_and_verse[0].replace(".", "").split(",")
                    perek = int(perek)
                    verse = int(verse)
                    if perek not in list(text_dict.keys()):
                        text_dict[perek] = {}
                    if verse not in list(text_dict[perek].keys()):
                        text_dict[perek][verse] = []
                    line = line.replace(perek_and_verse[0], "")
            if line[0] == " ":
                line = line[1:]
            line = self.fix_html(line)
            text_dict[perek][verse].append(line)

        for perek in list(text_dict.keys()):
            text_dict[perek] = convertDictToArray(text_dict[perek])
        text_arr = convertDictToArray(text_dict)

        parshiot_in_order["text"] = text_arr
        return parshiot_in_order






    def temp_func(self, text):
        for x, ch in enumerate(text):
            for y, line in enumerate(ch):
                text[x][y] = [ch[y]]
        return text


    def reorder_structure(self, element, move_footnotes=False, recurse_times=0):
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
        change_name = self.array_of_names == [] #because name was already changed if self.array_of_names has any contents
        if element.text and element.text.isdigit():
            change_name = False
        self.grab_title(element, delete=self.deleteTitles, test_lambda=self.grab_title_lambda, change_name=change_name)
        for index, child in enumerate(element):
            if self.reorder_test(child):
                if len(child) == 1:
                    child.text = child[0].text
                    child.remove(child[0])
                child.text = self.reorder_modify(child.text)
                if next_will_be_children is True:
                    for new_child in children:
                        if len(new_child) > 0:
                            new_child = self.reorder_structure(new_child, move_footnotes)
                        parent.append(new_child)
                    children = []
                parent = child
                next_will_be_children = True
            elif child.tag == "ftnote" and next_will_be_children:
                if move_footnotes:
                    children.append(child)
            elif next_will_be_children == True:
                if self.title == "Midrash Tanchuma" and len(title) > 0:
                    # EITHER PUT </b> at end of child.text;
                    # Just do replace <sup> with </b><sup> and </sup> with </sup><b>
                    title = title.replace("<sup>", "</b><sup>").replace("</sup>", "</sup><b>")
                    p = re.compile("^<bold>([A-Z\.]+)</bold>")
                    if p.match(child.text):
                        first_letter = p.match(child.text).group(1)
                        letter_with_tags = p.match(child.text).group(0)
                        child.text = child.text.replace(letter_with_tags, first_letter)
                    child.text = "<b>" + title + "</b> " + child.text
                    title = ""
                children.append(child)
            elif len(child) > 0:
                child = self.reorder_structure(child, move_footnotes)

        for new_child in children:
            if len(new_child) > 0:
                new_child = self.reorder_structure(new_child, move_footnotes)
            parent.append(new_child)


        return element





def roman_to_int(input):
   """
   Convert a roman numeral to an integer.

   >>> r = range(1, 4000)
   >>> nums = [int_to_roman(i) for i in r]
   >>> ints = [roman_to_int(n) for n in nums]
   >>> print r == ints
   1

   >>> roman_to_int('VVVIV')
   Traceback (most recent call last):
    ...
   ValueError: input is not a valid roman numeral: VVVIV
   >>> roman_to_int(1)
   Traceback (most recent call last):
    ...
   TypeError: expected string, got <type 'int'>
   >>> roman_to_int('a')
   Traceback (most recent call last):
    ...
   ValueError: input is not a valid roman numeral: A
   >>> roman_to_int('IL')
   Traceback (most recent call last):
    ...
   ValueError: input is not a valid roman numeral: IL
   """
   if type(input) != type(""):
      raise TypeError("expected string, got %s" % type(input))
   input = input.upper()
   nums = ['M', 'D', 'C', 'L', 'X', 'V', 'I']
   input = "".join([i for i in input if i in nums])
   ints = [1000, 500, 100, 50,  10,  5,   1]
   places = []
   for c in input:
      if not c in nums:
         raise ValueError("input is not a valid roman numeral: %s" % input)
   for i in range(len(input)):
      c = input[i]
      value = ints[nums.index(c)]
      # If the next place holds a larger number, this value is negative.
      try:
         nextvalue = ints[nums.index(input[i +1])]
         if nextvalue > value:
            value *= -1
      except IndexError:
         # there is no next place.
         pass
      places.append(value)
   sum = 0
   for n in places: sum += n
   # Easiest test for validity...
   if int_to_roman(sum) == input:
      return sum
   else:
      raise ValueError('input is not a valid roman numeral: %s' % input)

def int_to_roman(input):
   """
   Convert an integer to Roman numerals.

   Examples:
   >>> int_to_roman(0)
   Traceback (most recent call last):
   ValueError: Argument must be between 1 and 3999

   >>> int_to_roman(-1)
   Traceback (most recent call last):
   ValueError: Argument must be between 1 and 3999

   >>> int_to_roman(1.5)
   Traceback (most recent call last):
   TypeError: expected integer, got <type 'float'>

   >>> for i in range(1, 21): print int_to_roman(i)
   ...
   I
   II
   III
   IV
   V
   VI
   VII
   VIII
   IX
   X
   XI
   XII
   XIII
   XIV
   XV
   XVI
   XVII
   XVIII
   XIX
   XX
   >>> print int_to_roman(2000)
   MM
   >>> print int_to_roman(1999)
   MCMXCIX
   """
   if type(input) != type(1):
      raise TypeError("expected integer, got %s" % type(input))
   if not 0 < input < 4000:
      raise ValueError("Argument must be between 1 and 3999")
   ints = (1000, 900,  500, 400, 100,  90, 50,  40, 10,  9,   5,  4,   1)
   nums = ('M',  'CM', 'D', 'CD','C', 'XC','L','XL','X','IX','V','IV','I')
   result = ""
   for i in range(len(ints)):
      count = int(input / ints[i])
      result += nums[i] * count
      input -= ints[i] * count
   return result

