__author__ = 'stevenkaplan'
from BeautifulSoup import BeautifulSoup, NavigableString
import bleach
from sources.functions import post_text
import re

class Kuzari:
    def __init__(self, chapter_lengths, soup):
        self.text = []
        self.soup = BeautifulSoup(open(soup))
        self.extra = 0
        self.pattern = re.compile(u"^\[[\u05D0-\u05EA]+\]")
        self.chapter_lengths = chapter_lengths


    def run(self):
        for chapter, length in enumerate(self.chapter_lengths):
            self.get_text(chapter, length)

        print self.extra

        send_text = {
            "text": self.text,
            "language": "he",
            "versionTitle": "Kuzari in Judeo-Arabic",
            "versionSource": "http://www.cs.toronto.edu/~yuvalf/kuzari.html"
        }
        post_text("Kuzari", send_text, server="http://proto.sefaria.org")


    def get_text(self, chapter, length):
        self.text.append([])
        for i in range(length):
            name = "ch{}.{}".format(chapter+1, i+1)
            element = self.soup.find(attrs={"name": name})
            total = ""
            for each in element.parent.contents:
                if each == " ":
                    continue
                if type(each) is NavigableString:
                    total += each.replace("\n"," ")
                else:
                    total += each.text.replace("\n", " ")

            next_sibling = element.parent.nextSibling

            while next_sibling.find("a") is None:
                self.extra += 1
                total += " "+next_sibling.text
                next_sibling = next_sibling.nextSibling

            match = self.pattern.match(total)
            if match:
                total = total.replace(match.group(0), "")
                assert self.pattern.match(total) is None
            self.text[chapter].append(total)



if __name__ == "__main__":
    kuzari = Kuzari([117, 81, 74, 31, 28], "kuzari.html")
    kuzari.run()
