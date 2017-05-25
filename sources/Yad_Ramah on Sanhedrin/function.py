# -*- coding: utf-8 -*-
import codecs
import regex
from sefaria.model import *
from sources import functions
from data_utilities import util
from sources.Match import match_new
from sources.Match.match import Match
from sefaria.model.schema import AddressTalmud

list_of_pics = [
    "<img src='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEMAAAByCAIAAACHjvssAAAACXBIWXMAAA7EAAAOxAGVKw4bAAADsklEQVR4nO1cUZakIAyE3T1I30Rvhh6lT6J9Mucjb/N61YEiCZHptb58M4gpUiSBRuO2beEj8OtqA8xwM+kPN5P+cDPpDzcTL0zTNE1TjHGapkLTrUuweSkl9JaW9lQgpZRSYtOXZantoQsmxEHZycXzJMYYYyQa2r4sxrQaJJ4QwjAMu3+RzATqitsVVT35IfzrCv5jELnoj96sKpxy2EE2uK7zhHICRafdv4jh6b9A+PkkxvidocRQqXOneZIPUCbhq7m6qNYIWRoUwbRPqo6gNXhP26cwtKEhE7IyT+OYT+SPs+po32+JBrWxfKJhXwwSVcbQYgMBmjBBvEFVieVDDfvaYFG1iDSWPSKaQajKYJZPpmla1zVkExyvYMdxtHouw6xamec5YHkaaSOAjU/eC/LLoBfoMAzUVX55ZLLEzcCga3BQQpuJztCqiyfxllW/g/y0VT1YkJttO3wPgxnPaSSPpjSChgkvPIrJobwRagG5upC9BW7Z2iHBZ0cClJ8SQiYsmKKVfklTFrzpXiQ/gM30kDCpWieJB6sWEnVRzYvAJ2oRJFGlKmohzUwgj10+EQmH3CfIjV37pDaq+tAIYnUh0nJeftWpC5/rwVdaoXW14hkVJEx6i1qECiaeaU6A3k974LiZ9IebSX+QMOkziP3fTPrE5zCpW2TTLeAOg6B/DT7HJ5/D5F6fwHBbOdYx4QHuMKU03FupkqIeDdXlNkMIql+CwJb47qsKghyE31s8qWaItjsSnoFBwoR/WCwa6qQrgsyVdC/4S5D4KVUQzvjNNy4hcPrtF2mmhDwKb3C+pwjRumxRZUYwiDHVpgHA5txKgE/gtNPY56xPtExYYPnZsv3N9w1niz6QM5liesFbCmCpLjrUmUHb4sVkPPBTE7v3Fg1hdl6p6n2xFqHMTF2GNslgOU+WZaGL4im8ZVlIY4Yzx/40HC4zW43ZZ8Z3s4pJhk5Nj+Ood06rE4r+nmlVreBmcUtl+m9Yd6WUSDzFLw7goSIH2/R0xI4b0kxmlccKGzFxx0RQAfx22MgZx/H5fNI112aPx+PY7PV60TVdrOtaoTfVaFei+NzjIhR3jutK691Q+u5CURHzPKMxzWzAYZwOPI89X783Q16qvezbHqdjqin1r/xKCa9VjhC82dzF91Yy4sffU7vm2x5H6A/v9rJLROOa0dsOJ5uA7TSjQfEjH8dbelFXBqfCO5rdi7oyYC+FEKi4PlXgD/AJiB/gExA3k/5wM+kPN5P+8AXfKnAUFP/nYAAAAABJRU5ErkJggg=='>",
    "<img src='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEYAAABqCAIAAACOIrCeAAAACXBIWXMAAA7EAAAOxAGVKw4bAAADkklEQVR4nO2cXZKkIAyAw9bcC28mnkznZO5DaiiqVcgfEbv7e9jamtGEkBACMoR93+G9+Hd3A+z5mvQEHmNSSimlhP/J/54SRk4PIYTKb69aPqiXUkp1e+Z5vvrVT4f2sMlRtCxL/uGx0cuyxBinaapEHdwbeKd+qLQnP19vs7eXsIO3bfv9/QUA7HWoDnd8fts2AJjnuf4kAMDuhUZ1DkKSImkLGZwOZZYE1lvdTSrtiTHO8ywQgiFHfViggI5VhLM6ote8FELICQobpBHFet4446WU8tyCIddOUC2B7Hc08XAMD3OxAmlmXuKGB52dGbQGJpWxQZoKOZIrtdwlVrEBnDxLFyuQqTIpxgiK2abCuq7iHleZ1MM5CMab7F35vNQvH2gRdyH08Q8iaxjCznjERYsGpf+FgTesPcA1yXDOqYO5VAg9RlnrMDF6FYy9BwwJ+vMy9FqogYeaJOUJB5PAJnnJIcuVipRa2l7CrRm9JjfaXnJ2kV4RdSw9xUXQNAnHa++sYExzluhXyB11NdtDoeYlt1rBlppJ5XcEH1R10B/t9ODpK9zyVzLKJzPLBWXvwUpBs9NwpOYlt9ydCxQTzk0ad1+BwIlJD83dmQ+bl9zwGEvO4HS0G1XGQ5hkyxAmYeVlNXQvTbIKAzpWJeUQXrLla9ITODHJdpbw58Qkk0WLgDecl6xq5W/gPYGBAs+KS5M8Vxa2y+dLk/x3vKz4pMCDO1a1Jsl2CC/lvnsfk2z5sB2ihya9c5P8v5FZarzaWW4+YA4YfZ4baO/BjHq3AcC6rvqeo9BsD5H2lwvntYZ+1dQ49+BzbqjUpVc30FRrlfSop1M8HeXkpRCCw6BCR3U/CJr77Cl7EtQjhm7h53fEsNTngCYi2AdBobOv9FoYXspJ1mH1oUrogpolxqgvWypo/uBiZ51ARsrhxH2XpUUsnF09lJoGXf+KA0P8OkuF4F1JjZdS2v98FULo6iuBcHnZmq1aliVfmWGF6lODSXjoRR0RizW476FfDpQVRwbrpfJAqu3QyoU5rz4yj5MeYu/5s/sXq8o/u/fGqjuReZ6PFzxo9pgEx167zJX6azheYEnwu8ICFJuprH7pfmkPJsCXLwbcdco0TXgjzrqu7VlY1m0CKM24WlawGuxnUolyy64u/P5ryri5vtng++/02g8TmlLg/Sa9cHRCmUIoFfr9gWfOQNv8VnxNegJvaNJ/EZQp+ko34U8AAAAASUVORK5CYII='>",
    "<img src='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAG0AAABtCAIAAAAkmngBAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAEK0lEQVR4nO2dW5KsIAyG9dTsS3YGrgxmZZ4HqjM0KpcQECHfU1dXS8NPQgIorsdxLEwx/56uwCCwjjSwjjSwjjSwjjSwjjSwjjSwjjT8PF2BL5RS9oMx5vf3d1mWbdvshwBSSu/yBzj6ILfaoF0n7VoRbSjHGs6+7+6XrjTqgzFGCBEoyhhjjDmXBgU2MtLG/XbXbVLKeoU3aGZTHZs1r2pXXdLCr5VS4HTW14QQxpjaHmfLh5C1VPX0el10HIcXDapaRJjara6oYycKAl6n0hZeRUe3xlLKHkQEKqlJPz6u6wpVpC2ZEKjkQlRPynmhUuoVIi7f1XM1LSqxHK216y8kZTbAG3+01uiiaNr8OgVdQM2Scbyo5a4ZFvbns7itwKlZpCNJT/aD6+O51/L64x9gFucljzi4rhvMEgF0tETqWNgNnYMwEYwQriMgLu8fsMr0S7J1HNWjPXIdLnte+JYZSzlZLc2L17Zoa4mImr2LvO2zdFPfts1e8t58O5d0lTL8eh6PBtKbnOrXU3k0cHzi6rquEe9OMW9EHjASKSlKRpyJbr1PDUlvDI9VYNu2ux/E48yE4eUSq8OdCLzek8fdJkRERzZGABS4DtyBQYFHRo+AaOzXNLCOGQQyvyQdn7zPtUvOgsR15PQbCNlTdFitNmq/EqvJOfDG7ZHmto3RudURbPiYPnN0sWrYO9JdbueFnIHfcTlB5LyHhoiObIyJsD3SwDrSwDoi8dJB1pEG1pGGWx05UmdxqyNPB8Ok5uGw/129RkMQ2i/kqeElyHkhi+iC3C8MXDkz57Vt3lfIIKAD5480hHTknRkPWL7F7HMxQOAkIdYxm2s3xW2PzUlAsch9e5yKA0X37YENr+t63iSbBxtY4ImNC9LteWbvjirAcSZOyjQkQ8dp/RoaHjqxLsWq33iGByEpbU99nmvawJ3Y8FS/hlKmWv6hfy5uQrJWuTJ0hOwpfEDoGNijUO1nrXX098jn2IcfJXPjAdKvpxolU8jW0Q04Q2aUSik7cOU9JI3Ip8ZOJ3FN4/N7/ig5YhM5Ph7fD8qP4eDQCvt8cN7FJB04wFJQoSY0eTjmYLVucI9RXdApXXlPglUGHpfvFu9IUnQ5NIGi6pHS9SCsM41fCyFcKfsPO5AkLriocoagWz+8xSprVLLi+eFLl9PwStWjXzdzrbKrabgQAupDfjBWrfd9eAo+a5gNKtNoHffBO//a+ETd988IIdx7i7Zts1GyzZtnvNmB1rreCnSj93NdGkWNv272Rx6N/PryHq31m8K/8KZ3QCNDaR8BLp3ORUppXxO377t7NrqUUghhfdMbMbzL3T9qBFUiWkJ6bcP5yoNN6OJ9mq408NpCb3JpX1cGK/7u79tUMswz74EcD74PgAbWkQbWkQbWkQbWkQbWkQbWkQbWkYb/0xOSd775kpwAAAAASUVORK5CYII='>"]


def parse(file1):
    new_daf_tag = regex.compile(u'\u0040\u0032\u0032\u05d3\u05e3\s([\u05d0-\u05ea]{1,3})(\s\u05e2\u0022\u05d1)?')
    new_amud_tag = regex.compile(u'\u0040\u0032\u0032\u05e2\u0022\u05d1')
    placement = 0
    yad_ramah_on_sanhedrin = []
    second_level_list = []
    first_time = True
    daf_number, count = 0, 0
    picture_index_number = 0

    with codecs.open(file1, 'r', 'utf-8') as the_file:
        for each_line in the_file:

            each_line = each_line.strip()
            each_line = each_line.replace(u'\u201d', u'\u0022')
            if "@88" in each_line:
                a_dictionary = add_the_pictures(each_line, list_of_pics, picture_index_number)
                each_line = a_dictionary['the_text']
                picture_index_number = a_dictionary['the_number']

            new_daf = new_daf_tag.match(each_line)
            new_amud = new_amud_tag.match(each_line)

            if "@00" in each_line or "@99" in each_line:
                continue

            if "@33" and "@11" in each_line:
                each_line = each_line.replace('@11', '<b>', 1)
                each_line = each_line.replace('@33', '</b>', 1)


            if new_daf or new_amud:

                if not first_time:
                    yad_ramah_on_sanhedrin.append(second_level_list)
                    count += 1
                    second_level_list = []

                if new_daf:
                    daf_number = util.getGematria(new_daf.group(1))

                if new_daf:
                    placement = daf_number * 2 - 2
                    if new_daf.group(2):
                        placement += 1
                    while placement > count:
                        yad_ramah_on_sanhedrin.append([])
                        count += 1

                first_time = False

            elif not each_line:
                continue

            else:
                second_level_list.append(each_line)

    while placement > count:
        yad_ramah_on_sanhedrin.append([])
        count += 1

    yad_ramah_on_sanhedrin.append(second_level_list)

    return yad_ramah_on_sanhedrin


def create_index():
    return {
        "pubDate": "1200",
        "title": "Yad Ramah on Sanhedrin",
        "pubPlace": "Spain",
        "maps": [],
        "era": "Rishonim",
        "authors": [
            "Meir Abulafia"
        ],
        "categories": [
            "Commentary2",
            "Talmud",
            "Yad Ramah"
        ],
        "schema": {
            "nodeType": "JaggedArrayNode",
            "addressTypes": [
                "Talmud",
                "Integer"
            ],
            "depth": 2,
            "titles": [
                {
                    "lang": "he",
                    "text": u"\u05d9\u05d3 \u05e8\u05de\u05d4 \u05e2\u05dc \u05e1\u05e0\u05d4\u05d3\u05e8\u05d9\u05df",
                    "primary": True
                },
                {
                    "lang": "he",
                    "text": u"\u05d9\u05d3 \u05e8\u05de\u05d4 \u05e2\u05dc \u05de\u05e1\u05db\u05ea \u05e1\u05e0\u05d4\u05d3\u05e8\u05d9\u05df",
                },
                {
                    "lang": "en",
                    "text": "Yad Ramah on Sanhedrin",
                    "primary": True
                },
                {
                    "lang": "en",
                    "text": "Yad Ramah on Tractate Sanhedrin",
                }
            ],
            "key": "Yad Ramah on Sanhedrin",
            "sectionNames": [
                "Daf",
                "Comment"
            ]
        }
    }


def create_text(text):
    return {
        "versionTitle": "Yad Ramah Sanhedrin, Warsaw 1895 ed.",
        "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001063897",
        "language": "he",
        "text": text
    }


def create_links(sanhedrin_ja, yad_ramah_ja):
    list_of_links = []
    amud_number = 1
    match_object = Match(in_order=True, min_ratio=80, guess=False, range=False, can_expand=True)
    for amud_of_sanhedrin, amud_yad_ramah in zip(sanhedrin_ja, yad_ramah_ja):
        ref = 'Sanhedrin {}'.format(AddressTalmud.toStr('en', amud_number))
        the_first_few_words = take_the_first_few_words_of_each_paragraph(amud_yad_ramah)
        matches_dict = match_object.match_list(the_first_few_words, amud_of_sanhedrin, ref)
        for key in matches_dict:
            for match in matches_dict[key]:
                if match != 0:
                    # print'Amud: {} comment: {} corresponds to {}'.format(AddressTalmud.toStr('en', amud_number), key, match)
                    print create_link_text(amud_number, match, key)
                    list_of_links.append(create_link_text(amud_number, match, key))
        amud_number += 1

    return list_of_links


def take_the_first_few_words_of_each_paragraph(list_of_strings):
    list_of_first_few_words = []
    the_first_few_words = 8
    for comment in list_of_strings:
        split_string = comment.split()
        if len(split_string) > the_first_few_words:
            list_of_first_few_words.append(' '.join(split_string[:the_first_few_words]))
        else:
            list_of_first_few_words.append(' '.join(split_string))
    return list_of_first_few_words


"""
source_index - The location in the list.  This will be converted into the proper daf number corresponding to the index

line_number - This is the line number in the Gemara that matched the Divrei Hamatchil

comment_number - The comments of the Yad Ramah are stored in a depth 2 array.  The first level corresponds to the number
of pages in the mesechet.  The second level is a list of each comment on that particular page.  These indices DO NOT correspond
to the gemara line numbers.  The third comment is stored in the second_level_list[2]
"""


def create_link_text(source_index, line_number, comment_number):
    amud_number = AddressTalmud.toStr('en', source_index)
    return {
        "refs": [
            "Sanhedrin {}.{}".format(amud_number, line_number),
            "Yad Ramah on Sanhedrin {}.{}".format(amud_number, comment_number)
        ],
        "type": "commentary",
    }


def add_the_pictures(the_string, list_of_pictures, picture_index_number):
    while "@88" in the_string:
        the_string = the_string.replace('@88', ' {} '.format(list_of_pictures[picture_index_number]), 1)
        picture_index_number += 1

    return {'the_text': the_string, 'the_number': picture_index_number}
