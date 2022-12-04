import csv
from sefaria.model import *

ALLOWED_TAGS = ("i", "b", "br", "u", "strong", "em", "big", "small", "img", "sup", "sub", "span", "a")
ALLOWED_ATTRS = {
    'sup': ['class'],
    'span': ['class', 'dir'],
    'i': ['data-overlay', 'data-value', 'data-commentator', 'data-order', 'class', 'data-label', 'dir'],
    'img': lambda name, value: name == 'src' and value.startswith("data:image/"),
    'a': ['dir', 'class', 'href', 'data-ref', "data-ven", "data-vhe"],
}

number_map = {
    "Chapter One": 1,
    "Chapter 1": 1,
    "Chapter Two": 2,
    "Chapter 2": 2,
    "Chapter Three": 3,
    "Chapter 3": 3,
    "Chapter Four": 4,
    "Chapter 4": 4,
    "Chapter Five": 5,
    "Chapter 5": 5,
    "Chapter Six": 6,
    "Chapter 6": 6,
    "Chapter Seven": 7,
    "Chapter 7": 7,
    "Chapter Eight": 8,
    "Chapter 8": 8,
    "Chapter Nine": 9,
    "Chapter 9": 9,
    "Chapter Ten": 10,
    "Chapter 10": 10,
    "Chapter Eleven": 11,
    "Chapter 11": 11,
    "Chapter Twelve": 12,
    "Chapter 12": 12,
    "Chapter Thirteen": 13,
    "Chapter 13": 13,
    "Chapter Fourteen": 14,
    "Chapter 14": 14,
    "Chapter Fifteen": 15,
    "Chapter 15": 15,
    "Chapter Sixteen": 16,
    "Chapter 16": 16,
    "Chapter Seventeen": 17,
    "Chapter 17": 17,
    "Chapter Eighteen": 18,
    "Chapter 18": 18,
    "Chapter Nineteen": 19,
    "Chapter 19": 19,
    "Chapter Twenty": 20,
    "Chapter 20": 20,
    "Chapter Twenty One": 21,
    "Chapter 21": 21,
    "Chapter Twenty Two": 22,
    "Chapter 22": 22,
    "Chapter Twenty Three": 23,
    "Chapter 23": 23,
    "Chapter Twenty Four": 24,
    "Chapter 24": 24,
    "Chapter Twenty Five": 25,
    "Chapter 25": 25,
    "Chapter Twenty Six": 26,
    "Chapter 26": 26,
    "Chapter Twenty Seven": 27,
    "Chapter 27": 27,
    "Chapter Twenty Eight": 28,
    "Chapter 28": 28,
    "Chapter Twenty Nine": 29,
    "Chapter 29": 29,
    "Chapter Thirty": 30,
    "Chapter 30": 30,
}

chabad_book_names = ['Yesodei haTorah', "De'ot", 'Talmud Torah', 'Avodat Kochavim', 'Teshuvah', "Kri'at Shema",
                     'Tefilah and Birkat Kohanim', 'Tefillin, Mezuzah and Sefer Torah', 'Tzitzit', 'Berachot', 'Milah',
                     'Order of Prayers', 'Shabbat', 'Eruvin', 'Shevitat Asor', 'Shevitat Yom Tov', "Chametz U'Matzah",
                     'Shofar, Sukkah, vLulav', 'Shekalim', 'Kiddush HaChodesh', "Ta'aniyot", "Megillah v'Chanukah",
                     'Ishut', 'Gerushin', 'Yibbum vChalitzah', 'Naarah Betulah', 'Sotah', 'Issurei Biah',
                     "Ma'achalot Assurot", 'Shechitah', 'Shvuot', 'Nedarim', 'Nezirut', 'Arachim Vacharamim',
                     'Kilaayim', 'Matnot Aniyim', 'Terumot', 'Maaser', 'Maaser Sheini', 'Bikkurim', 'Shemita',
                     'Beit Habechirah', 'Klei Hamikdash', 'Biat Hamikdash', 'Issurei Mizbeiach', 'Maaseh Hakorbanot',
                     'Temidin uMusafim', 'Pesulei Hamukdashim', 'Avodat Yom haKippurim', 'Me`ilah', 'Korban Pesach',
                     'Chagigah', 'Bechorot', 'Shegagot', 'Mechussarey Kapparah', 'Temurah', "Tum'at Met",
                     'Parah Adumah', "Tum'at Tsara'at", "Metamme'ey Mishkav uMoshav", "She'ar Avot haTum'ah",
                     "Tum'at Okhalin", 'Kelim', 'Mikvaot', 'Hilchot Nizkei Mamon', 'Genevah', "Gezelah va'Avedah",
                     'Chovel uMazzik', 'Rotzeach uShmirat Nefesh', 'Mechirah', 'Zechiyah uMattanah', 'Shechenim',
                     'Sheluchin veShuttafin', 'Avadim', 'Sechirut', "She'elah uFikkadon", 'Malveh veLoveh',
                     'To’en veNit’an', 'Nachalot', 'Sanhedrin veha’Onashin haMesurin lahem', 'Edut', 'Mamrim', 'Avel',
                     'Melachim uMilchamot']
sefaria_book_names = [
    'Foundations of the Torah',
    'Human Dispositions',
    'Torah Study',
    'Foreign Worship and Customs of the Nations',
    'Repentance',
    'Reading the Shema',
    'Prayer and the Priestly Blessing',
    'Tefillin, Mezuzah and the Torah Scroll',
    'Fringes',
    'Blessings',
    'Circumcision',
    'The Order of Prayer',
    'Sabbath',
    'Eruvin',
    'Rest on the Tenth of Tishrei',
    'Rest on a Holiday',
    'Leavened and Unleavened Bread',
    'Shofar, Sukkah and Lulav',
    'Sheqel Dues',
    'Sanctification of the New Month',
    'Fasts',
    'Scroll of Esther and Hanukkah',
    'Marriage',
    'Divorce',
    'Levirate Marriage and Release',
    'Virgin Maiden',
    'Woman Suspected of Infidelity',
    'Forbidden Intercourse',
    'Forbidden Foods',
    'Ritual Slaughter',
    'Oaths',
    'Vows',
    'Nazariteship',
    'Appraisals and Devoted Property',
    'Diverse Species',
    'Gifts to the Poor',
    'Heave Offerings',
    'Tithes',
    'Second Tithes and Fourth Year\'s Fruit',
    'First Fruits and other Gifts to Priests Outside the Sanctuary',
    'Sabbatical Year and the Jubilee',
    'The Chosen Temple',
    'Vessels of the Sanctuary and Those who Serve Therein',
    'Admission into the Sanctuary',
    'Things Forbidden on the Altar',
    'Sacrificial Procedure',
    'Daily Offerings and Additional Offerings',
    'Sacrifices Rendered Unfit',
    'Service on the Day of Atonement',
    'Trespass',
    'Paschal Offering',
    'Festival Offering',
    'Firstlings',
    'Offerings for Unintentional Transgressions',
    'Offerings for Those with Incomplete Atonement',
    'Substitution',
    'Defilement by a Corpse',
    'Red Heifer',
    'Defilement by Leprosy',
    'Those Who Defile Bed or Seat',
    'Other Sources of Defilement',
    'Defilement of Foods',
    'Vessels',
    'Immersion Pools',
    'Damages to Property',
    'Theft',
    'Robbery and Lost Property',
    'One Who Injures a Person or Property',
    'Murderer and the Preservation of Life',
    'Sales',
    'Ownerless Property and Gifts',
    'Neighbors',
    'Agents and Partners',
    'Slaves',
    'Hiring',
    'Borrowing and Deposit',
    'Creditor and Debtor',
    'Plaintiff and Defendant',
    'Inheritances',
    'The Sanhedrin and the Penalties within their Jurisdiction',
    'Testimony',
    'Rebels',
    'Mourning',
    'Kings and Wars'
]


def create_book_name_map(chabad_book_names, sefaria_book_names):
    """
    This function creates a map between the Chabad Rambam names to the Sefaria Rambam names
    """

    # Confirmed that book names aligned, creating map
    name_map = {}
    for i in range(len(chabad_book_names)):
        name_map[chabad_book_names[i]] = sefaria_book_names[i]
    return name_map


def export_data_to_csv(list, file_name, headers_list):
    """
    This function writes the data to a new CSV
    """
    with open(f"{file_name}.csv", 'w+') as csvfile:
        headers = headers_list
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writerows(list)


def add_chabad_book_names_alt_titles():
    name_map = create_book_name_map(chabad_book_names, sefaria_book_names)

    for chabad_book in chabad_book_names:
        sef_book = name_map[chabad_book]
        index = library.get_index(f"Mishneh Torah, {sef_book}")
        new_alt_title = f"Hilchot {chabad_book}"
        print(f"Adding {new_alt_title}")
        index.nodes.add_title(new_alt_title, "en")
        index.save()
