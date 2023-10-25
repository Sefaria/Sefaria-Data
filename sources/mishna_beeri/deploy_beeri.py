import django
import subprocess
from sources.local_settings import API_KEY
django.setup()
superuser_id = 171118

books = [
    "Mishnah Berakhot",
    "Mishnah Peah",
    "Mishnah Demai",
    "Mishnah Kilayim",
    "Mishnah Sheviit",
    "Mishnah Terumot",
    "Mishnah Maasrot",
    "Mishnah Maaser Sheni",
    "Mishnah Challah",
    "Mishnah Orlah",
    "Mishnah Bikkurim",
    "Mishnah Shabbat",
    "Mishnah Eruvin",
    "Mishnah Pesachim",
    "Mishnah Shekalim",
    "Mishnah Yoma",
    "Mishnah Sukkah",
    "Mishnah Beitzah",
    "Mishnah Rosh Hashanah",
    "Mishnah Taanit",
    "Mishnah Megillah",
    "Mishnah Moed Katan",
    "Mishnah Chagigah",
    "Mishnah Yevamot",
    "Mishnah Ketubot",
    "Mishnah Nedarim",
    "Mishnah Nazir",
    "Mishnah Sotah",
    "Mishnah Gittin",
    "Mishnah Kiddushin",
    "Mishnah Bava Kamma",
    "Mishnah Bava Metzia",
    "Mishnah Bava Batra",
    "Mishnah Sanhedrin",
    "Mishnah Makkot",
    "Mishnah Shevuot",
    "Mishnah Eduyot",
    "Mishnah Avodah Zarah",
    "Mishnah Avot",
    "Mishnah Horayot",
    "Mishnah Zevachim",
    "Mishnah Menachot",
    "Mishnah Chullin",
    "Mishnah Bekhorot",
    "Mishnah Arakhin",
    "Mishnah Temurah",
    "Mishnah Keritot",
    "Mishnah Meilah",
    "Mishnah Tamid",
    "Mishnah Middot",
    "Mishnah Kinnim",
    "Mishnah Kelim",
    "Mishnah Oholot",
    "Mishnah Negaim",
    "Mishnah Parah",
    "Mishnah Tahorot",
    "Mishnah Mikvaot",
    "Mishnah Niddah",
    "Mishnah Makhshirin",
    "Mishnah Zavim",
    "Mishnah Tevul Yom",
    "Mishnah Yadayim",
    "Mishnah Oktzin"
]



if __name__ == '__main__':
    for book in books:
        script_path = "move_draft_text.py"
        book_name = book
        version_title = "Mishnah based on the Kaufmann manuscript, edited by Dan Be'eri"
        version_language = "he"
        noindex = "--noindex"
        api_key = API_KEY
        data_url = "https://www.sefaria.org"

        # Run the script with the specified parameters
        subprocess.run([
            "python", script_path, book_name, "-v", version_language + ":"+version_title, noindex, "-k", api_key, "-d", data_url
        ])