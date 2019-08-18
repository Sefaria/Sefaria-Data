A few things to note...

- Many of the links for Peninei Halakhah on the sandbox are currently missing because the following inidices must be changed to "is_cited":
mishna berurah, arukh hashulchan, magen avraham

- A few minor manual changes had to be made in the SCRAPED_HTML because of html mistakes (wrote the same paragraph twice, put wrong footnote number, bad url, etc).
As a result, rescraping html should be avoided. If it's really necessary, I think I should be contacted to fix the relevant scrapes.

- For admin/reset of the books, the following links can be used however you see most efficient.
http://penineihalakhah.sandbox.sefaria.org/admin/reset/Peninei_Halakhah,_Shabbat
http://penineihalakhah.sandbox.sefaria.org/admin/reset/Peninei_Halakhah,_Likkutim_I
http://penineihalakhah.sandbox.sefaria.org/admin/reset/Peninei_Halakhah,_Likkutim_II
http://penineihalakhah.sandbox.sefaria.org/admin/reset/Peninei_Halakhah,_Festivals
http://penineihalakhah.sandbox.sefaria.org/admin/reset/Peninei_Halakhah,_The_Nation_and_the_Land
http://penineihalakhah.sandbox.sefaria.org/admin/reset/Peninei_Halakhah,_Berakhot
http://penineihalakhah.sandbox.sefaria.org/admin/reset/Peninei_Halakhah,_High_Holidays
http://penineihalakhah.sandbox.sefaria.org/admin/reset/Peninei_Halakhah,_Shmitta_and_Yovel
http://penineihalakhah.sandbox.sefaria.org/admin/reset/Peninei_Halakhah,_Kashrut_I
http://penineihalakhah.sandbox.sefaria.org/admin/reset/Peninei_Halakhah,_Women's_Prayer
http://penineihalakhah.sandbox.sefaria.org/admin/reset/Peninei_Halakhah,_Prayer
http://penineihalakhah.sandbox.sefaria.org/admin/reset/Peninei_Halakhah,_Family
http://penineihalakhah.sandbox.sefaria.org/admin/reset/Peninei_Halakhah,_Sukkot
http://penineihalakhah.sandbox.sefaria.org/admin/reset/Peninei_Halakhah,_Pesah
http://penineihalakhah.sandbox.sefaria.org/admin/reset/Peninei_Halakhah,_Zemanim
http://penineihalakhah.sandbox.sefaria.org/admin/reset/Peninei_Halakhah,_Simchat_Habayit_V'Birchato

- Before running the script, I'd recommend just skimming the code and reading the comments to get a feel for how everything works. Some global or
otherwise parameters might want to be changed depending on if Rabbi Fischer has sent back the list of title translations, and if you want to print
out the new titles for Shmuel to look at and then add back to the PH_Chapter_Section_Title_Changes.tsv file.

- Because of the way the book names are so heavily used by the script, there isn't an easy way to read from the Peninei_Halakhah_Title_Translations.tsv
file to replace the english translations with Rabbi Fischer's translations. So, if Rabbi Fischer's translations are different from the ones being
used the "num_chapters" and "books" lists on lines 49 and 52, they should be manually replaced by just looking at the file and copying them over.

- If any major, or even minor, changes need to be made to the code, I'm happy to be contacted so that I can make the changes. I understand that
it'd be more difficult for someone else to really know everything that's going on in the script.