import os
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
