import django
django.setup()
from sefaria.model import *
from sefaria.system.database import db
import re

def get_ssn(read_id):
    """
    gets a sheet id from a server and maps it to the correct ssn (using tags)
    :param read_id: Sheet id
    :return: ssn
    """
    map_get_id_ssn = {}  # this is a map id -> ssn in the server db we are copying from
    ssn = map_get_id_ssn.get(read_id, 0)
    return ssn

def get_post_id(ssn):
    """
    for the post server gets a ssn and returns the id to which the sheet should be posted. based on the ssn<->id maping
    on the post server which we learn from the ssn tags
    :param ssn:
    :return:
    """
    map_post_ssn_id = {}
    post_id = map_post_ssn_id.get(ssn, 0)
    return post_id

if __name__ == "__main__":
    #use list of which sheets have links which has sheet title and sheet year and tags
    #for each sheet, get each segment and check if it has
    sheet_data = []
    sheets = db.sheets.find({"tags": "Bilingual"})
    compile = re.compile(u'/sheets/(?P<id>\d+)')  # (?:\.(?P<node>\d+))?
    for sheet_json in sheets:
        for i, s in enumerate(sheet_json['sources']):
            if 'outsideText' in s.keys():
                uni_outsidetext = unicode(s['outsideText'], encoding='utf8') if isinstance(s['outsideText'],str) else s['outsideText']
                compile = re.compile(u'/sheets/(?P<id>\d+)') #(?:\.(?P<node>\d+))?
                matched = re.search(compile, s['outsideText'])
                if matched:
                    ssn = get_ssn(matched.group("id"))
                    to_post_id = get_post_id(ssn)
                    new_link = re.sub(compile, u'/sheets/\g<id>')
                    s['outsideText'] = re.sub(compile, u'/sheets/\g<id>', uni_outsidetext) #todo: check and then test this line
            elif 'outsideBiText' in s.keys():
                uni_outsidetext = unicode(s['outsideBiText']['he'], encoding='utf8') if isinstance(s['outsideBiText']['he'], str) else \
                s['outsideBiText']['he']
                matched = re.search(compile, s['outsideBiText'])
                if matched:
                    ssn = get_ssn(matched.group("id"))
                    to_post_id = get_post_id(ssn)
                    new_link = re.sub(compile, u'/sheets/\g<id>')
                    s['outsideBiText'] = re.sub(compile, u'/sheets/\g<id>',uni_outsidetext)  # todo: check and then test this line
        pass
    # for title_year_tags in sheet_data:
    #     title, year, tags = title_year_tags
    #     sheet = db.sheets.find({"title": title, "summary": year, "tags": tags})
    #     assert sheet, u"Couldn't find sheet {}".format(title)
    #     for segment in sheet["sources"]:
    #         text = segment["text"]["he"] if "text" in segment.keys() else segment["outsideText"]
    #         for match in re.findall("^<a href.*?nechama.org.il/pages/.*?</a>", text):
    #             text = text.replace(match, )



