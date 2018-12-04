#encoding=utf-8

from bs4 import BeautifulSoup, element
from sources.functions import getGematria
from sefaria.model.text import *
from main import *


class Segment(object):

    def __init__(self, type):
        self.type = type
        self.text = ""

    def create_source(self):
        #create source for sourcesheet out of myself
        segment = BeautifulSoup(self.text, "lxml")
        segment = remove_a_links(segment)
        source = {"outsideText": segment.text}
        return source


class Source(object):

    # def __init__(self, segment_class, ref):
    def __init__(self, ref, segment_class=None):
        self.parshan_name = u""
        self.parshan_id = 0
        self.about_source_ref = u""  # words of nechama in regards to the parshan or this specific book, that we will lose since it is not part of our "ref" system see 8.html sec 1. "shadal"
        self.perek = u""
        self.pasuk = u""
        self.ref = ref  # this can be blank indicating our parser couldn't figure out what the ref is
        self.nechama_comments = u""
        self.nechama_q = []  # list of Qustion objs about this Parshan seg
        self.segment_class = segment_class
        self.text = u""
        self.refDisplayPosition = u"top"
        self.snunit_ref = None

    @staticmethod
    def is_source_text(segment, important_classes):
        return isinstance(segment, element.Tag) and "class" in segment.attrs.keys() and segment.attrs["class"][0] in important_classes

    def get_sefaria_ref(self, ref):
        if ref == "":
            return None
        try:
            r = Ref(ref)
            assert r.text('he').text
            if r.is_commentary():
                if re.search(u".*(?:on|,)\s((?:[^:]*?):(?:[^:]*)):?", r.normal()):
                    r_base = Ref(re.search(u".*(?:on|,)\s((?:[^:]*?):(?:[^:]*)):?", r.normal()).group(1))
                else:
                    return r #None
            else:
                r_base = r
            if not r.is_book_level():
                return r
            else:
                return None
        except (InputError,  AssertionError, IndexError) as e:
            # try to see if all that is wrong is the segment part of the ref, say, for Ralbag Beur HaMilot on Torah, Genesis 4:17
            last_part = ref.split()[-1]
            if last_part[0].isdigit(): # in format, Ralbag Beur HaMilot on Torah, Genesis 4:17 and last_part is "4:17", now get the node "Ralbag Beur HaMilot on Torah, Genesis"
                ref_node = " ".join(re.split(u"[:\s]", ref)[0:-1])
                return self.get_sefaria_ref(ref_node) #returns Ralbag Beur HaMilot on Torah, Genesis

    def glue_ref_and_text(self, ref, text, gray=True):
        if isinstance(text, list):
            text = u' '.join(text)
        if self.about_source_ref and self.ref:
            if self.about_source_ref != self.ref:
                try:
                    he_self_ref = Ref(self.ref).he_normal()
                except InputError as e:
                    print u"Exception {}".format(e)
                    assert isinstance(self.ref, unicode)
                    he_self_ref = self.ref
                about_words = [x.strip(u'''"\u05f3' ,''') for x in re.split(u" |:", self.about_source_ref.strip())]
                ref_words = [x.strip(u'''"\u05f3' ,''') for x in re.split(u" |:", he_self_ref)]
                diff = set(about_words).difference(set(ref_words))
                diff.discard(u'פרק')
                diff.discard(u'פסוק')
                diff.discard(u'הלכה')
                diff.discard(u'')
                print u"diff words: {}".format(len(diff))
                for w in diff:
                    print w
                if len(diff) <= 3:
                    if self.get_sefaria_ref(self.ref):
                        return text
                    else:
                        return self.gray(self.about_source_ref, text)
                else:
                    return u"{}<br/>{}".format(self.about_source_ref, text)
            else:  # self.about_source_ref == self.ref, they are the same so the self.ref is not a Sefaria Ref it is just the about_source_ref and we make it look nice
                return self.gray(self.ref, text)
        else:
            return self.gray(self.about_source_ref, text)

    def gray(self, source_ref, text):
        """
        this is to get the grey as
        :param source_ref:
        :param text:
        :return:
        """
        if len(source_ref.split()) > 12:
            return u"{}<br/>{}".format(source_ref, text)
        else:
            return u"<span style='color:rgb(153,153,153);'>{}</span><br/><span style='color:rgb(51,51,51);'>{}</span>".format(source_ref, text)

    def create_source(self):
        # remove snunit tags from text and about_source_ref
        if isinstance(self.text, list):
            for i, line in enumerate(self.text):
                segment = BeautifulSoup(self.text[i], "lxml")
                segment = remove_a_links(segment)
                self.text[i] = segment.text
        else:
            segment = BeautifulSoup(self.text, "lxml")
            for a in segment.findAll('a'):  # get all a tags and remove them
                a.replaceWithChildren()
            self.text = segment.text


        comment = self.text

        segment = BeautifulSoup(self.about_source_ref, "lxml")
        for a in segment.findAll('a'):  # get all a tags and remove them
            a.replaceWithChildren()
        self.about_source_ref = segment.text

        nested_source_refDisplayPosition = True if isinstance(comment, list) else False
        # is Sefaria ref
        if self.get_sefaria_ref(self.ref):
            if self.about_source_ref:
                comment = self.glue_ref_and_text(self.about_source_ref, comment, gray=False)
            enRef = self.get_sefaria_ref(self.ref).normal()
            heRef = self.get_sefaria_ref(self.ref).he_normal()
            source = {"ref": enRef, "heRef": heRef,
                      "text":
                          {
                              "he": comment,
                              "en": ""
                          },
                      "options": {
                          "indented": "indented-1",
                          "sourceLayout": "",
                          "sourceLanguage": "hebrew",
                          "sourceLangLayout": "",
                          "refDisplayPosition": self.refDisplayPosition
                      }
                      }
            if isinstance(self.text, list):
                source["text"] = {
                    "he": u'{} <a class="nested_question_hack" href= "/{}">{}</a><br>{}'.format(self.text[0], enRef, heRef, self.text[1]),
                    "en": ""
                }
                source["options"]["indented"] = ""

        elif self.ref:
            # thought we found a ref but it's not an actual ref in the Sefaria library
            # get the he_normal() of ref or if it's invalid ref, try modifying and then running he_normal()
            try:
                self.ref = Ref(self.ref).he_normal()
            except InputError:
                last_part = self.ref.split()[-1]
                #assert last_part[0].isdigit()  # in format, Ralbag Beur HaMilot on Torah, Genesis 4:17 and last_part is "4:17", now get the node "Ralbag Beur HaMilot on Torah, Genesis"
                try:
                    temp_ref = Ref(" ".join(self.ref.split()[0:-1]))
                    self.ref = temp_ref.he_normal()
                except (InputError, AttributeError), e:
                    if " on " in self.ref: #Rashi on Genesis
                        term = " ".join(self.ref.split()[0:-1]).split(" on ")[0] # this should get just "Rashi" or "Abarbanel"
                        term = Term().load({"titles.text": term})
                        if term:
                            self.ref = [title['text'] for title in term.titles if title['lang'] == 'he'][0]
                    elif ", " in self.ref: #HaKtav VeKabbalah, Hosea
                        title = " ".join(self.ref.split()[0:-1]).rsplit(", ")[0:-1]
                        index = Index().load({"title": title})
                        if index:
                            self.ref = index.get_title('he')
                    else: #Onkelos Isaiah
                        term = Term().load({"titles.text": self.ref.split()[0]})
                        if term:
                            self.ref = [title['text'] for title in term.titles if title['lang'] == 'he'][0]

            if self.about_source_ref:
                comment = self.glue_ref_and_text(self.about_source_ref, comment, gray=False) #use actual text if we can
            else:
                comment = self.glue_ref_and_text(self.ref, comment, gray=True) # otherwise, use the ref we thought it was
            source = {"outsideText": comment,
                      "options": {
                          "indented": "indented-1",
                          "sourceLayout": "",
                          "sourceLanguage": "hebrew",
                          "sourceLangLayout": "",
                          "refDisplayPosition": self.refDisplayPosition
                      }
                      }
        elif not self.ref:
            if self.about_source_ref:
                comment = self.glue_ref_and_text(self.about_source_ref, comment, gray=False)
            source = {"outsideText": comment,
                      "options": {
                          "indented": "indented-1",
                          "sourceLayout": "",
                          "sourceLanguage": "hebrew",
                          "sourceLangLayout": "",
                          "refDisplayPosition": self.refDisplayPosition
                        }
                      }
        else:
            raise InputError, "Didn't anticipate this case in the casses of ref on Source obj"
        if nested_source_refDisplayPosition:
            source["options"]["indented"] = ""
        return source

    def get_ref(self):
        return self.ref

    def add_text(self, segment, segment_class=None):
        for br in segment.find_all("br"):
            br.replace_with("\n")
        segment_text = bleach.clean(str(segment), tags=["u", "b", "table", "td", "tr", "p", "br"], strip=True)
        # self.parshan_name = segment_class
        # print self.parshan_name
        if not self.text:
            self.text = segment_text
            return None
        else:
            new_source = self.copy()
            new_source.text = segment_text
            if segment.attrs.get("id"):
                new_source.parshan_id = segment.attrs.get("id")
            return new_source



    def index_not_found(self):
        return not self.get_ref() and self.about_source_ref #not found a ref, but have info on what it is


    def copy(self):
        # ref_copy = Ref(self.ref.normal())
        ref_copy = self.ref
        new_source = Source(ref_copy, self.segment_class)
        # new_source.parshan_name = self.parshan_name
        new_source.parshan_id = self.parshan_id
        new_source.about_source_ref = self.about_source_ref
        # new_source.pasuk = self.pasuk
        # new_source.perek = self.perek

        return new_source


class Header(object):
    def __init__(self, segment):
        self.letter = segment.find(attrs = {"class":"number"}).text.replace(".", "").strip()
        self.header_text = [x for x in segment.find_all("td") if x.attrs == {}][0].text.strip()
        table_html = str(segment)
        formatted_text = self.format(BeautifulSoup(table_html, "lxml").text)
        self.text = u"<table><tr><td><big>{}</big></td></tr></table>".format(formatted_text)

    @staticmethod
    def is_header(segment):
        return isinstance(segment, element.Tag) and segment.name == "table" and \
               segment.attrs["class"][0] in ["header"]

    def create_source(self):
        #create source for sourcesheet out of myself
        segment = BeautifulSoup(self.text, "lxml")
        segment = remove_a_links(segment)
        source = {"outsideText": str(segment)}
        return source

    def format(self, comment):
        found_difficult = ""
        # digits = re.findall("\d+\.", comment)
        # for digit in set(digits):
        #     comment = comment.replace(digit, "<b>"+digit + " </b>")

        all_a_links = re.findall("(<a href.*?>(.*?)</a>)", comment)
        for a_link_and_text in all_a_links:
            a_link, text = a_link_and_text
            comment = comment.replace(a_link, text)

        if "pages/images/hard.gif" in comment:
            found_difficult += "*"
        if "pages/images/harder.gif" in comment:
            found_difficult += "*"

        # we need to specifically keep these tags because the "text" property will remove them so we "hide" them with nosense characters
        tags_to_keep = ["u", "b"]
        comment = comment.replace("<u>", "$!u$").replace("</u>", "$/!u$")
        comment = comment.replace("<b>", "$!b$").replace("</b>", "$/!b$")
        text = BeautifulSoup(comment, "lxml").text

        text = text.strip()
        while "  " in text:
            text = text.replace("  ", " ")

        # following code makes sure "3.\nhello" becomes "3. hello"
        digit = re.match(u"^.{1,2}[\)|\.]", text)
        if digit:
            text = text.replace(digit.group(0), u"")
            text = text.strip()
            text = digit.group(0) + u" " + text

        # now get the tags back and remove nonsense chars
        text = text.replace("$!u$", "<u>").replace("$/!u$", "</u>")
        text = text.replace("$!b$", "<b>").replace("$/!b$", "</b>")
        text = text.replace("\n", "<br/>")

        return (found_difficult + text).strip()


class Question(object):

    def __init__(self, segment=None, question=None):
        if question:
            self.number = question.number
            self.difficulty= question.difficulty
            return

        bullet_tag = segment.select(".bullet > p")
        number = []
        bullet = []
        if bullet_tag:
            bullet_tag = bullet_tag[0]
            number, bullet = (bullet_tag.parent.parent.select(".number"), bullet_tag.find('img'))

        self.number = number[0].text if number else u""
        # bullet = [t.find('img') for t in segment.select(".bullet > p")][0]
        # self.number = bullet.parent.parent.select(".number")[0].text if bullet.parent.parent.select(".number") else u""
        if not bullet:
            self.difficulty = 0
        elif bullet.attrs['src'] == 'pages/images/hard.gif':
            self.difficulty = 1
        elif bullet.attrs['src'] == 'pages/images/harder.gif':
            self.difficulty = 2

        table_html = str(segment)  # todo: fix this line, why are we losing so much data here?
        segs = [s for s in segment.find_all('p') if not s.parent.has_attr('class')]
        any([s.attrs for s in segs])
        self.q_text = u" ".join([bleach.clean(str(s), tags=["u", "b", "table", "td", "tr", "p", "br"], strip=True).strip() for s in segment.find_all('p') if not s.parent.has_attr('class')])
        self.text = self.format()
        self.q_source = segment

    @staticmethod
    def nested(segment):
        # check if nested. if so, return the data to Source to create new segments from the nested parts.
        # assert len(Section.get_tags(segment)) == 1
        imp_contents = Section.get_tags(segment)[0]

        q = [tag for tag in imp_contents.contents if isinstance(tag, element.Tag) and not tag.attrs] #todo: can we make this line more reliable, write tests for this line
        # print '******'+str(len(q))
        q = q[0]
        classes = ["parshan", "midrash", "talmud", "bible", "commentary","question2", "question", "table"]  # todo: probbaly should be a list of classes of our Obj somewhere
        is_nested = False
        for e in Section.get_tags(q):
            if e.find('td') or (e.attrs and 'class' in e.attrs and [c in e.attrs['class'] for c in classes]) and e.text:
                is_nested = True
                break

        if is_nested:
            # print "**NESTED**"
            return q
        # print "****Print Q not nested"
        return None

    @staticmethod
    def is_question(segment):
        return isinstance(segment, element.Tag) and segment.name == "table" and \
               segment.attrs["class"][0] in ["question", "question2"]

    def create_source(self):
        #create source for sourcesheet out of myself
        segment = BeautifulSoup(self.text, "lxml")
        segment = remove_a_links(segment)
        source = {"outsideText": str(segment)}
        return source

    def format(self, without_params=[], difficulty_symbol = [u'<sup class="nechama"></sup>', u'''<sup class="nechama">*</sup>''', u'''<sup class="nechama">**</sup>''']):
        """

        :param without_params: list. ex: ["difficulty", "number"]
        :return: the text of the q the way it is presented in source sheets with/without (but for now the only way
        to present outside sources in source sheets) the number and difficulty
        """
        print self.q_text
        # if re.search(u'>(.*?)<', self.q_text):
        #     text = re.search(u'>(.*?)<',  self.q_text).group(1)
        # else:
        text = self.q_text
        if "number" not in without_params:
            text= str(self.number) + ' ' + text
        # difficulty is first in the order
        if "difficulty" not in without_params:
            text = str(difficulty_symbol[self.difficulty]) + ' ' + text

        return text


class Table(object):
    ## specifically for tables in HTML that end up staying as HTML in source sheet such class="RT" or "RTBorder"

    def __init__(self, segment):
        self.text = bleach.clean(str(segment), tags=["u", "b", "table", "td", "tr", "p", "br"], strip=True)
        self.text = re.sub("<p>.{1,2}</p>", "<br/>", self.text) # try to mimic formatting of HTML

    @staticmethod
    def is_table(segment):
        return isinstance(segment, element.Tag) and segment.attrs.get("class", "") in [["RT"], ["RTBorder"]]

    def create_source(self):
        #create source for sourcesheet out of myselfwithout_params=["number"]
        segment = BeautifulSoup(self.text, "lxml")
        segment = remove_a_links(segment)
        source = {"outsideText": str(segment)}
        return source



def remove_a_links(segment):
    for a in segment.findAll('a'):  # get all a tags and remove them
        if a.attrs and "class" in a.attrs.keys() and a.attrs["class"] == "nested_question_hack":
            continue
        # if a.attrs["href"].find("snunit") > 0:
        #     ref = Section.exctract_pasuk_from_snunit(a)
        #     new_a_href = "<a href='/{}'".format(ref)
        #     segment.replace_with(ref, new_a_href)


        a.replaceWithChildren()
    return segment



class RT_Rashi(object):
    """an object representing an RT_Rashi table for parsing purposes"""

    def __init__(self):
        pass

    @staticmethod
    def order_the_table(self, segment):
        tags = Section.get_tags(segment)


class Nechama_Comment(object):

    def __init__(self, text):
        self.text = text

    @staticmethod
    def is_comment(segments, i, important_classes):
        # determine if it's worth looking to see what this ref is:
        # if it's the last one, it's not a ref because a comment needs to come after it
        # if the next one isn't a Tag, this can't be a ref because comments are always Tags with classes
        # indicating parshan, bible, etc.
        # also make sure the next one has a class in self.important_classes
        # if it doesn't meet all the criteria, then it's just a comment by Nechama
        # segment = segments[i]
        next_comment_parshan_or_bible = ""
        this_comment_could_be_ref = i < len(segments) - 1 and isinstance(segments[i + 1], element.Tag) and isinstance(
            segments[i], element.Tag)
        if this_comment_could_be_ref:
            next_comment_parshan_or_bible = "class" in segments[i + 1].attrs.keys() and \
                                            segments[i + 1].attrs["class"][0] in important_classes
        return not next_comment_parshan_or_bible or not this_comment_could_be_ref



    def create_source(self):
        #create source for sourcesheet out of
        segment = BeautifulSoup(self.text, "lxml")
        segment = remove_a_links(segment)
        source = {"outsideText": str(segment)}
        return source


class Nested(object):
    """
    class for Hybrid obj classes that we must chose btw to egt the Obj that will be the actual source in the sheet_segment
    """

    def __init__(self, obj, section, question=False):
        self.question = question
        if obj:
            self.obj = obj
        else:
            self.obj = []
        self.segment_objs = []
        self.add_segments(section)
    # def __init__(self, options, section):
    #     self.whole_segments_of_section = section
    #     self.options = options


    @staticmethod
    def is_nested(segment):
        if isinstance(segment, element.NavigableString):
            return
        classed_tags = []
        tags_with_p = []
        classes = ["parshan", "midrash", "talmud", "bible", "commentary", "question2", "question", "table", "RT", "RTBorder"]#, "RT", "RT_RASHI"]
        for i, e in enumerate(segment.findAll()):
            if (e.attrs and 'class' in e.attrs and set(e.attrs['class']).intersection(
                    classes)):  # any([c in e.attrs['class'] for c in classes])):  # e.find('td') or
                if not e.text.strip() in ' '.join([item[1].text.strip() for item in classed_tags]): #todo: write better. can be in the same line but i want to test that it right first. it is to deal with cases like q 2 in section 3 in 62.html
                    classed_tags.append((i, e))
            elif (e in segment.findAll('p')) and not e.parent.has_attr('class') and e.text.strip()\
                and not (re.search('mypopup', e.parent.attrs.get('href')) if e.parent.attrs.get('href') else None):
                tags_with_p.append((i, e))
            elif (e in segment.findAll('p')) and e.parent.has_attr('class') and e.parent.attrs['class'] == ['RT_RASHI']:
                tags_with_p.append((i, e))

        if not classed_tags: #we don't need to check in this case
            return

        objs = set()
        all_text = ur''.join([item[1].text.strip() for item in classed_tags])
        for p in tags_with_p:
            if p[1].text.strip() not in all_text: #or not re.search(p[1].text.strip(), all_text)
                objs.add(p)
        objs = objs.union(set(classed_tags))
        testing_doubls = [o for o in objs if re.search(u'וכי סומים היו', o[1].text)]
        objs = sorted(objs, key=lambda x: x[0])
        objs = [o[1] for o in objs]
        return objs
        # # Test: testing if we get all the text from the html to ourObjs
        # extract_text = ' '.join([e.text for e in classed_tags]) #text that was taken out of the segment after cleaning
        # exctract_set = set(extract_text.split())
        # seg_set = set(segment.text.split())
        # diff = seg_set.difference(exctract_set)
        # if diff:
        #     pass
        # return classed_tags

        # check if nested. if so, return the data to Source to create new segments from the nested parts.
        imp_contents = Section.get_tags(segment)
        q = []
        classed_tages = segment.findAll(class_="question2")
        tags_with_text = [t for t in segment.findAll(text=True) if t != '\n'] #assumeing that only tags with text => seen will be of value to us while scrapping
        leaves = [tag for tag in segment.findAll(class_ = "question2") if tag.text in tags_with_text]
        nleaves = [leaf for leaf in leaves if not any([leaf in l for l in leaves])]
        for cont in imp_contents:
            q += [tag for tag in cont.contents if isinstance(tag,element.Tag) and not tag.attrs]  # todo: can we make this line more reliable, write tests for this line

        # print '******' + str(len(q))
        q = q[0]
        classes = ["parshan", "midrash", "talmud", "bible", "commentary", "question2", "question",
                   "table"]  # todo: probbaly should be a list of classes of our Obj somewhere
        is_nested = False
        for e in Section.get_tags(q):
            if e.find('td') or (e.attrs and 'class' in e.attrs and [c in e.attrs['class'] for c in classes]):
                is_nested = True
                break

        if is_nested:
            # print "**NESTED**"
            return q
        # print "****Print Q not nested"
        return None

    def add_segments(self, section):
        # section.add_segments(self.obj)
        for i, sp_obj in enumerate(self.obj):
            self.segment_objs.append(section.classify(sp_obj, i, self.obj))

        for i, obj in enumerate(self.segment_objs):
            if isinstance(obj, Text): #and isinstance(self.segment_objects[i-1], Source):
                if isinstance(self.segment_objs[i-1], Source):
                    self.segment_objs[i] = self.segment_objs[i - 1].add_text(obj.sp_segment, obj.segment_class)
                    if isinstance(self.segment_objs[i], Text):
                        self.segment_objs.pop(i)
                else:
                    if obj.ref_guess:
                        self.segment_objs[i] = Source(obj.ref_guess)
                        self.segment_objs[i].add_text(obj.sp_segment)
                        self.segment_objs[i].parshan_id = obj.sp_segment.attrs.get("id")

    def choose(self):

        def demi_q(q, text):
            like_q = Question(question=q)
            like_q.q_text = text
            like_q.text = like_q.format()
            return like_q

        if self.question:
            for i, s in enumerate(self.segment_objs):
                if isinstance(s, Nechama_Comment):
                    self.segment_objs[i] = demi_q(self.question, s.text)
                    return self.segment_objs
                elif isinstance(s, Question):
                    return self.segment_objs
            self.glue_q_number(self.segment_objs[0])
            # self.segment_objs.insert(0, demi_q(self.question, u''))
        return self.segment_objs

    def glue_q_number(self, ourObj):
        number = self.question.number
        if isinstance(ourObj, Source):
            ourObj.refDisplayPosition = "none"
            ourObj.text = [number, ourObj.text]

    def create_source(self):
        return_sheet_obj = []
        # for option in self.options:
        #     return_sheet_obj.extend([obj.create_source() for obj in option] if isinstance(option, list) else [option.create_source()])

        # source = self.choose().create_source()
        # return source
        # return return_sheet_obj

        if self.segment_objs:
            created_obj = []
            for seg in self.segment_objs:
                if not seg:
                    continue
                created_obj.append(seg.create_source())
            return created_obj
            # return create_sheetsources_from_sections(self.segment_objs)
        # if isinstance(self.obj, list):
        #     pass # place holder till Nested is resolved
        else:
            return self.obj.create_source()

class Text(object):

    def __init__(self, sp_segment, segment_class, ref_guess=None):
        self.sp_segment = sp_segment
        self.segment_class = segment_class
        self.ref_guess = ref_guess


    def create_source(self):
        """
        Text should never get to a create_source place, because Text is only one part of Source that "got lost"
        this function is only for the sake of test runes. it reality it is code that should never be run! todo: right a test to see that it is not run.
        :return: a sheet obj
        """
        self.sp_segment = remove_a_links(self.sp_segment)
        source = {"outsideText": self.sp_segment.text}
        return source

    def choose(self):
        s = Source(self.ref_guess)
        s.add_text(self.sp_segment)
        return s
