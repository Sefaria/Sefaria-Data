'''
How to convert XML tree into JaggedArray
User provides in order the names of the JaggedArrayNodes for the given text and the depths for each one.
Then
User gives a level of depth to go to and then xpath("string()") on that depth to return a jagged array of that depth. 
'''
import re

import bleach
from lxml import etree
from BeautifulSoup import BeautifulSoup, Tag
import PIL
from PIL import Image
from sefaria.helper.text import replace_roman_numerals
from num2words import *
from sources.functions import *
from sefaria.model import *


class XML_to_JaggedArray:


    def __init__(self, title, file, allowedTags, allowedAttributes, post_info=None, dict_of_names={}, print_bool=False, array_of_names=[], deleteTitles=True, change_name=False, assertions=False, image_dir=None, titled=False):
        self.title = title
        self.writer = UnicodeWriter(open("{}.csv".format(file.split(".")[0]), 'w'))
        self.post_info = post_info
        self.file = file
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
        self.print_bool = print_bool #print results to CSV file
        self.footnotes_within_footnotes = {} #used in English Mishneh Torah translations for footnotes with Raavad being quoted
        self.word_to_num = WordsToNumbers()

    def set_title(self, title):
        self.title = title

    def set_funcs(self, grab_title_lambda=lambda x: len(x) > 0 and x[0].tag == "title", reorder_test=lambda x: False,
                  reorder_modify=lambda x: x, modify_before_parse=lambda x: x, modify_before_post=lambda x: x):
        self.modify_before_parse = modify_before_parse
        self.grab_title_lambda = grab_title_lambda
        self.reorder_test = reorder_test
        self.reorder_modify = reorder_modify
        self.modify_before_post = modify_before_post


    def run(self):
        xml_text = ""
        print self.title
        digit = re.compile(u"<p>\d+. ")
        chapter = re.compile(u"<title>CHAPTER")
        prev_line_ch = False
        prev_line = ""
        ch_line = ""
        for line in open(self.file):
            xml_text += line
            if chapter.match(line):
                prev_line_ch = True
                ch_line = line
            else:
                prev_line_ch = False
            prev_line = line

        self.get_each_type_tag(BeautifulSoup(xml_text).contents)
        xml_text = self.modify_before_parse(xml_text)
        xml_text = bleach.clean(xml_text, tags=self.allowedTags, attributes=self.allowedAttributes, strip=False)
        self.root = etree.XML(xml_text)

        self.root.text = self.title

        for count, child in enumerate(self.root):
            if self.array_of_names:
                child.text = str(self.array_of_names[count])
            elif self.dict_of_names:
                key = self.cleanNodeName(child[0].text)
                child[0].text = self.dict_of_names[key]
            child = self.reorder_structure(child, False)

        results = self.go_down_to_text(self.root, self.root.text)
        #    results = self.handle_special_case(results)
        self.interpret_and_post(results, self.title)
        self.record_results_to_file()


    def record_results_to_file(self):
        if "Glazer" in self.title:
            f = open("Raavad.csv", 'w')

            writer = UnicodeWriter(f, encoding='utf-8')
            for chapter in self.footnotes_within_footnotes.keys():
                for comment in self.footnotes_within_footnotes[chapter]:
                    try:
                        chapter = chapter.decode('utf-8')
                        comment = comment.decode('utf-8')
                    except UnicodeEncodeError:
                        pass
                    writer.writerow([chapter, comment])


    def process_footnote_for_MT(self, comment_text, chapter, ftnote_text, ftnote_key):
        '''
        check if it has quotes,
        if it does, return modified text without footnote in it and a bool value saying no_footnote
        if no_footnote isn't true,
        proceed as usual
        '''
        actual_footnote = True
        orig_ftnote_text = ftnote_text
        ftnote_text = self.cleanText(ftnote_text)
        if ftnote_text.find('</sup>"') > 0:
            actual_footnote = False
            #remove footnote from dictionary
            self.footnotes[chapter].pop(ftnote_key)

            #remove footnote from text
            ftnote_xref_in_comment = re.compile(".*?(<xref rid=\"{}\">.*?</xref>)".format(ftnote_key)).match(comment_text)
            assert ftnote_xref_in_comment
            comment_text = comment_text.replace(ftnote_xref_in_comment.group(1), "")

            #format footnote text right by removing <sup> and
            #checking for comment on footnote that will become a footnote in turn
            # and save it in footnotes_within_footnotes

            raavad = re.compile('<sup>.*?</sup>(\".*?\"\.?)').match(ftnote_text)
            if not raavad:  #if not a normal raavad match, it should be the one exception that is still raavad
                            #namely, having only one quotation mark
                assert len(ftnote_text.split('"')) == 2
                #print "ONLY ONE QUOTATION MARK:"
                #print ftnote_text
                pos_start = ftnote_text.find('"')
                if chapter not in self.footnotes_within_footnotes:
                    self.footnotes_within_footnotes[chapter] = []
                self.footnotes_within_footnotes[chapter].append(ftnote_text[pos_start:])
                return comment_text, actual_footnote
            else:
                raavad = raavad.group(1)
                comm_raavad_pos = ftnote_text.find(raavad) + len(raavad)
                comm_raavad = ftnote_text[comm_raavad_pos:]
                if len(comm_raavad) > 0:
                    #if '"' in comm_raavad and len(comm_raavad.split('"')) % 2 == 0:
                    #    print "EXTRA QUOTATION MARK:"
                    #    print comm_raavad
                    raavad = u"{}<sup>*</sup><i class='footnote'>{}</i>".format(raavad, comm_raavad)

                if chapter not in self.footnotes_within_footnotes:
                    self.footnotes_within_footnotes[chapter] = []
                self.footnotes_within_footnotes[chapter].append(raavad)

        return comment_text, actual_footnote



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
        if root:
            print "Set of tags not specified: {}".format(tag_set - set(self.allowedTags))
        return tag_set

    def removeChapter(self, text):
        match = re.search("^(CHAPTER|chapter|Chapter) [a-zA-Z0-9]{1,5}(\.|\,)?", text)
        if match:
            text = text.replace(match.group(0), "").strip()
        return text

    def cleanNodeName(self, text):
        if text == "\n":
            return text
        text = self.cleanText(text)
        text = self.removeChapter(text)
        comma_chars = ['.']
        remove_chars = ['?'] + re.findall(u"[\u05D0-\u05EA]+", text)
        space_chars = ['-']
        while not any_english_in_str(text[-1]):
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
        things_to_replace = {
            u'\xa0': u'',
            u'\u015b': u's',
            u'\u2018': u"'",
            u'\u2019': u"'",
            u'\u05f4': u'"',
            u'\u201c': u'"',
            u'\u201d': u'"',
            u'\u1e93': u'z',
            u'\u1e24': u'H'
        }
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
        if type(text) is str or type(text) is unicode:
            try:
                text = text.decode('utf-8')
            except UnicodeEncodeError:
                pass
            self.writer.writerow([ref, self.cleanText(text)])
        else:
            assert type(text) is list
            for count, element in enumerate(text):
                ref = u"{}.{}".format(orig_ref, count+1)
                self.write_text_to_file(ref, element)


    def split_on_nums(self, text):
        lines = re.split("\d+\. ", text)
        lines = lines[1:]
        for count, line in enumerate(lines):
            lines[count] = u"{}. {}".format(count+1, line)
        return lines

    def post(self, ref, text, not_last_key):
        text = self.modify_before_post(text)
        if self.print_bool:
            self.write_text_to_file(ref, text)
            self.writer.stream.close()
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
            print "Not Posting...."
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
            xrefs = BeautifulSoup(text).findAll('xref')
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
            if text[0].isdigit():
                return " ".join(text.split(" ")[1:])
            return text

        def buildFtnoteText(num, text):
            sup_match = re.compile("^<sup>\d+</sup>").match(text)
            if sup_match:
                text = text.replace(sup_match.group(0), "")
            if text[0].isdigit():
                text = " ".join(text.split()[1:])
            return u'<sup>{}</sup><i class="footnote">{}</i>'.format(num, text)

        def convertIMGBase64(text):
            tags = re.findall("<img.*?>", text)
            for tag in tags:
                filename = BeautifulSoup(tag).findAll("img")[0]['src']
                filetype = filename.split(".")[1]
                img = Image.open("./"+filename)
                orig_height = img.size[1]
                orig_width = img.size[0]
                if orig_width > 550:
                    percent = 550 / float(orig_width)
                    height = int(float(orig_height) * float(percent))
                    img = img.resize((550, height), PIL.Image.ANTIALIAS)
                    img = img.save(filename)
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
            if len(text) == 0:
                continue
            text_arr[index] = removeNumberFromStart(text_arr[index])
            text_arr[index] = text_arr[index].replace("<sup><xref", "<xref").replace("</xref></sup>", "</xref>")
            ft_ids, ft_sup_nums = extractIDsAndSupNums(text_arr[index])

            ft_pos = getPositions(text_arr[index])

            assert len(ft_ids) == len(ft_sup_nums) == len(ft_pos), "id={},sups={},pos={},index={}".format(ft_ids, ft_sup_nums, ft_pos, index)

            if node_name in footnotes.keys():
                for i in range(len(ft_ids)):
                    reverse_i = len(ft_ids) - i - 1
                    ftnote_text = footnotes[node_name][ft_ids[reverse_i]]
                    text_to_insert = buildFtnoteText(ft_sup_nums[reverse_i], ftnote_text)
                    pos = ft_pos[reverse_i]
                    modified_text = u"{}{}{}".format(text_arr[index][0:pos], text_to_insert, text_arr[index][pos:])
                    text_arr[index] = modified_text

                all = re.findall(footnote_pattern, text_arr[index])
                for each in all:
                    text_arr[index] = text_arr[index].replace(each, "")

            text_arr[index] = self.fix_html(text_arr[index])
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
            text_arr[i] = u"{}. {}".format(i+1, line)
            text_arr[i] = text_arr[i].replace("<li>", "").replace("</li>", "").replace("<p>", "<br>")


        element.text = "<br>".join(text_arr)
        for child in element:
            element.remove(child)
        return element


    def print_table_info(self, element, index):
        print "{}, {}.{}".format(self.title, element.text, index)


    def handle_special_tags(self, element, child, index):
        if child.tag == "ol":
            child = self.fix_ol(child)
        if child.tag == "table":
            self.print_table_info(element, index)
        if child.tag in ["chapter"] and "CHAPTER " in child.text.upper():# and len(child.text.split(" ")) <= 3:
            tags = re.findall("<sup>.*?</sup>", child.text)
            for tag in tags:
                child.text = child.text.replace(tag, "")
            child.text = str(child.text.split(" ")[1])
            #child.text = str(roman_to_int(child.text.split(" ")[-1])) # Chapter II => 2
            #child.text = str(self.word_to_num.parse(child.text.split(" ")[-1])) #  Chapter Two => 2

    def go_down_to_text(self, element, parent):
        text = {}
        text["text"] = []
        text["subject"] = []
        prev_footnote = False #need this flag for when footnote is broken up into ftnote tags and p tags
        still_titles = False #need this flag so that the headers and titles at the beginning of a section
                             #do not get their own segment but are attached to the beginning of the first paragraph

        for index, child in enumerate(element):
            self.handle_special_tags(element, child, index)
            if len(child) > 0:
                if child.text.isdigit():
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
                elif self.siblingsHaveChildren(element) > 0:
                    self.siblingsHaveChildren(element)
                    text["subject"] += [self.cleanText(child.xpath("string()").replace("\n\n", " "))]
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
                        text["text"] += [self.cleanText(child.xpath("string()").replace("\n\n", " "))]
        return text


    def add_footnote(self, parent, element, child):
        xpath_result = unicode(child.xpath("string()"))
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
        for count, x in enumerate(text):
            if type(x) is dict:
                array.append(self.convertManyIntoOne(x['text'], "{} {}".format(node_name, count+1)))
            else:
                ''''
                add to array based on starting numerals for each sentence that dictate where in the array each line goes
                if not x[0].isdigit():
                    array[-1] += u"<br/>{}".format(x)
                    continue

                num = int(x.split(".")[0])
                for i in range(num-prev_num-1):
                    array.append("")
                prev_num = int(x.split(".")[0])
                '''
                array.append(x)

        if len(array) > 0 and type(array[0]) is not list: #not list in other words string or unicode
            array = self.pre_parse(array)
            array = self.parse(array, self.footnotes, node_name)
            self.any_problems(array, node_name)
        return array

    def any_problems(self, array, node_name):
        found = False
        for x in array:
            if "xref" in x:
                found = True
        if found:
            print "PROBLEM IN"
            print node_name

    def pre_parse(self, text_arr):
        p = re.compile(u"(\d+)[\.|\s+\.]+")
        content = {}
        prev = 1
        '''
        for count, line in enumerate(text_arr):
            match = p.match(line)
            if match:
                num = int(match.group(1))
                if num not in content:
                    content[num] = line.replace(match.group(0),"")
                else:
                    content[num] += "<br>" + line.replace(match.group(0),"")
                prev = num
            else:
                if prev in content:
                    content[prev] += "<br>" + line
                else:
                    content[prev] = line

        content = convertDictToArray(content, empty="")
        '''
        return text_arr

    def sort_by_book_order(self, key):
        if key == "text":
            return len(self.array_of_names) + 1
        if key == "subject":
            return len(self.array_of_names) + 2
        index = self.array_of_names.index(key)
        return index


    def interpret_and_post(self, node, running_ref, prev="string"):
        if self.assertions:
            assert Ref(running_ref), running_ref
        sorted_keys = sorted(node.keys())#, key=self.sort_by_book_order)
        last_key = sorted_keys[len(sorted_keys) - 1]
        not_last_key = True
        for i, key in enumerate(sorted_keys):
            if key == '\n':
                continue

            if last_key == key:
                not_last_key = False

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
                text = self.convertManyIntoOne(node["text"], running_ref.split(", ", 1)[-1])
                self.post(running_ref, text, not_last_key)

    def handle_special_case(self, results):
        #normalize dictionary keys to be Parsha names
        torah_book = self.title.split(" ")[-1]
        torah_book = library.get_index(torah_book)
        parshiot_dicts = torah_book.alt_structs["Parasha"]["nodes"]
        parshiot = [el["sharedTitle"] for el in parshiot_dicts]
        old_results = dict(results)
        for parsha in results.keys():
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
                    if perek not in text_dict.keys():
                        text_dict[perek] = {}
                    if verse not in text_dict[perek].keys():
                        text_dict[perek][verse] = []
                    line = line.replace(perek_and_verse[0], "")
            if line[0] == " ":
                line = line[1:]
            line = self.fix_html(line)
            text_dict[perek][verse].append(line)

        for perek in text_dict.keys():
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
        if element.text.isdigit():
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
      raise TypeError, "expected string, got %s" % type(input)
   input = input.upper()
   nums = ['M', 'D', 'C', 'L', 'X', 'V', 'I']
   ints = [1000, 500, 100, 50,  10,  5,   1]
   places = []
   for c in input:
      if not c in nums:
         raise ValueError, "input is not a valid roman numeral: %s" % input
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
      raise ValueError, 'input is not a valid roman numeral: %s' % input

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
      raise TypeError, "expected integer, got %s" % type(input)
   if not 0 < input < 4000:
      raise ValueError, "Argument must be between 1 and 3999"
   ints = (1000, 900,  500, 400, 100,  90, 50,  40, 10,  9,   5,  4,   1)
   nums = ('M',  'CM', 'D', 'CD','C', 'XC','L','XL','X','IX','V','IV','I')
   result = ""
   for i in range(len(ints)):
      count = int(input / ints[i])
      result += nums[i] * count
      input -= ints[i] * count
   return result

