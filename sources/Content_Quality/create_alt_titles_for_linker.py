import django
django.setup()
from sefaria.model import *
import csv
alt_titles_dict = {}
alt_titles_dict["Shulchan Arukh, Orach Chayim"] = \
    ["Shulhan Arukh OH", "Shulchan Aruch O.C.",
    "Orach Chaim", "S.A. O.C.", "SA OC"]
alt_titles_dict["Shulchan Arukh, Yoreh De'ah"] = ["S.A. Y.D.", "SA YD"]
alt_titles_dict["Shulchan Arukh, Even HaEzer"] = ["SA EH", "S.A. E.H."]
alt_titles_dict["Shulchan Arukh, Choshen Mishpat"] = ["SA CM", "S.A. C.M."]
for title in library.get_indexes_in_category("Bavli"):
    alt_titles_dict[title] = ["BT {}".format(title), "Talmud {}".format(title)]
for title in library.get_indexes_in_category("Yerushalmi"):
    alt_titles_dict[title] = [title.replace("Jerusalem Talmud", "JT")]
alt_titles_dict["Bava Batra"].append("Bava Basra")
#alt_titles_dict["Jerusalem Talmud Bava Batra"].append("Jerusalem Talmud Bava Basra")
alt_titles_dict["Mishnah Berurah"] = ["M.B.", "MB", "Mishnah Berurah O.C.", "Mishna Brurah"]
alt_titles_dict["Kitzur Shulchan Aruch"] = ["Kitzur Shulchan Aruch Orach Chaim"]
with open("output_of_alt_titles_for_linker.csv", 'w') as output:
    writer = csv.writer(output)
    writer.writerow(["Index", "New Alt Title"])
    for index_title, alt_titles in alt_titles_dict.items():
        index = library.get_index(index_title)
        print(index_title)
        root = index.nodes
        curr_alt_titles = root.get_titles('en')
        added_alt_titles = []
        for alt_title in alt_titles:
            if alt_title not in curr_alt_titles:
                added_alt_titles.append(alt_title)
                root.add_title(alt_title, "en")
        writer.writerow([index_title, *added_alt_titles])
        index.save()