import django
django.setup()
from sefaria.model import *
from sefaria.system.database import db
import re
if __name__ == "__main__":
    #use list of which sheets have links which has sheet title and sheet year and tags
    #for each sheet, get each segment and check if it has
    sheet_data = []
    sheets = db.sheets.find()
    for title_year_tags in sheet_data:
        title, year, tags = title_year_tags
        sheet = db.sheets.find({"title": title, "summary": year, "tags": tags})
        assert sheet, u"Couldn't find sheet {}".format(title)
        for segment in sheet["sources"]:
            text = segment["text"]["he"] if "text" in segment.keys() else segment["outsideText"]
            for match in re.findall("^<a href.*?nechama.org.il/pages/.*?</a>", text):
                text = text.replace(match, )



