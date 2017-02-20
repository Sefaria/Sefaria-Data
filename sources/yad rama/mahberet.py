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
        for index, letter in enumerate(letters):
            letters[index] = letter.decode('utf-8')
        self.he_letters = letters


    def create_schema(self):
        root = SchemaNode()
        root.key = "mahberet"
        root.add_title("Mahberet Menachem", "en", primary=True)
        root.add_title(u"מחברת מנחם", "he", primary=True)

        intro = JaggedArrayNode()
        intro.add_primary_titles("Introduction", u"הקדמה")
        intro.add_structure(["Paragraph"])
        root.append(intro)

        for i in range(len(22)):
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






if __name__ == "__main__":
    mahberet = Mahberet()
    mahberet.create_schema()