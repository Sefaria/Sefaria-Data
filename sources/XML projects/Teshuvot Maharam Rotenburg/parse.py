import django
django.setup()
from data_utilities.XML_to_JaggedArray import XML_to_JaggedArray
SERVER = "http://proto.sefaria.org"
import re
import bleach
import csv

def reorder_modify(text):
    return bleach.clean(text, strip=True)


def make_map(csv_file):
    _map = {}
    with open(csv_file) as f:
        reader = csv.reader(f)
        for row in reader:
            orig = row[1]
            new = row[2]
            if "," in new:
                new_segments = [int(el.replace(" ", "")) for el in new.split(",")]
                for i, el in enumerate(new_segments):
                    _map[el] = u"{}.{}".format(orig, i+1)
            else:
                new = int(new)
                _map[new] = u"{}.1".format(orig)
    return _map

def make_new_csv_from_map(old_csv_file, map_, map_name, title):
    with open(old_csv_file) as old_csv:
        reader = csv.reader(old_csv)
        for row in reader:
            old_ref, text = row
            old_ref = ".".join(old_ref.split(".")[1:])
            old_siman, old_seif = old_ref.split(".")
            new_siman_seif = map_[old_siman]
            new_ref = "{}, {} Edition {}:{}".format(title, map_name)



if __name__ == "__main__":
    post_info = {}
    post_info["language"] = "en"
    post_info["server"] = SERVER
    allowed_tags = ["book", "intro", "part", "chapter", "p", "ftnote", "title", "ol", "footnotes", "appendix", "h1"]
    allowed_attributes = ["id"]
    p = re.compile("\d+a?\.")

    post_info["versionTitle"] = "Teshuvot Maharam Rotenburg"
    post_info["versionSource"] = "http://ste.sefaria.org"
    title = "Teshuvot Maharam"
    file_name = "RMeirOfRotenberg.xml"

    #open csv files containing english to hebrew mapping
    # lemberg = make_map("lemberg.csv")
    # cremona = make_map("cremona.csv")
    # prague = make_map("prague.csv")


    parser = XML_to_JaggedArray(title, file_name, allowed_tags, allowed_attributes, post_info, change_name=True, image_dir="./images",
                                titled=True, print_bool=True)
    parser.set_funcs(reorder_test=lambda x: x.tag == "h1", reorder_modify=reorder_modify)
    parser.run()

    #Instead of creating dictionaries above, what about doing it below?  Make a map of the text instead of refs to array of text
    #In Prague, when we encounter 66 -> 82, 89; we make sure they are in order, then combine all of the text of 82 and 89
    #and put it inside 66
    siman_to_text = {}
    with open("RMeirOfRotenberg.csv") as csv_f:
        reader = csv.reader(csv_f)
        for row in reader:
            old_ref, text = row
            current_siman = old_ref.split(".")[1]
            if not current_siman in siman_to_text.keys():
                siman_to_text[current_siman] = []
            siman_to_text[current_siman].append(text)

    for title, file in zip(["Lemberg", "Prague", "Cremona"], ["lemberg.csv", "prague.csv", "cremona.csv"]):
        with open(file) as f:
            reader = csv.reader(f)
            for row in reader:
                he = row[1]
                en = row[2]
                en_simanim = sorted([el.replace(" ", "") for el in en.split(",")])
                combined_text = []
                for en_siman in en_simanim:
                    combined_text += siman_to_text[en_siman]


    # make_new_csv_from_map("RMeirOfRotenberg-Vol1.csv", lemberg, "Lemberg", "Teshuvot Maharam")







