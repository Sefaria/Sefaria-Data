# encoding=utf-8

import os
import bs4
import csv
import json

'''
Shabbat 21-24 missing
Yevamot 12-16 missing (the text currently up is partial)
Makot 3 missing
'''


with open('guggenheimer_titles.json') as fp:
    titles_to_file_mapping = json.load(fp)
book_mapping = {
    value: key.replace("Jerusalem Talmud", "JTmock") for key, value in titles_to_file_mapping.items()
}

xml_dir, output_dir = 'GuggenheimerXmls', 'code_output/missing_base'
for xml_file, missing_book, missing_chapters in [
    ['moed_sabbat_eruvin.xml', 'JTmock Shabbat', [21,22,23,24]],
    ['neziqin_sanhedrin_makkot_horaiot.xml', 'JTmock Makkot', [3]],
    ['nasim_yebamot.xml', 'JTmock Yevamot', [12,13,14,15,16]]
]:
    with open(os.path.join(xml_dir, xml_file)) as fp:
        soup = bs4.BeautifulSoup(fp, 'xml')
    books = soup.find_all('book')
    for book in books:
        title = book_mapping[book['id']]
        if title != missing_book:
            continue
        title = title.replace("JTmock ", "")
        with open('{}/{}.csv'.format(output_dir, title), 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            for chapter in book.find_all('chapter'):
                if int(chapter["num"]) in missing_chapters:
                    chap_label = "{} {}".format(title, chapter["num"])
                    parts = chapter.find_all(["halacha","mishna"])
                    for part in parts:
                        part_label = part.label.get_text()
                        paras = part.find_all("source_para")
                        for para in paras:
                            para_text = para.get_text().replace("\n\n\n"," ").replace("  "," ").strip()
                            csv_writer.writerow([chap_label, part_label, para_text])

