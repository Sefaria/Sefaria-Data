from sources.functions import *
vtitle = "Vilna, 1879"
vsource = "http://aleph.nli.org.il/F/?func=direct&doc_number=001872727&local_base=NNL01"
def create_azharot():
    nodes = """Positive Commandments / מצוות עשה
Negative Commandments / מצוות לא תעשה
Postscript / חתימה""".splitlines()
    r = SchemaNode()
    r.add_primary_titles("Azharot of Solomon ibn Gabirol", "אזהרות לרבי שלמה אבן גבירול")
    r.key = "Azharot of Solomon ibn Gabirol"
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
        if i == 1:
            node.add_structure(["Chapter", "Paragraph"])
        else:
            node.add_structure(["Paragraph"])
        r.append(node)
    r.validate()
    indx = {
        "title": r.key,
        "schema": r.serialize(),
        "categories": ["Halakhah", "Commentary"],
        "dependence": "Commentary",
        "base_text_titles": ["Azharot of Solomon ibn Gabirol"]
    }
    post_index(indx)

def parse_azharot():
    positive, negative, more_info = parse_file_into_pos_and_neg("Azharot.txt", more_info_bool=True)

    positive = {
        "language": "he",
        "text": positive,
        "versionTitle": vtitle,
        "versionSource": vsource
    }
    post_text("Azharot of Solomon ibn Gabirol, Positive Commandments", positive)
    negative = {
        "language": "he",
        "text": negative,
        "versionTitle": vtitle,
        "versionSource": vsource
    }
    post_text("Azharot of Solomon ibn Gabirol, Negative Commandments", negative)
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
    links = []
    for tuple in [("Positive", positive), ("Negative", negative)]:
        for i, siman in enumerate(tuple[1]):
            zohar_ref = "Zohar HaRakia, {} Commandments {}".format(tuple[0], i+1)
            azharot_ref = "Azharot of Solomon ibn Gabirol, {} Commandments {}".format(tuple[0], i+1)
            links.append({"generated_by": "Azharot_to_Zohar_Commandments", "type": "Commentary",
                          "auto": True, "refs": [zohar_ref, azharot_ref]})
    post_link_in_steps(links, int(len(links)/4), sleep_amt=5)
    positive = {
        "language": "he",
        "text": positive,
        "versionTitle": vtitle,
        "versionSource": vsource
    }
    post_text("Zohar HaRakia, Positive Commandments", positive)
    negative = {
        "language": "he",
        "text": negative,
        "versionTitle": vtitle,
        "versionSource": vsource
    }
    post_text("Zohar HaRakia, Negative Commandments", negative)
    index_pos = {
        "language": "he",
        "text": index_pos,
        "versionTitle": vtitle,
        "versionSource": vsource
    }
    post_text("Zohar HaRakia, Index, Positive Commandments", index_pos)
    index_negative = {
        "language": "he",
        "text": index_negative,
        "versionTitle": vtitle,
        "versionSource": vsource
    }
    post_text("Zohar HaRakia, Index, Negative Commandments", index_negative)
    parse_principles()

def parse_principles():
    text = {}
    curr = 0
    with open("principles.txt", 'r') as f:
        for line in f:
            if line.startswith("@11השרש"):
                curr += 1
                text[curr] = [removeAllTags(line)]
            else:
                text[curr].append(removeAllTags(line))
    text = convertDictToArray(text)
    send_text = {
        "language": "he",
        "versionTitle": vtitle,
        "versionSource": vsource,
        "text": text
    }
    post_text("Zohar HaRakia, Principles", send_text)

def link_zohar_to_azharot(mapping):
    links = []
    for key in mapping:
        for azharot_siman, zohar_index_simanim in mapping[key].items():
            for zohar_index_siman in zohar_index_simanim:
                links.append({"generated_by": "Azharot_to_Zohar_index", "auto": True, "type": "Commentary",
                              "refs": ["Zohar HaRakia, Index, {} Commandments {}".format(key.capitalize(), zohar_index_siman),
                                       "Azharot of Solomon ibn Gabirol, {} Commandments {}".format(key.capitalize(), azharot_siman)]})
    #post_link_in_steps(links, int(len(links)/4), sleep_amt=5)
    print(len(links))


def parse_one_depth(file, ref):
    text = []
    with open(file, 'r') as f:
        for line in f:
            text.append(removeAllTags(line))
    send_text = {
        "text": text,
        "language": "he",
        "versionTitle": vtitle,
        "versionSource": vsource
    }
    post_text(ref, send_text)

if __name__ == "__main__":
    create_azharot()
    create_zohar()
    #azharot_to_zohar_index = parse_azharot()
    parse_zohar()
    #link_zohar_to_azharot(azharot_to_zohar_index)
    parse_one_depth("zohar_intro.txt", "Zohar HaRakia, Introduction")
    parse_one_depth("zohar_haRakia_ending.txt", "Zohar HaRakia, Postscript")
    parse_one_depth("Azharot_ending.txt", "Azharot of Solomon ibn Gabirol, Postscript")
