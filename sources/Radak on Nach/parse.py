# -*- coding: utf-8 -*-

__author__ = 'stevenkaplan'
from sefaria.model import *
from sources.functions import *
from data_utilities.dibur_hamatchil_matcher import *


SERVER = "https://www.sefaria.org"

class Radak:
    def __init__(self, file, book, create=True):
        self.file = file
        self.title = book
        self.num_perakim = 9
        self.text = ""
        self.dhs = ""
        self.create_lines(file)


    def create_lines(self, f):
        lines = []
        text = {}
        open_file = open(f)
        for line in open_file:
            line = line.replace("15", "").replace("14", "").replace("80", "")
            lines.append(line)
        line = " ".join(lines).decode('utf-8')

        self.text, self.dhs = self.parse(line)


    def which_one_first(self, line, options):
        first_pos = 10000
        first_char = ""
        for option in options:
            pos = line.find(option)
            if pos < first_pos and pos >= 0:
                first_pos = pos
                first_char = option
        return first_char


    def which_one_last(self, line, options):
        last_pos = -1
        last_char = ""
        for option in options:
            pos = line.rfind(option)
            if pos > last_pos:
                last_pos = pos
                last_char = option
        return last_char


    def combine_short_verses_with_next(self, verses, perek):
        new_verses = []
        for i in range(len(verses)):
            if (verses[i].find("61") >= 0) ^ (verses[i].find("62") >= 0) or (verses[i].find("61") == verses[i].find("62") == -1):
                verse_tag = re.findall(r'\(.*?\)', verses[i])
                assert len(verse_tag) == 1
                verses[i] = verses[i].replace(verse_tag[0], u"", 1)
                verses[i] = removeAllTags(verses[i])
                which_one = self.which_one_first(verses[i+1], ["61", "62"])
                verses[i+1] = verses[i+1].replace(which_one, "", 1)
                next_verse_tag = re.findall(r'\(.*?\)', verses[i+1])
                assert len(next_verse_tag) == 1
                verses[i+1] = verses[i+1].replace(next_verse_tag[0], u"", 1)
                verses[i+1] = u"{}61{}{}".format(next_verse_tag[0], verses[i], verses[i+1])
            else:
                if self.which_one_first(verses[i], ["61", "62"]) == "62":
                    verses[i] = verses[i].replace("62", "", 1)

                if self.which_one_last(verses[i], ["61", "62"]) == "61":
                    arr = verses[i].rpartition("61")
                    verses[i] = arr[0] + arr[2]

                new_verses.append(verses[i])
        return new_verses


    def extract_comments(self, verse, perek_num, verse_num):
        dhs = []
        finds = re.findall(u"61.*?62", verse)
        positions = []
        for count, find in enumerate(finds): #0-2, 10-12, 20-22 -30
            dhs.append(removeAllTags(find))
            verse = verse.replace(find, u"$@!#")

        comments = verse.split(u"$@!#")

        if len(comments[0]) == 0: #normal case
            assert len(comments) - 1 == len(dhs)
            comments = comments[1:]
        else: #comment in front without DH
            dhs.insert(0, "")
            assert len(dhs) == len(comments)

        if len(comments[-1]) == 0:  #DH at end without comment
            assert len(comments) == len(dhs)
            del comments[-1]

        if comments[0].find("62") >= 0 and len(comments[0].split(" ")) < 3:
            del comments[0]
            del dhs[0]

        for i in range(len(comments)):
            if comments[i].find("61") > comments[i].find(":") or comments[0].find("61") == 0:
                comments[i] = comments[i].replace("61", "")
            if hasTags(comments[i]):
                print "{} {}:{}:{}".format(self.title, perek_num, verse_num, i+1)
                print comments[i]
                print
            if len(dhs[i]) > 0:
                comments[i] = "<b>" + dhs[i] + "</b>" + comments[i]


        return comments, dhs


    def remove_verse_tag(self, verse):
        verse_tag = re.findall(ur'\([\u05D0-\u05EA|-]+\)', verse)
        assert len(verse_tag) == 1
        if verse_tag[0].find("-") >= 0:
            verse_tag[0] = verse_tag[0].split("-")[1]
        verse = verse.replace(verse_tag[0], "")
        return verse, getGematria(verse_tag[0])

    def parse(self, line):
        text = {}
        dh_dict = {}
        line = line.replace("51 ", "51")
        perakim = line.split("51")
        assert len(perakim[0]) < 6
        perakim = perakim[1:]
        for perek in perakim:
            verses = perek.split("60")
            assert len(verses[0]) in range(1,5)
            perek_num = getGematria(verses[0])
            verses = verses[1:]
            text[perek_num] = {}
            dh_dict[perek_num] = {}
            for i, verse in enumerate(verses):
                verse, verse_num = self.remove_verse_tag(verse)
                comments, dhs = self.extract_comments(verse, perek_num, verse_num)
                text[perek_num][verse_num] = comments
                dh_dict[perek_num][verse_num] = dhs
                assert len(dhs) == len(comments)
        return text, dh_dict



def create_schema(book):
    he_book = library.get_index(book).all_titles('he')[0]
    print he_book
    root = JaggedArrayNode()
    en_title = "Radak on {}".format(book)
    he_title = u'רד"ק על {}'.format(he_book)
    root.add_primary_titles(en_title, he_title)
    root.add_structure(["Chapter", "Verse", "Paragraph"])
    root.validate()
    root.toc_zoom = 2
    post_index({
        "title": "Radak on {}".format(book),
        "schema": root.serialize(),
        "categories": ["Tanakh", "Commentary", "Radak", "Writings"],
        "dependence": "Commentary",
        "collective_title": "Radak",
        "base_text_titles": [book],
        "base_text_mapping": "many_to_one"
    }, server=SERVER)

if __name__ == "__main__":
    '''
all_texts = [book for book in library.get_indexes_in_category("Radak", include_dependant=True) if book not in ["Radak on Psalms", "Radak on Genesis"]]

for text in all_texts:
    print """./run scripts/move_draft_text "{}" -l '2' -d "http://www.sefaria.org" -v "all" -k 'kAEw7OKw5IjZIG4lFbrYxpSdu78Jsza67HgR0gRBOdg'""".format(text)
for text in all_texts:
    print text
    refs = library.get_index(text).all_section_refs()
    for ref in refs:
        found = False
        tc = TextChunk(ref, vtitle="Radak on Nach", lang='he')
        for i, line in enumerate(tc.text):
            if line.find("  ") >= 0:
                print ref
                new_text = line.replace("   ", " ").replace("  ", " ")
                found = True
                tc.text[i] = new_text
        if found:
            tc.save(force_save=True)
    '''
    print 'hi'
    skip = ["I_Chronicles", "II_Chronicles"]
    files = [file for file in os.listdir("./RADAK ready")]
    for file in files:
        book = file.replace(".txt", "")
        print book
        if book not in skip:
            continue
        create_schema(book)
        print book
    '''
        radak = Radak("./RADAK ready/{}".format(file), "Radak on {}".format(book), create=False)
        for perek in radak.text:
            radak.text[perek] = convertDictToArray(radak.text[perek])
        radak.text = convertDictToArray(radak.text)
        send_text = {
            "language": "he",
            "versionTitle": "Radak on Nach",
            "versionSource": "http://www.sefaria.org",
            "text": radak.text
        }
        #post_text("Radak on {}".format(book), send_text, server=SERVER)
        #links = radak.make_links()
        #post_link(links, server=SERVER)
    '''