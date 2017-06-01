# -*- coding: utf-8 -*-
from sources.functions import *
from sefaria.model import *
from sefaria.model.schema import AddressTalmud

server = "http://draft.sefaria.org"


def create_schema():
    root = SchemaNode()
    root.add_title("Brit Moshe", "en", primary=True)
    root.add_title(u"ברית משה", "he", primary=True)
    root.key = "britmoshe"

    vol1 = JaggedArrayNode()
    vol1.key = 'vol1'
    vol1.add_title("Volume One", "en", primary=True)
    vol1.add_title(u"חלק "+numToHeb(1), "he", primary=True)
    vol1.depth = 3
    vol1.sectionNames = ["Mitzvah", "Comment", "Paragraph"]
    vol1.addressTypes = ["Integer", "Integer", "Integer"]

    vol2 = JaggedArrayNode()
    vol2.key = 'vol2'
    vol2.add_title("Volume Two", "en", primary=True)
    vol2.add_title(u"חלק "+numToHeb(2), "he", primary=True)
    vol2.depth = 3
    vol2.sectionNames = ["Mitzvah", "Comment", "Paragraph"]
    vol2.addressTypes = ["Integer", "Integer", "Integer"]

    root.append(vol1)
    root.append(vol2)
    root.validate()

    term_obj = {
        "name": "Brit Moshe",
        "scheme": "commentary_works",
        "titles": [
            {
                "lang": "en",
                "text": "Brit Moshe",
                "primary": True
            },
            {
                "lang": "he",
                "text": u"ברית משה",
                "primary": True
            }
        ]
    }

    post_term(term_obj, server=server)

    index = {
        "title": "Brit Moshe",
        "dependence": "Commentary",
        "base_text_titles": ["Sefer Mitzvot Gadol"],
        "categories": ["Halakhah", "Commentary"],
        "schema": root.serialize()
        }
    post_index(index, server=server)


def parse_mitzvah(line, text, mitzvah_num, num_words_marker, next_mitzvah_number_must_be):
    line = line.replace(" ".join(line.split(" ")[0:num_words_marker]), "")
    if line[-1] == ' ':
        line = line[0:-1]
    if line[0] == ' ':
        line = line[1:]
    poss_mitzvah_num = getGematria(line.split(" ")[0])
    #poss_mitzvah_num = ChetAndHey(poss_mitzvah_num, mitzvah_num)
    if (next_mitzvah_number_must_be and next_mitzvah_number_must_be == poss_mitzvah_num) or poss_mitzvah_num > mitzvah_num:
        mitzvah_num = poss_mitzvah_num
        next_mitzvah_number_must_be = None
    else:
        next_mitzvah_number_must_be = mitzvah_num + 2
        mitzvah_num += 1
    text[mitzvah_num] = {}
    return mitzvah_num, next_mitzvah_number_must_be


def almost_identical(str1, str2, diff_allowed=1):
    if len(str1) - len(str2) == 1 and ord(str1[0]) == 65279:
        str1 = str1[1:]
    if len(str1) is not len(str2):
        return False
    diff = 0
    for i in range(len(str1)):
        if str1[i] != str2[i]:
            diff += 1
    return diff <= diff_allowed


def modify_line(line, mitzvah_marker):
    line = line.decode('utf-8').replace("\n", "")
    if line.find(u"""@88מצוה ל"ת""") == 0:
        line = line.replace(u"""@88מצוה ל"ת""", mitzvah_marker)
    if line.find(u"""@88ל"ת""") == 0:
        line = line.replace(u"""@88ל"ת""", mitzvah_marker)
    if line.find(u"""@88מצוה לא תעשה ע' עד עו """) == 0:
        line = line.replace(u"""@88מצוה לא תעשה ע' עד עו """, u"""@88מצוה לא תעשה עה """)
    return line


def parse_section(line, text, section_num, next_sec_number_must_be):
    poss_section_num = getGematria(line)
    poss_section_num = fixChetHay(poss_section_num, section_num)
    if next_sec_number_must_be and next_sec_number_must_be == poss_section_num:
        section_num = poss_section_num
        next_sec_number_must_be = None
    elif 15 > poss_section_num - section_num > 0:
        next_sec_number_must_be = None
        section_num = poss_section_num
    else:
        next_sec_number_must_be = section_num + 2
        section_num += 1

    text[section_num] = []
    return section_num, next_sec_number_must_be


def parse_text(file, mitzvah_marker):
    text = {}
    num_words_marker = len(mitzvah_marker.split(" "))
    section_num = 0
    mitzvah_num = 0
    next_mitzvah_number_must_be = None
    next_sec_number_must_be = None
    for line in file:
        orig_line = line
        line = line.replace("\r", "")
        line = modify_line(line, mitzvah_marker)
        if line.replace(" ", "") == "":
            continue

        if line.find("@11") == 0:
            if len(line.split(" ")) < 3 and getGematria(line) == section_num + 1:
                section_num += 1
                text[mitzvah_num][section_num] = []
            else:
                text[mitzvah_num][section_num].append(removeAllTags(line))
        elif line.find("@99") == 0 or line.find("@00") == 0:
            last_comment = len(text[mitzvah_num][section_num]) - 1
            assert last_comment >= 0
            text[mitzvah_num][section_num][last_comment] += removeAllTags(line)
        elif len(line.split(" ")) < 9 and "22" not in line and almost_identical(" ".join(line.split(" ")[0:num_words_marker]), mitzvah_marker):
            mitzvah_num, next_mitzvah_number_must_be = parse_mitzvah(line, text, mitzvah_num, num_words_marker, next_mitzvah_number_must_be)
            section_num = 0
        elif line.find("@22") == 0 and len(line.split(" ")) <= 3:
            section_num, next_sec_number_must_be = parse_section(line, text[mitzvah_num], section_num, next_sec_number_must_be)


        prev_line = line

    return text


def force_order(arr_heb_parenthesis):
    current = 0
    new_arr = []
    for item in arr_heb_parenthesis:
        poss = getGematria(item)
        if poss == current + 1:
            current = poss
            new_arr.append(item)


def iterate_semag(semag_json, brit_vol, which_volume):
    semag_json = semag_json[which_volume][""]
    links_brit_moshe_to_semag = []
    brit_moshe_pos = None
    found_link_in_brit = False
    prev_brit_moshe_ref = None
    for i, mitzvah in enumerate(semag_json):

        for j, semag_segment in enumerate(mitzvah):

            semag_links = re.findall(u"\([\u0590-\u05FF|\"]+\)", semag_segment)
            which_semag_link = 0
            num_links = len(semag_links)
            if (i+1) not in brit_vol or num_links == 0:
                if num_links > 0:
                    print "{} Mitzvah {}".format(which_volume, i+1)
                continue
            semag_ref = "Sefer Mitzvot Gadol, {} {}:{}".format(which_volume, i+1, j+1)



            for brit_moshe_section in brit_vol[i+1]:
                for brit_moshe_seg_count, brit_moshe_segment in enumerate(brit_vol[i+1][brit_moshe_section]):
                    current_brit_moshe_ref = "Brit Moshe, {} {}:{}:{}".format(which_volume, i+1, brit_moshe_section, brit_moshe_seg_count+1)
                    if num_links > which_semag_link and semag_links[which_semag_link] in brit_moshe_segment:
                        if found_link_in_brit:
                            links_brit_moshe_to_semag[-1] = redo_prev_link(links_brit_moshe_to_semag[-1], prev_brit_moshe_ref)
                        links_brit_moshe_to_semag.append({
                            "refs": [semag_ref, current_brit_moshe_ref],
                            "type": "Commentary",
                            "auto": True,
                            "generated_by": "semag_brit_moshe"
                        })
                        found_link_in_brit = True
                        which_semag_link += 1
                    prev_brit_moshe_ref = current_brit_moshe_ref

    return links_brit_moshe_to_semag


def redo_prev_link(link, prev_ref):
    assert prev_ref
    brit_ref, semag_ref = (link["refs"][0], link["refs"][1]) if "Brit Moshe" in link["refs"][0] else (link["refs"][1], link["refs"][0])
    if brit_ref != prev_ref:
        brit_ref = Ref(brit_ref).to(Ref(prev_ref))
        link["refs"] = [brit_ref.normal(), semag_ref]
    return link




    '''
To create links, iterate through SeMaG, for each segment, find all letters in () and then start iterating through Brit Moshe
for each letter, start iterating through Brit Moshe looking for it being found, when it is, set a variable to that segment,
go to the next letter, iterate from last point in Brit Moshe (the variable just mentioned), until we find this new letter.
when we do, we create a link from the SeMaG segment to the range from the segment holding the previous letter to the
segment holding the new letter, excluding the end and including the start.
    '''

if __name__ == "__main__":
    #create_schema()
    brit_vol_2 = parse_text(open("brit moshe vol 2 CORRECTED.txt"), u"@02מצות עשה")
    brit_vol_1 = parse_text(open("brit moshe vol 1.txt"), u"@88מצוה לא תעשה")

    links_vol_1 = iterate_semag(json.load(open("semag.json"))["text"], brit_vol_1, "Volume One")
    links_vol_2 = iterate_semag(json.load(open("semag.json"))["text"], brit_vol_2, "Volume Two")
    post_link(links_vol_1, server=server)
    post_link(links_vol_2, server=server)


    for mitzvah in brit_vol_1:
        brit_vol_1[mitzvah] = convertDictToArray(brit_vol_1[mitzvah])
    for mitzvah in brit_vol_2:
        brit_vol_2[mitzvah] = convertDictToArray(brit_vol_2[mitzvah])
    brit_vol_1 = convertDictToArray(brit_vol_1)
    brit_vol_2 = convertDictToArray(brit_vol_2)

    post_text("Brit Moshe, Volume One", {
            "text": brit_vol_1,
            "language": "he",
            "versionTitle": "Munkatch, 1901",
            "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002023637"
        }, server=server)
    post_text("Brit Moshe, Volume Two", {
            "text": brit_vol_2,
            "language": "he",
            "versionTitle": "Munkatch, 1901",
            "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002023637"
        }, server=server)




