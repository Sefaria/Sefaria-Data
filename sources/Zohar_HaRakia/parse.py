from sources.functions import *

def create_azharot():
    nodes = """Positive Commandments / מצוות עשה
Negative Commandments / מצוות לא תעשה
Postscript / חתימה""".splitlines()
    r = SchemaNode()
    r.add_primary_titles("Azharot", "אזהרות")
    r.key = "Azharot"
    for en_he in nodes:
        en, he = en_he.split(" / ")
        node = JaggedArrayNode()
        node.add_primary_titles(en, he)
        node.key = en
        node.add_structure(["Paragraph"])
        r.append(node)
    r.validate()
    indx = {
        "title": r.key,
        "schema": r.serialize(),
        "categories": ["Halakhah"]
    }
    post_index(indx)


def create_zohar():
    r = SchemaNode()
    r.add_primary_titles("Zohar HaRakia", "זוהר הרקיע")
    r.key = "Zohar HaRakia"
    index_node = SchemaNode()
    index_node.add_primary_titles("Index", "מניין המצוות")
    positive = JaggedArrayNode()
    positive.add_primary_titles("Positive Commandments", "מצוות עשה")
    positive.add_structure(["Paragraph"])
    negative = JaggedArrayNode()
    negative.add_primary_titles("Negative Commandments", "מצוות לא תעשה")
    negative.add_structure(["Paragraph"])
    index_node.append(positive)
    index_node.append(negative)
    r.append(index_node)
    nodes = """Introduction / הקדמה
Principles / שרשים
Positive Commandments / מצוות עשה
Negative Commandments / מצוות לא תעשה
Postscript / חתימה""".splitlines()
    for i, en_he in enumerate(nodes):
        en, he = en_he.split(" / ")
        node = JaggedArrayNode()
        node.add_primary_titles(en, he)
        node.key = en
        if i == 0:
            node.add_structure(["Paragraph"])
        elif i == 1:
            node.add_structure(["Chapter", "Paragraph"])
        else:
            node.add_structure(["Section", "Paragraph"])
        r.append(node)
    r.validate()
    indx = {
        "title": r.key,
        "schema": r.serialize(),
        "categories": ["Halakhah", "Commentary"],
        "dependence": "Commentary",
        "base_text_titles": ["Azharot"]
    }
    post_index(indx)

def parse_azharot():
    positive, negative, more_info = parse_file_into_pos_and_neg("Azharot.txt", more_info_bool=True)
    return more_info

def parse_file_into_pos_and_neg(file, tag="@22", more_info_bool=False):
    positive = {}
    negative = {}
    mitzvah_num = 0
    current = positive
    more_info_dict = {"positive": {}, "negative": {}}
    current_more_info = "positive"
    with open(file, 'r') as f:
        for line in f:
            mitzvah = re.search("{}(.*)".format(tag), line)
            if mitzvah:
                mitzvah_num = getGematria(mitzvah.group(1).split()[0])
                if mitzvah_num in current and mitzvah_num == 1:
                    current = negative
                    current_more_info = "negative"
                assert mitzvah_num not in current
                current[mitzvah_num] = ""
                if more_info_bool and mitzvah.group(1).count(" ") >= 1:
                    more_info = [getGematria(x) for x in mitzvah.group(1).split()[1:]]
                    assert mitzvah_num not in more_info_dict
                    more_info_dict[current_more_info][mitzvah_num] = []
                    for siman in more_info:
                        more_info_dict[current_more_info][mitzvah_num].append(siman)
            else:
                current[mitzvah_num] += removeAllTags(line).strip() + "\n"

    positive = convertDictToArray(positive)
    negative = convertDictToArray(negative)

    if more_info_bool:
        return positive, negative, more_info_dict
    else:
        return positive, negative

def parse_zohar():
    index_pos, index_negative = parse_file_into_pos_and_neg("zohar_haRakia_index.txt", tag="@23")
    positive, negative = parse_file_into_pos_and_neg("zohar_haRakia.txt")

def link_zohar_to_azharot():
    pass

if __name__ == "__main__":
    create_azharot()
    create_zohar()
    azharot_to_zohar_index = parse_azharot()
    parse_zohar()
    link_zohar_to_azharot()