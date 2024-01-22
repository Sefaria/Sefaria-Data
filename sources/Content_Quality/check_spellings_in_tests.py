import django
django.setup()
from sefaria.model import *
import os
import re

def tokenizer(s):
    s = re.sub(r'<.+?>', '', s).strip()
    return re.split(r'\s+', s)


nodes = library.get_index("Megillat Ta'anit").nodes
index_list, ref_list = nodes.text_index_map(tokenizer=tokenizer)
assert index_list[1] == 9
assert index_list[2] == 20
assert index_list[5] == 423

#from sefaria.model.linker.tests.linker_test_utils import create_raw_ref_data
# first = [create_raw_ref_data(['@Babli', '#28b', '~,', '#31a'], "Jerusalem Talmud Taanit 1:1:3", 'en'),
#  ("Taanit 28b", "Taanit 31a")],  # non-cts with talmud
# second = [create_raw_ref_data(['@Exodus', '#21', '#1', '~,', '#3', '~,', '#22', '#5'], "Jerusalem Talmud Taanit 1:1:3", 'en'),
#  ("Exodus 21:1", "Exodus 21:3", "Exodus 22:5")],  # non-cts with tanakh
# third = create_raw_ref_data(['@Roš Haššanah', '#4', '#Notes 42', '^–', '#43'], "Jerusalem Talmud Taanit 1:1:3", "en"),
             #("Jerusalem Talmud Rosh Hashanah 4",), #marks=pytest.mark.xfail(
        #reason="currently dont support partial ranged ref match. this fails since Notes is not a valid address type of JT")),

trefs = ["Berakhot 2a-b", "Rashi on Shabbat 15a:10-13",
         "Shulchan Arukh, Even HaEzer 2:2-4"]  # NOTE the m-dash in the Shulchan Arukh ref
test_strings = [
    "I am going to quote a range. hopefully you can parse it. ({}) plus some other stuff.".format(temp_tref) for
    temp_tref in trefs
]
for i, test_string in enumerate(test_strings):
    matched_refs = library.get_refs_in_string(test_string, lang='en', citing_only=False)
    assert matched_refs == [Ref(trefs[i])]

words = """Rabbenu
Bereishit Rabbah
Parashat Bereishit
Chayim
HaChayim
Maamar Mezake HaRabim  
Chidushei
Megilat Esther on Sefer HaMitzvot
Or 
Bamidbar
Achronim
Yitzhak
Zerachiah ha-Levi of Girona
Biur Halacha
Kessef Mishneh
Yorah De'ah
Raavad
Saadia
Pardes Rimonim 
Siddur Tehilat Hashem
Likutei
Tefilot
Taanit
Beha'alotcha
Sh'lach
Eichah
Shaarei
Laish
Daat Zkenim
Yehiel 
Ben-Zion Meir Hai Uziel
Hilchos Talmud Torah
Baal HaSulam
Petikha LePerush HaSulam
Hakdamot L'Chochmat HaEmet 
Halevi
Hagahot 
Yaavetz 
Beur
tzadik""".splitlines()
def search_for_string(root_dir, search_string):
    for subdir, dirs, files in os.walk(root_dir):
        for filename in files:
            filepath = os.path.join(subdir, filename)
            if "test" not in filepath:
                continue
            try:
                with open(filepath, 'r', encoding='utf-8') as file:
                    if search_string in file.read():
                        print(f"String '{search_string}' found in: {filepath}")
            except (UnicodeDecodeError, PermissionError, FileNotFoundError):
                # Skip files that cannot be read; you might need to handle other exceptions as well.
                pass

# Replace 'path/to/directory' with the directory path and 'search_term' with the string you're searching for.
for word in words:
    search_for_string('../../../Sefaria-Project/sefaria', word)
    search_for_string('../../../Sefaria-Project/reader', word)