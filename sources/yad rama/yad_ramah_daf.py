# -*- coding: utf-8 -*-
from sources.functions import *
__author__ = 'stevenkaplan'


class Yad_Ramah:

    def __init__(self):
        self.daf_re = re.compile(u"\[[\u05D0-\u05EA]{1,3},[\u05D0-\u05EA]{1}\]")
        self.siman_re = re.compile(u"[\u05D0-\u05EA]+\. ")


    def getText(self, file):
        text = []
        temp = ""
        for line in file:
            line = line.decode('utf-8')
            line = line.replace("\n", "")
            line = self.removeBadText(line)
            if line.replace(" ", "") == "":
                continue
            if line.find(u"פרק ") >= 0 and len(line.split(" ")) < 4 and line.find("#") >= 0:
                continue
            if line.find("#") >= 0:
                temp += line.replace("#", "")
                if len(temp) > 0:
                    text.append(temp)
                temp = ""
            else:
                temp += line

        file.close()
        if len(temp) > 0:
            text.append(temp)
        return text


    def removeBadText(self, para):
        arr = []
        arr = re.findall(u">.*?<", para)
        arr += re.findall(u"<.*?>", para)
        for each in arr:
            print each
            if len(each) < 12:
                para = para.replace(each, u"")
        return para


    def structureText(self, text):
        text_by_daf = {}
        for index, para in enumerate(text):
            daf_match = self.daf_re.match(para)
            if daf_match:
                data = daf_match.group(0)
                para = para.replace(data+" ", "")
                para = para.replace(data, "")
                daf = getGematria(data.split(",")[0])
                amud = getGematria(data.split(",")[1])
                if amud == 2:
                    page = daf * 2
                else:
                    page = daf * 2 - 1
                assert page+1 not in text_by_daf
                text_by_daf[page] = []

            siman_match = self.siman_re.match(para)
            if siman_match:
                siman = siman_match.group(0)
                para = para.replace(siman, u"<b>{}</b>".format(siman))

            assert page in text_by_daf
            text_by_daf[page].append(para)
        return text_by_daf

    def create_schema(self):
        root = JaggedArrayNode()
        root.add_primary_titles("Yad Ramah on Bava Batra", u"יד רמה על בבא בתרא")
        root.add_structure(["Daf", "Paragraph"], address_types=["Talmud", "Integer"])
        root.validate()
        index = {
            "title": "Yad Ramah on Bava Batra",
            "schema": root.serialize(),
            "categories": ["Commentary2", "Talmud", "Yad Ramah"]
        }
        post_index(index)


if __name__ == "__main__":
    yad_ramah = Yad_Ramah()
    text = yad_ramah.getText(open("YR.txt"))
    text = yad_ramah.structureText(text)
    text = convertDictToArray(text)
    yad_ramah.create_schema()
    send_text = {
        "text": text,
        "language": "he",
        "versionTitle": "Yad Ramah on Bava Batra",
        "versionSource": "http://www.sefaria.org/"
    }
    print "about to post"
    post_text("Yad Ramah on Bava Batra", send_text)