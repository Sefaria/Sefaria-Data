#encoding=utf-8
import requests
import re
from bs4 import BeautifulSoup
from sources.functions import getGematria
class Sheets:
    def __init__(self):
        self.parsha_and_year_to_url = {}
        self.bereshit_parshiot = ["1","2","30","62","84","148","212","274","302","378","451","488","527","563","570","581","750","787","820","844","894","929","1021","1034","1125","1183","1229","1291","1351","1420"]
        self.sheets = {}
        self.current_url = ""
        self.current_perakim = ""
        self.current_sefer = ""


    def parse_as_sheets(self, text):
        pass


    def parse_as_text(self, text):
        sections = 0
        sheet_sections = []
        for div in text.find_all("div"):
            if "ContentSection" in div['id']:
                sections += 1
                assert str(sections) in div['id']
                segments = [el for el in div.contents if getattr(el, "text", None)]
                segments = self.group_segments(segments)
                sheet_sections.append(segments)
        return sheet_sections


    def group_segments(self, tags):
        """
        Currently segments are separated like ["Rashi:", "[Rashi quote here]", "Ramban:", "[Ramban quote here]"...]
        This method goes through and groups them like so ["Rashi: Rashi quote here", "Ramban: Ramban quote here"]
        :param tags: list of BeautifulSoup tags
        :return grouped_segments: list of strings corresponding to each tag's text
        """
        prev_seemed_like_commentary = False
        is_commentary = lambda segment: segment.find(":") in [len(segment) - 1, len(segment) - 2]
        is_pasuk = lambda segment: segment.find(u"פסוק") in [0, 1] and len(segment.strip().split()) == 2
        commentary_header = ""
        grouped_segments = []
        for i, tag in enumerate(tags):
            text = tag.text.replace("\n", "")
            if is_commentary(text) or is_pasuk(text):
                if prev_seemed_like_commentary:
                    print "Two commentary headers in a row in {}.html".format(self.current_url)
                    grouped_segments.append(commentary_header)
                if not text.endswith(":"): #pasuk not commentary
                    text += u":"
                commentary_header = text #store this away to be added to the next segment
            else:
                if commentary_header:
                    text = u"<b>{}</b> {}".format(commentary_header, text)
                    commentary_header = u""
                grouped_segments.append(text)
        return grouped_segments


    def extract_perek_info(self, content):
        perek_info = content.find("p", {"id": "pasuk"}).text
        sefer = perek_info.split()[0]
        pereks = re.findall(u"פרק\s+(.*?)\s+", perek_info)
        return (sefer, [getGematria(perek) for perek in pereks])


    def download_sheets(self):
        page_missing = u'דף שגיאות'
        for i in range(1, 1472):
            if str(i) not in self.bereshit_parshiot:
                continue
            response = requests.get("http://www.nechama.org.il/pages/{}.html".format(i))
            content = BeautifulSoup(response.content, "lxml")
            header = content.find('div', {'id': 'contentTop'})
            if page_missing in header.text:
                continue
            year = content.find("div", {"id": "year"}).text
            parsha = content.find("div", {"id": "paging"}).text
            self.current_sefer, self.current_perakim = self.extract_perek_info(content)
            if u"בראשית" not in parsha:
                continue
            print "Sheet {}".format(i)
            text = content.find("div", {"id": "contentBody"})
            if parsha not in self.sheets:
                self.sheets[parsha] = {}
            assert year not in self.sheets[parsha].keys()
            self.parsha_and_year_to_url[parsha+" "+year] = i
            self.current_url = i
            self.sheets[parsha][getGematria(year)] = (year, self.current_sefer, self.current_perakim, self.parse_as_text(text))
            pass


    def post_sheets(self):
        pass


if __name__ == "__main__":
    sheets = Sheets()
    sheets.download_sheets()
    sheets.post_sheets()
    pass

