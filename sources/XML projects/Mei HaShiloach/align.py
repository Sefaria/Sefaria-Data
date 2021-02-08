from sources.functions import *
def post_and_check(ref, en, writer, dont_check=False):
    if dont_check == False:
        len_he = len(Ref(ref).text('he').text)
        len_en = len(en)
        if len_he != len_en:
            print("{}: {} english segments vs {} hebrew segments".format(ref, len_en, len_he))
    for i, segment in enumerate(en):
        seg_ref = "{} {}".format(ref, i + 1)
        writer.writerow([seg_ref, segment])
    send_text = {
        "language": "en",
        "versionTitle": "Living waters, the Mei HaShiloach. Trans. and edited by Betsalel Philip Edwards, Jerusalem, J. Aronson 2001",
        "versionSource": "https://www.nli.org.il/he/books/NNL_ALEPH002230918/NLI",
        "text": en
    }
    #post_text(ref, send_text)

probs = set()
parshiyot = {"Sh’lach L’cha": "Shelach", "Vayaqhel": "Vayakhel", "Acharai Mot": "Achrei Mot",
             "Tsav": "Tzav", "Truma": "Terumah", "Ta’azria": "Tazria", "Vezot Habracha": "V'Zot HaBerachah",
             "Ki Teitsei": "Ki Teitzei",
             "B’shalach": "Beshalach", "Nitsavim": "Nitzavim", 'Ha’azinu': "Ha'azinu", "Miqets": "Miketz", 'Re’e': "Re'eh",
             'Vayeisheiv': "Vayeshev", "Mattot": "Matot", 'Beha’alotcha': "Beha'alotcha", "Vaeira": "Vaera", 'Mas’ei': "Masei",
             'Lech L’cha': "Lech Lecha", 'Metsora': "Metzora", "Vayeitse": "Vayetzei", "Tetsave": "Tetzaveh"}

text = {}
other_text = {}
other_books = set()
started_parshiyot = False
with open("Mei HaShiloach.csv", 'r') as f:
    for row in csv.reader(f):
        if "Parshat" in row[0]:
            started_parshiyot = True
            parasha = row[0].replace("Parshat", "Parashat").split("Mei HaShiloach, ")[-1].split(".")[0]
            try:
                for old, new in parshiyot.items():
                    parasha = parasha.replace(old, new)
                index = Ref(parasha).index.title
            except Exception as e:
                probs.add(row[0].replace("Mei HaShiloach, Parshat ", "").split(".")[0])
            if index not in text:
                text[index] = {}
            if parasha not in text[index]:
                text[index][parasha] = []
            ref = row[0].replace("Parshat", index + ",")
            dh = re.search("""^<i>(.*?)</i>""", row[1])
            if dh:
                text[index][parasha].append(row[1])
            else:
                text[index][parasha][-1] += "<br/>"+row[1]
        elif " " in row[0].replace("Mei HaShiloach", "") and started_parshiyot:
            for k, v in {"Megillat Kohellet": "Five Scrolls, Ecclesiastes",
                          "Sefer Shmuel Two": "Prophets, II Samuel", "Hoshea": "Prophets, Hosea",
             "Yeshayahu": "Prophets, Isaiah", "Melachim Two": "Prophets, II Kings",
                          "Sefer Shmuel One": "Prophets, I Samuel", "Megillat Ruth": "Five Scrolls, Ruth",
             "Sefer Mishlei": "Writings, Proverbs", "Sefer Yehoshua": "Prophets, Joshua",
                          "Melachim One": "Prophets, I Kings",
             "Sefer Tehillim": "Writings, Psalms"}.items():
                row[0] = row[0].replace(k, v)
            if "Translator" in row[0]:
                 continue
            row[0] = row[0].replace("Mei HaShiloach, ", "Mei HaShiloach, Volume I, ")
            k = row[0].replace("Mei HaShiloach, Volume I, ", "").split(".")[0]
            if k not in other_text:
                other_text[k] = [""]
            dh = re.search("""^<i>(.*?)</i>""", row[1])
            if dh:
                other_text[k].append(row[1])
            else:
                other_text[k][-1] += "<br/>" + row[1]


with open("aligned.csv", 'w') as f:
    writer = csv.writer(f)
    for index in text:
        for parasha in text[index]:
            ref = "Mei HaShiloach, Volume I, {}, {}".format(index, parasha)
            post_and_check(ref, text[index][parasha], writer)
    for index in other_text:
        ref = "Mei HaShiloach, Volume I, {}".format(index)
        #post_and_check(ref, other_text[index], writer, dont_check=True)

