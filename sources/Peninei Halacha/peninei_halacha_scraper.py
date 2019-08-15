# -*- coding: utf-8 -*-
import django
django.setup()
from sefaria.model import *
from sources.functions import *
import requests
from bs4 import BeautifulSoup, element
import re
import PIL
from PIL import Image

VERSION_TITLE_HE = "Peninei Halakhah, Yeshivat Har Bracha"
VERSION_SOURCE_HE = "https://ph.yhb.org.il"
VERSION_TITLE_EN = "Peninei Halakhah, English ed. Yeshivat Har Bracha"
VERSION_SOURCE_EN = "https://ph.yhb.org.il/en"

jar = requests.cookies.RequestsCookieJar()
jar.set("wp-postpass_b0cab8db5ce44e438845f4dedf0fcf4f", "%24P%24BH2d6c1lhrllIz02CYT36lWgURQXVe1")

img_text_re = re.compile(u"(.*?)\(max-width.*?(br/>|/p>|/>)")
footnote_re = re.compile(u"\[[0123456789]+\]")
pics = 0
num_chapters = {"Shabbat": 30, "Likkutim I": 11, "Likkutim II": 17, "Festivals": 13, "The Nation and the Land": 10,
                "Berakhot": 18, "High Holidays": 10, "Shmitta and Yovel": 11, "Kashrut I": 19, "Women's Prayer": 24,
                "Prayer": 26, "Family": 10, "Sukkot": 8, "Pesah": 16, "Zemanim": 17, "Simchat Habayit V'Birchato": 10}
books = [("Shabbat", u"שבת", 1),
         ("Prayer", u"תפילה", 2),
         ("Women's Prayer", u"תפילת נשים", 3),
         ("Pesah", u"פסח", 4),
         ("Zemanim", u"זמנים", 5),
         ("The Nation and the Land", u"העם והארץ", 6),
         ("Likkutim I", u"ליקוטים א", 7),
         ("Likkutim II", u"ליקוטים ב", 8),
         ("Berakhot", u"ברכות", 10),
         ("Family", u"משפחה", 11),
         ("Festivals", u"מועדים", 12),
         ("Sukkot", u"סוכות", 13),
         ("Simchat Habayit V'Birchato", u"שמחת הבית וברכתו", 14),
         ("High Holidays", u"ימים נוראים", 15),
         ("Shmitta and Yovel", u"שביעית ויובל", 16),
         ("Kashrut I", u"כשרות א – הצומח והחי", 17)]

# ------------------------------------------------
# book_list = [5, 6, 7, 8, 9, 11, 12, 13, 14, 15]
book_list = [2]
lang = "both"
# ------------------------------------------------

def do_peninei_halakhah(book_name_en, book_name_he, url_number, lang="he"):
    if lang not in ["he", "en", "both"]:
        raise Exception("Language field can only be \"he\", \"en\", or \"both\".")
    if book_name_en == "The Nation and the Land":
        introduction_he, chapters_he, ordered_chapter_titles_he, section_titles_he = get_soup(book_name_en, url_number, lang)
        goren_intro, supp_sections, supp_section_titles, sup_all_siman_titles = supplement_parser()
        # print "Book title: " + book_name_he
        # print
        # for chapter in ordered_chapter_titles_he:
        #     print "Chapter title: " + chapter
        #     for section in section_titles_he[chapter]:
        #         print "Section title: " + section
        # for section in supp_section_titles:
        #     for siman in sup_all_siman_titles[section]:
        #         print "Siman title: " + siman
        # post_index_to_server(book_name_en, book_name_he, ordered_chapter_titles_he, section_titles_he, supp_section_titles=supp_section_titles, sup_all_siman_titles=sup_all_siman_titles)
        # post_text_to_server(book_name_en, introduction_he, chapters_he, lang, goren_intro, supp_sections)

    elif lang == "both":
        download_html(book_name_en, url_number, "he")
        download_html(book_name_en, url_number, "en")
        introduction_he, chapters_he, ordered_chapter_titles_he, section_titles_he = get_soup(book_name_en, url_number, "he")
        introduction_en, chapters_en, ordered_chapter_titles_en, section_titles_en = get_soup(book_name_en, url_number, "en")
        post_index_to_server(book_name_en, book_name_he, [ordered_chapter_titles_he, ordered_chapter_titles_en], [section_titles_he, section_titles_en], both=True)
        post_text_to_server(book_name_en, introduction_he, chapters_he, "he")
        post_text_to_server(book_name_en, introduction_en, chapters_en, "en")
    else:
        download_html(book_name_en, url_number, lang)
        introduction, chapters, ordered_chapter_titles, section_titles = get_soup(book_name_en, url_number, lang)
        # print "Book title: " + book_name_he
        # print
        # for chapter in ordered_chapter_titles:
        #     print "Chapter title: " + chapter
        #     for section in section_titles[chapter]:
        #         print "Section title: " + section
        if lang == "he":
            post_index_to_server(book_name_en, book_name_he, ordered_chapter_titles, section_titles)
        post_text_to_server(book_name_en, introduction, chapters, lang)


def download_html(book_name, url_number, lang="he"):
    try:
        os.mkdir("./Scraped_HTML/{}_{}".format(book_name, lang))
    except OSError:
        return

    # DOES NOT WORK CONSISTENTLY FOR DIFFERENT BOOKS
    if lang == "he":
        if url_number in [11,6]:
            url = "https://ph.yhb.org.il/{}-00/".format('%02d' % url_number)
        elif url_number == 17:
            url = u"https://ph.yhb.org.il/פתח-דבר/"
        else:
            url = "https://ph.yhb.org.il/{}-00-00/".format('%02d' % url_number)
        text = requests.get(url, cookies=jar).text.encode("utf8")
        file = open("./Scraped_HTML/{}_he/Introduction.html".format(book_name), "w+")
        file.write(text)
        file.close()

    for curr_chapter in range(num_chapters[book_name]):
        total_num_sections = int(get_num_sections(book_name, curr_chapter+1, lang, url_number, scrape=True))

        for num_section in range(total_num_sections):
            url = "https://ph.yhb.org.il/{}/{}-{}-{}/".format(lang, '%02d' % url_number, '%02d' % (curr_chapter+1), '%02d' % (num_section+1))
            text = requests.get(url, cookies=jar).text.encode("utf8")
            file = open("./Scraped_HTML/{}_{}/Chapter_{}_Section_{}.html".format(book_name, lang, curr_chapter+1, num_section+1), "w+")
            file.write(text)
            file.close()


def get_num_sections(book_name, curr_chapter, lang, url_number, scrape=False):
    if scrape:
        url = "https://ph.yhb.org.il/{}/{}-{}-01/".format(lang, '%02d' % url_number, '%02d' % (curr_chapter))
        source = requests.get(url, cookies=jar).text
    else:
        file = open("./Scraped_HTML/{}_{}/Chapter_{}_Section_1.html".format(book_name, lang, curr_chapter))
        source = file.read()
    soup = BeautifulSoup(source, 'lxml')
    num_sections = soup.find_all("div", style="display:block")
    for section in num_sections[1].find_all("li", class_="collapsing categories item"):
        None

    return section.a["href"].split("-")[2][:2]


def get_chapter_title(book_name, curr_chapter, lang, url_number, scrape=False):
    if scrape:
        url = "https://ph.yhb.org.il/{}/{}-{}-01/".format(lang, '%02d' % url_number, '%02d' % (curr_chapter))
        source = requests.get(url, cookies=jar).text
    else:
        file = open("./Scraped_HTML/{}_{}/Chapter_{}_Section_1.html".format(book_name, lang, curr_chapter))
        source = file.read()
    soup = BeautifulSoup(source, 'lxml')
    chapter_title = soup.find("div", class_="entry-utility").a.text

    return chapter_title


def get_soup(book_name, url_number, lang="he"):
    final_comment = False
    chapters = []
    introduction = []
    titles = {}
    ordered_chapter_titles = []
    aleph_bet = ""

    for curr_chapter in range(num_chapters[book_name]+1):
        sections = []
        section_titles = []

        if curr_chapter == 0 and lang == "en":
            continue

        if curr_chapter:
            total_num_sections = int(get_num_sections(book_name, curr_chapter, lang, url_number))
            chapter_title = get_chapter_title(book_name, curr_chapter, lang, url_number)
            ordered_chapter_titles.append(chapter_title)
        else:
            total_num_sections = 1

        for num_section in range(total_num_sections):
            if book_name == "Prayer" and curr_chapter == 8 and num_section == 1 and lang == "he":
                sections.append([u"p1", u"p2", u"p3", u"p4", u"p5"])
            elif book_name == "Women's Prayer" and curr_chapter == 11 and num_section == 10 and lang == "he":
                sections.append([u"p1", u"p2", u"p3", u"p4", u"p5", u"p6", u"p7", u"p8", u"p9"])
            elif book_name == "Women's Prayer" and curr_chapter == 21 and num_section == 4 and lang == "he":
                sections.append([u"p1", u"p2"])
            elif book_name == "Women's Prayer" and curr_chapter == 21 and num_section == 5 and lang == "he":
                sections.append([u"p1", u"p2", u"p3", u"p4", u"p5", u"p6"])
            paragraphs = []
            if curr_chapter:
                file = open("./Scraped_HTML/{}_{}/Chapter_{}_Section_{}.html".format(book_name, lang, curr_chapter, num_section+1))
            else:
                file = open("./Scraped_HTML/{}_he/Introduction.html".format(book_name))
            source = file.read()
            soup = BeautifulSoup(source, 'lxml')

            if curr_chapter:
                curr_section_title = soup.title.text.split("|")[0]
                if curr_chapter == 4 and num_section == 0 and book_name == "Shabbat" and lang == "en":
                    paragraphs.append(u"<strong>{}</strong> <sup>1</sup><i class=\"footnote\">Editor’s note: The term ner "
                                      u"originally referred to an oil lamp. Nowadays, it has become common to speak "
                                      u"of “Shabbat candles.” We have adopted this term because of the generic usage, "
                                      u"but unless otherwise noted these laws apply to any source of illumination that "
                                      u"is acceptable for use as nerot Shabbat.</i>".format(clean_text(curr_section_title)))
                    section_titles.append(clean_text(curr_section_title))
                else:
                    section_titles.append(curr_section_title)
                    paragraphs.append(u"<strong>{}</strong>".format(curr_section_title))

            raw_paragraphs = soup.find("div", class_="entry-content")
            footnotes = get_footnotes(raw_paragraphs, curr_chapter, num_section)

            first = True
            for raw_paragraph in raw_paragraphs.find_all(["p", "h5", "h3", "h2", "blockquote", "div", "ul"], recursive=False):
                if not first or not curr_chapter:
                    if raw_paragraph.img and raw_paragraph.name != "div":
                        img_paragraphs = parse_pictures(raw_paragraph, curr_chapter, num_section)
                        if img_paragraphs:
                            paragraphs.extend(img_paragraphs)
                    if raw_paragraph.name == "blockquote":
                        paragraphs[len(paragraphs)-1] += " \"" + clean_text(raw_paragraph.p.text) + "\" "
                    elif raw_paragraph.text == "***":
                        final_comment = True
                    elif raw_paragraph.text == u'\xa0':
                        continue
                    elif raw_paragraph.name == "ul":
                        bulletpoints = raw_paragraph.find_all("li")
                        for bulletpoint in bulletpoints:
                            paragraphs.append(aleph_bet + clean_text(u"\u25AA" + bulletpoint.text))
                            aleph_bet = ""
                    elif raw_paragraph.name == "div" and (raw_paragraph.img or (raw_paragraph.a and raw_paragraph.a.img)):
                        # if raw_paragraph["class"] == "wp-caption aligncenter":
                        a = raw_paragraph.find("a", recursive=False)
                        img = raw_paragraph.find("img", recursive=False)
                        if a:
                            if "https://ph.yhb.org.il/en/wp-content/uploads/" in a["href"]:
                                img_paragraphs = parse_pictures(a, curr_chapter, num_section, exception=True)
                                if img_paragraphs:
                                    paragraphs.extend(img_paragraphs)
                        elif img:
                            if "https://ph.yhb.org.il/en/wp-content/uploads/" in img["src"]:
                                img_paragraphs = parse_pictures(raw_paragraph, curr_chapter, num_section, exception=True)
                                if img_paragraphs:
                                    paragraphs.extend(img_paragraphs)
                    else:
                        if final_comment:
                            paragraphs.append("*** <br/><br/>" + clean_text(raw_paragraph.text))
                        elif (not raw_paragraph.img and raw_paragraph.name != "div") or raw_paragraph.name in ["h2", "h5", "h3"]:
                            if raw_paragraph.name == "h2":
                                paragraphs.append(aleph_bet + clean_text("<b>" + raw_paragraph.text + "</b>"))
                                aleph_bet = ""
                            else:
                                cleaned_text = clean_text(raw_paragraph.text)
                                if len(cleaned_text) > 0:
                                    if len(cleaned_text) == 1:
                                        aleph_bet = u"{}. ".format(cleaned_text)
                                    else:
                                        paragraphs.append(aleph_bet + cleaned_text)
                                        aleph_bet = ""
                    potential_sups = raw_paragraph.find_all("sup")
                    for sup in potential_sups:
                        if sup.a:
                            footnote_num = sup.a.text.replace("]", "").replace("[", "")
                            try:
                                footnote_text = footnotes[int(footnote_num)]
                                footnote_tag = u"<sup>{}</sup><i class=\"footnote\">{}</i>".format(footnote_num, clean_text(footnote_text))
                                paragraphs[len(paragraphs)-1] += footnote_tag
                            except TypeError:
                                continue
                first = False
            if curr_chapter:
                sections.append(paragraphs[:])
            print "section added"

        if curr_chapter:
            chapters.append(sections[:])
            titles[chapter_title] = section_titles[:]
        else:
            introduction = paragraphs[:]
        print "chapter added"

    return introduction, chapters, ordered_chapter_titles, titles


def supplement_parser():
    sections = []
    goren_introduction = []
    all_siman_titles = {}
    section_titles = [u"תשובות הרב שלמה גורן", u"הרב אברהם שפירא", u"הרב נחום אליעזר רבינוביץ\'"]
    aleph_bet = ""

    num_simanim = [12, 2, 1]
    for curr_section in range(3):
        simanim = []
        simanim_titles = []

        for num_siman in range(num_simanim[curr_section]):
            paragraphs = []
            if not curr_section and not num_siman:
                file = open("./Scraped_HTML/The Nation and the Land_he/Chapter_11_Section_1_Introduction.html")
            elif not curr_section:
                file = open("./Scraped_HTML/The Nation and the Land_he/Chapter_11_Section_{}_Siman_{}.html".format(curr_section + 1, num_siman))
            else:
                file = open("./Scraped_HTML/The Nation and the Land_he/Chapter_11_Section_{}_Siman_{}.html".format(curr_section + 1, num_siman + 1))
            source = file.read()
            soup = BeautifulSoup(source, 'lxml')

            if num_siman or curr_section:
                curr_siman_title = soup.title.text.split("|")[0]
                simanim_titles.append(curr_siman_title)
                paragraphs.append(u"<strong>{}</strong>".format(curr_siman_title))

            raw_paragraphs = soup.find("div", class_="entry-content")
            footnotes = get_footnotes(raw_paragraphs)

            first = True
            for raw_paragraph in raw_paragraphs.find_all(["p", "h5", "h3", "h2", "blockquote", "div", "ul"], recursive=False):
                if not first: # or not curr_chapter:
                    if raw_paragraph.name == "blockquote":
                        paragraphs[len(paragraphs) - 1] += " \"" + clean_text(raw_paragraph.p.text) + "\" "
                    elif raw_paragraph.text == u'\xa0':
                        continue
                    elif raw_paragraph.name == "ul":
                        bulletpoints = raw_paragraph.find_all("li")
                        for bulletpoint in bulletpoints:
                            paragraphs.append(aleph_bet + clean_text(u"\u25AA " + bulletpoint.text))
                            aleph_bet = ""
                    else:
                        if (not raw_paragraph.img and raw_paragraph.name != "div") or raw_paragraph.name in ["h2", "h5", "h3"]:
                            if raw_paragraph.name == "h2":
                                paragraphs.append(aleph_bet + clean_text("<b>" + raw_paragraph.text + "</b>"))
                                aleph_bet = ""
                            else:
                                cleaned_text = clean_text(raw_paragraph.text)
                                if len(cleaned_text) > 0:
                                    if len(cleaned_text) == 1:
                                        aleph_bet = u"{}. ".format(cleaned_text)
                                    else:
                                        paragraphs.append(aleph_bet + cleaned_text)
                                        aleph_bet = ""
                    potential_sups = raw_paragraph.find_all("sup")
                    for sup in potential_sups:
                        if sup.a:
                            footnote_num = sup.a.text.replace("]", "").replace("[", "")
                            try:
                                footnote_text = footnotes[int(footnote_num)]
                                footnote_tag = u"<sup>{}</sup><i class=\"footnote\">{}</i>".format(footnote_num,
                                                                                                   footnote_text)
                                paragraphs[len(paragraphs) - 1] += footnote_tag
                            except TypeError:
                                continue
                first = False
            if curr_section or num_siman:
                simanim.append(paragraphs[:])
            else:
                goren_introduction = paragraphs[:]
            print "section added"

        sections.append(simanim[:])
        all_siman_titles[section_titles[curr_section]] = simanim_titles[:]
        print "chapter added"

    return goren_introduction, sections, section_titles, all_siman_titles


def clean_text(paragraph):
    paragraph = re.sub(footnote_re, "", paragraph)
    paragraph = re.sub(img_text_re, "", paragraph).strip()
    paragraph = paragraph.replace(u"\u0124", u"\u1E24").replace(u"\u0125", u"\u1E25")
    # if len(paragraph) < 3:
        # print u"{} <<<<<<".format(paragraph)
    # print paragraph[:20]
    return paragraph


def parse_pictures(raw_paragraph, curr_chapter, curr_section, footnote=None, exception=False):
    paragraphs = []
    pic = 1
    for child in raw_paragraph.children:
        if isinstance(child, element.Tag):
            if child.name == "img" and (child["src"][-3:] == "png" or exception or "https://ph.yhb.org.il/en/wp-content/uploads/" in child["src"]):
                img_64_code = get_64_code(child, curr_chapter, curr_section, pic, footnote)
                if img_64_code:
                    pic += 1
                    paragraphs.append(img_64_code)
            elif child.name == "span":
                paragraphs[len(paragraphs)-1] += clean_text(child.text)
            elif child.name == "a" and ("https://ph.yhb.org.il/en/wp-content/uploads/" in child["href"] or "https://ph.yhb.org.il/wp-content/uploads/" in child["href"]):
                img_64_code = get_64_code(child.img, curr_chapter, curr_section, pic, footnote)
                if img_64_code:
                    pic += 1
                    paragraphs.append(img_64_code)
            elif child.name == "p" and child.parent.find("p", class_="wp-caption-text"):
                try:
                    paragraphs[len(paragraphs)-1] += "<br/>" + child.text
                except IndexError:
                    paragraphs.append(child.text)
            else:
                assert True #child.name == "br" or child.img["src"][-3:] != "png"
        elif isinstance(child, element.NavigableString):
            if len(child) > 2 and "max-width" not in child:
                paragraphs.append(clean_text(child))
        else:
            raise Exception("Something seems wrong. This exception means there is another type of child that was unaccounted for.")
    if not paragraphs:
        if raw_paragraph.name == "img" and raw_paragraph["src"][-3:] == "png":
            img_64_code = get_64_code(raw_paragraph, curr_chapter, curr_section, pic, footnote)
            if img_64_code:
                pic += 1
                paragraphs.append(img_64_code)
    return paragraphs


def get_64_code(img_tag, curr_chapter, curr_section, pic_num, footnote):
    global pics
    if footnote:
        filename = "Chapter_{}_Section_{}_Picture_{}_footnote_{}_{}".format(curr_chapter, curr_section + 1, pic_num, footnote, pics)
    else:
        filename = "Chapter_{}_Section_{}_Picture_{}_{}".format(curr_chapter, curr_section + 1, pic_num, pics)
    pics += 1

    try:
        file = open("./Images/"+filename+".png")
    except IOError:
        img_url = img_tag["src"]
        img = requests.get(img_url, cookies=jar)
        if img.status_code == 404:
            return 0
        f = open("./Images/"+filename+".png", "w+")
        f.write(img.content)
        f.close()
        img = Image.open("./Images/" + filename + ".png")

        orig_height = img.size[1]
        orig_width = img.size[0]
        if orig_width > 550:
            percent = 550 / float(orig_width)
            height = int(float(orig_height) * float(percent))
            img = img.resize((550, height), PIL.Image.ANTIALIAS)
            img = img.save("./Images/"+filename+".png")
        file = open("./Images/"+filename+".png")

    data = file.read()
    file.close()
    data = data.encode("base64")
    new_tag = '<img src="data:image/png;base64,{}">'.format(data)
    return new_tag


def get_footnotes(raw_paragraphs, curr_chapter=None, curr_section=None):
    # footnotes = raw_paragraphs.findAll("div", class_=None, recursive=False)
    footnotes_list = raw_paragraphs.findAll("div", class_=None) + raw_paragraphs.findAll("div", class_="footnotes")
    if not footnotes_list:
        return
    footnotes_list = [footnote for footnote in footnotes_list if not footnote.hr or not footnote.find("div", class_=None) or footnote.ol]
    footnotes_dict = {}
    allowed_footnote_tags = ["span", "strong", "br", "em", "i", "b", "ol", "sup"] #took out img
    for footnote in footnotes_list:
    # try:
    #     footnotes = footnotes[0].div.children
    # except AttributeError:
        footnotes = footnote.children
        number = 0
        text = ""
        for footnote_line in footnotes:
            if isinstance(footnote_line, element.Tag):
                if footnote_line.name == "a":
                    if number:
                        footnotes_dict[number] = text
                        text = ""
                    number = int(footnote_line.text.replace("[", "").replace("]", ""))
                elif footnote_line.name == "ol":
                    alt_footnotes = footnote_line.findAll("li")
                    for alt in alt_footnotes:
                        if number:
                            footnotes_dict[number] = text
                            text = ""
                        number = int(alt["id"].split("-")[2])
                        for child in alt.children:
                            if isinstance(child, element.Tag):
                                assert child.name == "p"
                                text += child.text
                            elif isinstance(child, element.NavigableString):
                                text += child
                            else:
                                assert False
                elif footnote_line.name == "p":
                    if footnote_line.a:
                        for sub_footnote_line in footnote_line.children:
                            if isinstance(sub_footnote_line, element.Tag):
                                if sub_footnote_line.name == "a":
                                    if number:
                                        footnotes_dict[number] = text
                                        text = ""
                                    number = int(sub_footnote_line.text.replace("[", "").replace("]", ""))
                                else:
                                    assert sub_footnote_line.name in allowed_footnote_tags
                                    if sub_footnote_line.name in allowed_footnote_tags:
                                        text += get_tag(sub_footnote_line)
                            else:
                                assert isinstance(sub_footnote_line, element.NavigableString)
                                text += sub_footnote_line
                    else:
                        if len(footnote_line.text) > 2:
                            text += "<br/>"
                            for text_child in footnote_line.children:
                                if isinstance(text_child, element.NavigableString):
                                    text += text_child
                                elif isinstance(text_child, element.Tag):
                                    assert text_child.name in allowed_footnote_tags

                                    text += text_child.text
                            # text += footnote_line.text
                elif footnote_line.name in allowed_footnote_tags:
                    text += get_tag(footnote_line)
                elif footnote_line.name == "img":
                    img_paragraphs = parse_pictures(footnote_line, curr_chapter, curr_section, footnote=number)
                    if img_paragraphs:
                        for paragraph in img_paragraphs:
                            text += "<br/>" + paragraph
                elif footnote_line.name == "div" and footnote_line.img:
                    img_paragraphs = parse_pictures(footnote_line, curr_chapter, curr_section, footnote=number)
                    if img_paragraphs:
                        for paragraph in img_paragraphs:
                            text += "<br/>" + paragraph
                elif (footnote_line.name == "div" and footnote_line.text.strip() == "") or footnote_line.name == "hr":
                    None
                else:
                    assert False
            elif isinstance(footnote_line, element.NavigableString):
                if len(footnote_line) > 2:
                    text += footnote_line
            else:
                raise Exception("There's a footnote child that's not a NavigableString or a p-tag")
        footnotes_dict[number] = text[1:]

    return footnotes_dict

def get_tag(tag):
    if tag.name in ["strong", "b"]:
        return u"<strong>{}</strong>".format(tag.text)
    elif tag.name in ["em", "i"]:
        return u"<em>{}</em>".format(tag.text)
    elif tag.name == "br":
        return "<br/>"
    elif tag.name == "sup":
        return u"<sup>{}</sup>".format(tag.text)
    elif tag.name == "ol":
        return tag.li.text
    else:
        return tag.text

def post_index_to_server(en, he, ordered_chapter_titles, section_titles, both=False, supp_section_titles=None, sup_all_siman_titles=None):

    def clean_title(title):
        new_title = title.replace(u"\u2013", u":").replace(u"\u2019", u"\'").replace(u"-", u":").replace(u"\u0125", u"h").replace(u"\u201c", "\"").replace(u"\u201d", "\"").replace(u"\u0124", u"H")
        # if new_title != title:
            # print "Old --> " + title
            # print "New --> " + new_title
        return new_title

    root = SchemaNode()
    comm_en = "Peninei Halakhah, {}".format(en)
    comm_he = u"פניני הלכה, {}".format(he)
    root.add_primary_titles(comm_en, comm_he)
    root.key = "Peninei Halakhah, {}".format(en)

    intro_node = JaggedArrayNode()
    intro_node.add_shared_term("Introduction")
    intro_node.key = u"Introduction"
    intro_node.add_structure(["Paragraph"])
    intro_node.toc_zoom = 2
    intro_node.depth = 1
    root.append(intro_node)

    chapters_node = JaggedArrayNode()
    chapters_node.key = "default"
    chapters_node.default = True
    chapters_node.add_structure([u"Chapter", u"Section", u"Paragraph"])
    # chapters_node.toc_zoom = 1
    chapters_node.depth = 3
    root.append(chapters_node)

    if en == "The Nation and the Land":
        supplement_node = SchemaNode()
        supplement_node.add_primary_titles("Supplement", u"נספח")
        # supplement_node.toc_zoom = 2
        # supplement_node.depth = 3

        # supplement_sections_he = ordered_chapter_titles[0][len(ordered_chapter_titles[0])-1]
        # supplement_sections_en = ordered_chapter_titles[1][len(ordered_chapter_titles[1])-1]
        supplement_sections_en = ["Responsa of Rabbi Shlomo Goren", "Responsa of Rabbi Araham Shapiro", "Responsa of Rabbi Nahum Rabinovitch"]

        for num, supplement_section_he in enumerate(supp_section_titles):
            if not num:
                supp_section_node = SchemaNode()
                supp_section_node.add_primary_titles(supplement_sections_en[num], supplement_section_he)
                # supp_section_node.toc_zoom = 2
                # supp_section_node.depth = 3
                supp_section_node_sub = JaggedArrayNode()
                supp_section_node_sub.add_shared_term("Introduction")
                supp_section_node_sub.key = u"Introduction"
                supp_section_node_sub.add_structure(["Paragraph"])
                supp_section_node_sub.toc_zoom = 2
                supp_section_node_sub.depth = 1
                supp_section_node_sub.validate()
                supp_section_node.append(supp_section_node_sub)

                supp_section_node_sub = JaggedArrayNode()
                supp_section_node_sub.key = "default"
                supp_section_node_sub.default = True
                supp_section_node_sub.add_structure(["Siman", "Paragraph"])
                supp_section_node_sub.toc_zoom = 3
                supp_section_node_sub.depth = 2
                supp_section_node_sub.validate()
                supp_section_node.append(supp_section_node_sub)

                supp_section_node.validate()
                supplement_node.append(supp_section_node)
            else:
                supp_section_node = JaggedArrayNode()
                supp_section_node.add_primary_titles(supplement_sections_en[num], supplement_section_he)
                supp_section_node.add_structure(["Siman", "Paragraph"])
                supp_section_node.toc_zoom = 3
                supp_section_node.depth = 2
                supp_section_node.validate()
                supplement_node.append(supp_section_node)

        root.append(supplement_node)

    root.validate()

    altstruct_nodes = []
    array_map = ArrayMapNode()
    array_map.wholeRef = "Peninei Halakhah, {}, Introduction".format(en)
    array_map.depth = 0
    array_map.includeSections = False
    array_map.refs = []
    array_map.add_shared_term("Introduction")
    array_map.key = u"Introduction"
    array_map.validate()
    altstruct_nodes.append(array_map.serialize())

    if both:
        chapter_list = ordered_chapter_titles[0]
    else:
        chapter_list = ordered_chapter_titles

    for chap_num, he_chapter_title in enumerate(chapter_list):
        schema = SchemaNode()
        en_chapter_title = (ordered_chapter_titles[1][chap_num]) if both else "{}".format(chap_num+1)
        schema.add_primary_titles(clean_title(en_chapter_title), he_chapter_title)

        if both:
            section_list = section_titles[0][he_chapter_title]
        else:
            section_list = section_titles[he_chapter_title]
        bias = 0
        for sec_num, he_section_title in enumerate(section_list):
            if (en == "Prayer" and chap_num == 7 and sec_num == 1) or \
                    (en == "Women's Prayer" and chap_num == 11 and sec_num == 10) or \
                    (en == "Women's Prayer" and chap_num == 21 and sec_num == 4) or \
                    (en == "Women's Prayer" and chap_num == 21 and sec_num == 5):
                array_map = ArrayMapNode()
                if sec_num == 1:
                    array_map.add_primary_titles("02 : Hand Washing Concerning One Who Did Not Sleep All Night", u"???")
                elif sec_num == 4:
                    array_map.add_primary_titles("05. Women and Tzitzit", u"???")
                elif sec_num == 5:
                    array_map.add_primary_titles("06. Women and Tefilin", u"???")
                elif sec_num == 10:
                    array_map.add_primary_titles("11. The Prohibition of Reciting Sacred Words in the Presence of \"Erva\"", u"???")
                array_map.depth = 0
                array_map.includeSections = False
                array_map.wholeRef = "Peninei Halakhah, {} {}:{}".format(en, chap_num + 1, sec_num + 1)
                array_map.refs = []
                array_map.validate()
                schema.append(array_map)
                bias += 1
            array_map = ArrayMapNode()
            en_section_title = (section_titles[1][en_chapter_title][sec_num+bias]) if both else "{}".format(sec_num+1)
            array_map.add_primary_titles(clean_title(en_section_title), he_section_title)
            array_map.depth = 0
            array_map.includeSections = False
            array_map.wholeRef = "Peninei Halakhah, {} {}:{}".format(en, chap_num+1, sec_num+1+bias)
            array_map.refs = []
            array_map.validate()
            schema.append(array_map)
        schema.validate()
        altstruct_nodes.append(schema.serialize())

    if en == "The Nation and the Land":
        supplement_node_alt = SchemaNode()
        supplement_node_alt.add_primary_titles("Supplement", u"נספח")

        for sec_num, he_section_title in enumerate(supp_section_titles):

            sub_alt = SchemaNode()
            sub_alt.add_primary_titles(clean_title(supplement_sections_en[sec_num]), he_section_title)
            if not sec_num:
                array_map = ArrayMapNode()
                array_map.add_shared_term("Introduction")
                array_map.key = u"Introduction"
                array_map.depth = 0
                array_map.includeSections = False
                array_map.wholeRef = "Peninei Halakhah, {}, Supplement, Responsa of Rabbi Shlomo Goren, Introduction".format(en)
                array_map.refs = []
                array_map.validate()
                sub_alt.append(array_map)

                siman_titles = sup_all_siman_titles[he_section_title]
                for sim_num, he_siman_title in enumerate(siman_titles):
                    array_map = ArrayMapNode()
                    array_map.add_primary_titles(clean_title("Siman {}".format(sim_num + 1)), he_siman_title) # FIX THIS
                    array_map.depth = 0
                    array_map.includeSections = False
                    array_map.wholeRef = "Peninei Halakhah, {}, Supplement, {} {}".format(en, supplement_sections_en[sec_num], sim_num + 1)
                    array_map.refs = []
                    array_map.validate()
                    sub_alt.append(array_map)
            else:
                siman_titles = sup_all_siman_titles[he_section_title]
                for sim_num, he_siman_title in enumerate(siman_titles):
                    array_map = ArrayMapNode()
                    array_map.add_primary_titles(clean_title("Siman {}".format(sim_num + 1)), he_siman_title) # FIX THIS
                    array_map.depth = 0
                    array_map.includeSections = False
                    array_map.wholeRef = "Peninei Halakhah, {}, Supplement, {} {}".format(en, supplement_sections_en[sec_num], sim_num + 1)
                    array_map.refs = []
                    array_map.validate()
                    sub_alt.append(array_map)

            sub_alt.validate()
            supplement_node_alt.append(sub_alt)
        altstruct_nodes.append(supplement_node_alt.serialize())


    index = {
        "title": comm_en,
        "collective_title": "Peninei Halakhah",
        "schema": root.serialize(),
        "categories": ["Halakhah", "Peninei Halakhah"],
        "alt_structs": {"Topic": {"nodes": altstruct_nodes}}
    }
    response = post_index(index, server=SEFARIA_SERVER)


def post_text_to_server(book_name_en, introduction, chapters, lang, goren_intro=None, supp_sections=None):
    supplement_sections_en = ["Responsa of Rabbi Shlomo Goren", "Responsa of Rabbi Avraham Shapiro",
                              "Responsa of Rabbi Nahum Rabinovitch"]
    if lang == "he":
        vt = VERSION_TITLE_HE
        vs = VERSION_SOURCE_HE
    else:
        vt = VERSION_TITLE_EN
        vs = VERSION_SOURCE_EN

    send_text_chapters = {
        "text": chapters,
        "versionTitle": vt,
        "versionSource": vs,
        "language": lang
    }

    post_text("Peninei Halakhah, {}".format(book_name_en), send_text_chapters, server=SEFARIA_SERVER)

    if lang == "he":
        send_text_intro = {
            "text": introduction,
            "versionTitle": vt,
            "versionSource": vs,
            "language": lang
        }

        post_text("Peninei Halakhah, {}, Introduction".format(book_name_en), send_text_intro, server=SEFARIA_SERVER)

    if book_name_en == "The Nation and the Land":
        for num, rav in enumerate(supplement_sections_en):
            send_text_supp = {
                "text": supp_sections[num],
                "versionTitle": vt,
                "versionSource": vs,
                "language": lang
            }

            post_text("Peninei Halakhah, {}, Supplement, {}".format(book_name_en, rav), send_text_supp, server=SEFARIA_SERVER)

        send_text_goren_intro = {
            "text": goren_intro,
            "versionTitle": vt,
            "versionSource": vs,
            "language": lang
        }

        post_text("Peninei Halakhah, {}, Supplement, Responsa of Rabbi Shlomo Goren, Introduction".format(book_name_en), send_text_goren_intro, server=SEFARIA_SERVER)

if __name__ == "__main__":
    # add_term("Peninei Halakhah", u"פניני הלכה")
    # add_category("Peninei Halakhah",["Halakhah", "Peninei Halakhah"], u"פניני הלכה")
    for curr_book in book_list:
        do_peninei_halakhah(books[curr_book][0], books[curr_book][1], books[curr_book][2], lang=lang)






# chapters = get_soup("Shabbat")
# chapter_n = 1
# section_n = 1
# for chapter in chapters:
#     print "------------------chapter {}--------------------".format(chapter_n)
#     chapter_n += 1
#     section_n = 1
#     for section in chapter:
#         print "------------------section {}--------------------".format(section_n)
#         section_n += 1
#         for paragraph in section:
#             print paragraph
#             print "------------------------------"

# book_name = "Shabbat"
# chapter = 01#15#22
# section = 01#12#8
# file = open("./Scraped_HTML/{}/Introduction.html".format(book_name))
# source = file.read()
# # curr_chapter = "01"
# # curr_section = "01"
# # url = "https://ph.yhb.org.il/01-{}-{}/".format(curr_chapter, curr_section)
# # source = requests.get(url).text
# soup = BeautifulSoup(source, 'lxml')
# print soup.prettify()
# sidebar = soup.find("ul", class_="collapsing categories list", id="widget-collapscat-4-top").find("li", class_ = "collapsing categories expandable parent")
# chapters = sidebar.div.ul
# for chapter in chapters.children:
#     last_chapter_num = chapter.
# last_chapter
