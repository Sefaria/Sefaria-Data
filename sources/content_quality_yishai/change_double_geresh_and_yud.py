import django
django.setup()
from sefaria.helper.text import modify_many_texts_and_make_report

versionTitles = ["Torat Emet 357", "Tosefta Kifshuta. Third Augmented Edition, JTS 2001", "Tikkunei Zohar", "Torat Emet 363", "Hebrew Translation", "Vilna, 1874", "ToratEmet", "On Your Way", "Vilna Edition", "Torat Emet Freeware Shulchan Aruch", "Zohar Chadash", "Sefer HaChinukh -- Torat Emet", "Torat Emet", "Wikisource Shulchan Aruch", "On Your Way New", "Kobetz Teshuvot HaRambam, 1859", "Be'er Mayim Chaim on Chofetz Chaim", "Derech Chaim, with footnotes and annotations by Rabbi Yehoshua D. Hartman, Machon Yerushalyim, 2005-2010", "Ohr Chadash, with footnotes and annotations by Rabbi Yehoshua D. Hartman, Machon Yerushalyim, 2014", "Aruch HaShulchan, Vilna 1923-29", "Leipzig :  H.L. Shnuis, 1859", "The Tosefta according to to codex Vienna. Third Augmented Edition, JTS 2001", "Shulhan Arukh, Hoshen ha-Mishpat, Lemberg, 1898", "Gevurot Hashem, with footnotes and annotations by Rabbi Yehoshua D. Hartman, Machon Yerushalyim, 2015-2020 new", "Tiferet Yisrael, with footnotes and annotations by Rabbi Yehoshua D. Hartman, Machon Yerushalyim, 2010", "Chofetz Chaim", "Romemot El, Warsaw 1875", "Be'er HaGolah, with footnotes and annotations by Rabbi Yehoshua D. Hartman, Machon Yerushalyim, 2002", "Netivot Olam, Netiv Hatorah, with footnotes and annotations by Rabbi Yehoshua D. Hartman, Machon Yerushalyim, 2012", "Sefer Baal Shem Tov. Lodz, 1938", "Gur Aryeh, Machon Yerushalyim, 1989-1995"]

r=modify_many_texts_and_make_report(lambda x: (x.replace("'''", '\'"').replace("''", '"'), x.count("''")), {'versionTitle': {'$in': versionTitles}})
with open('geresh.csv', 'wb') as fp:
    fp.write(r)
r=modify_many_texts_and_make_report(lambda x: (x.replace("ײ", 'יי'), x.count("ײ")), {'actualLanguage': {'$ne': 'yi'}})
with open('yud.csv', 'wb') as fp:
    fp.write(r)
