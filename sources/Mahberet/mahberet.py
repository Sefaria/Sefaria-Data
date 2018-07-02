# -*- coding: utf-8 -*-
from functions import *
__author__ = 'stevenkaplan'

class Mahberet:

    def __init__(self):
        he_letters = ["א", "ב", "ג", "ד", "ה", "ו", "ז", "ח", "ט","י", "כ", "ל", "מ", "נ", "ס", "ע", "פ", "צ", "ק", "ר", "ש", "ת"]
        self.en_letters = ["Letter Alef",
                        "Letter Bet",
                        "Letter Gimel",
                        "Letter Daled",
                        "Letter Heh",
                        "Letter Vav",
                        "Letter Zayin",
                        "Letter Chet",
                        "Letter Tet",
                        "Letter Yod",
                        "Letter Kaf",
                        "Letter Lamed",
                        "Letter Mem",
                        "Letter Nun",
                        "Letter Samekh",
                        "Letter Ayin",
                        "Letter Peh",
                        "Letter Tzadi",
                        "Letter Kof",
                        "Letter Resh",
                        "Letter Shin",
                        "Letter Tav"]
        for index, letter in enumerate(he_letters):
            he_letters[index] = letter.decode('utf-8')
        self.he_letters = he_letters


    def create_schema(self):
        root = SchemaNode()
        root.key = "mahberet"
        root.add_title("Mahberet Menachem", "en", primary=True)
        root.add_title(u"מחברת מנחם", "he", primary=True)

        intro = JaggedArrayNode()
        intro.add_primary_titles("Introduction", u"הקדמה")
        intro.add_structure(["Paragraph"])
        root.append(intro)

        for i in range(22):
            he_title = self.he_letters[i]
            en_title = self.en_letters[i]
            letter = SchemaNode()
            letter.add_title(en_title, "en", primary=True)
            letter.add_title(he_title, "he", primary=True)
            letter.key = en_title

            intro = JaggedArrayNode()
            intro.add_primary_titles("Introduction", u"הקדמה")
            intro.add_structure(["Paragraph"])

            default = JaggedArrayNode()
            default.key = "default"
            default.depth = 2
            default.default = True
            default.sectionNames = ["Word", "Paragraph"]
            default.addressTypes = ["Integer", "Integer"]

            letter.append(intro)
            letter.append(default)
            root.append(letter)

        glossary = JaggedArrayNode()
        glossary.add_primary_titles("Glossary", u"ביאור המונחים")
        glossary.add_structure(["Paragraph"])
        root.append(glossary)

        root.validate()

        index = {
            "title": "Mahberet Menachem",
            "schema": root.serialize(),
            "categories": ["Other"]
        }
        post_index(index)


    def getIntroText(self, file):
        intro_text = []
        started = False
        for line in file:
            line = line.decode('utf-8').replace("\n", "")
            if len(line) == 0:
                continue
            if line.find("@00") >= 0:
                if started:
                    break
                else:
                    started = True
            else:
                intro_text.append(line)
        return intro_text, file


    def getMainText(self, file):
        letters_text_count = 0
        letters_text = []
        letters_intro_text = []
        letters_text.append([])
        letters_intro_text.append([])
        still_intro = True
        comment = -1
        for line in file:
            line = line.decode('utf-8').replace("\n", "")
            if len(line) == 0:
                continue
            if line.find("@00") >= 0:
                if letters_text_count == 21:
                    break
                letters_text_count += 1
                assert letters_text_count not in letters_text
                letters_text.append([])
                letters_text[0].append([])
                letters_intro_text.append([])
                still_intro = True
                comment = -1
            elif line.find("@30") >= 0:
                line = line.replace("@30", "").replace("@88", "").replace(".","")
                line = u"<strong><big>{}</big></strong>".format(line)
                still_intro = False
                comment += 1
                assert comment not in letters_text[letters_text_count]
                letters_text[letters_text_count].append([])

            if not still_intro:
                assert letters_text_count >= 0
                letters_text[letters_text_count][comment].append(line)

            if not line.find("@00") >= 0 and still_intro:
                assert letters_text_count >= 0
                letters_intro_text[letters_text_count].append(line)


        return letters_intro_text, letters_text, file


    def getText(self, fname):
        file = open(fname)
        intro_text = []
        letters_text = []
        glossary_text = []

        intro_text, file = self.getIntroText(file)
        letters_intro_text, letters_text, file = self.getMainText(file)

        for line in file:
            if len(line) == 0:
                continue
            line = line.decode('utf-8').replace("\n", "")
            glossary_text.append(line)

        return intro_text, letters_intro_text, letters_text, glossary_text



if __name__ == "__main__":
    mahberet = Mahberet()
    mahberet.create_schema()
    vtitle = "Mahberet Menahem, London, 1854."
    vsource = "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001092125"
    intro_text, letters_intro_text, letters_text, glossary_text = mahberet.getText("mahberet.txt")
    intro = {
        "language": "he",
        "text": intro_text,
        "versionTitle": vtitle,
        "versionSource": vsource
    }
    post_text("Mahberet Menachem, Introduction", intro)
    glossary = {
        "language": "he",
        "text": glossary_text,
        "versionTitle": vtitle,
        "versionSource": vsource
    }
    post_text("Mahberet Menachem, Glossary", glossary)

    for index, letter in enumerate(mahberet.en_letters):
        ref = "Mahberet Menachem, {}".format(letter)
        letter_intro = {
            "language": "he",
            "text": letters_intro_text[index],
            "versionTitle": vtitle,
            "versionSource": vsource
        }
        text = {
            "language": "he",
            "text": letters_text[index],
            "versionTitle": vtitle,
            "versionSource": vsource
        }

        post_text(ref, text)
        post_text(ref+", Introduction", letter_intro)

