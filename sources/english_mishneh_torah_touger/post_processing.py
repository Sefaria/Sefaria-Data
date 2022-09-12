# coding=utf8
import django

django.setup()

import csv
import re
import requests
from bs4 import BeautifulSoup
import PIL
from PIL import Image
from io import BytesIO
from base64 import b64decode, b64encode
import statistics
import bleach

from sefaria.model import *
from utilities import create_book_name_map, sefaria_book_names, export_data_to_csv, ALLOWED_TAGS, ALLOWED_ATTRS


def convert_base_64_img(halakha):
    ref_name = halakha['ref'].lower()
    ref_name = re.sub(" ", "", ref_name)
    ref_name = re.sub("\.", "_", ref_name)
    filename = f"{ref_name}_img.jpg"
    text = halakha['text']
    tags = re.findall("<img.*?>", text)
    for tag in tags:
        url = re.findall(r"src=\"(.*?)\"", tag)[0]
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        orig_height = img.size[1]
        orig_width = img.size[0]
        if orig_width > 550:
            percent = 550 / float(orig_width)
            height = int(float(orig_height) * float(percent))
            img = img.resize((550, height), PIL.Image.ANTIALIAS)
        img = img.save(f"images/{filename}")
        file = open("./images/{}".format(filename), 'rb')
        data = file.read()
        file.close()
        data = b64encode(data)
        new_tag = '<img src="data:image/{};base64,{}"></img>'.format('jpg', str(data)[2:-1])
        text = text.replace(tag, new_tag)
    return text


def setup_data():
    """
    This function reads the CSV from the scraping, and sets up a list of Chabad specific Rambam names,
    as well as a list of dictionaries of the scraping data for easy manipulation later
    """
    chabad_book_names = []
    mishneh_torah_list = []
    with open('mishneh_torah_data_scraped_ftns.csv', newline='') as csvfile:
        r = csv.reader(csvfile, delimiter=',')
        for row in r:
            book_ref = row[0]

            # Texts which are exceptions to the scrape
            if book_ref == "Tefillin, Mezuzah and Sefer Torah 8.4":
                txt = "<p>Since I have seen great confusion about these matters in all the scrolls I have seen, and similarly, the masters of the tradition who have written down and composed [texts] to make it known [which passages] are <i>p'tuchot</i> and which are <i>s'tumot</i> are divided with regard to the scrolls on which to rely, I saw fit to write down the entire list of all the passages in the Torah that are <i>s'tumot</i> and <i>p'tuchot</i>, and also the form of the songs. In this manner, all the scrolls can be corrected and checked against these [principles].<sup class=\"footnote-marker\">9</sup><i class=\"footnote\">In his introduction to the <i>Mishneh Torah</i>, the Rambam outlines the goals he had in composing the text:<br>to compose a work that clarifies... the entire Oral Law, setting it in order without question or difficulty... revealing all the laws to the great and the small regarding each and every mitzvah.<br>The goal of presenting the Oral Law in a form that could be put in practice by every Jew is clearly expressed in these halachot that give precise instructions enabling each individual to compose a kosher Torah scroll.</i><br>The scroll on which I relied on for [clarification of] these matters was a scroll renowned in Egypt, which includes all the 24 books [of the Bible]. It was kept in Jerusalem for many years so that scrolls could be checked from it. Everyone relies upon it because it was corrected by ben Asher,<sup class=\"footnote-marker\">10</sup><i class=\"footnote\">This appears to refer to the scribe Aharon ben Moshe, from the tribe of Asher, who lived in Tiberias in the generation following Rav Sa'adiah Gaon and was renowned for his knowledge of grammar (<i>Shalshelet HaKabbalah</i>).</i>who spent many years writing it precisely, and [afterward] checked it many times.</p><p>I relied [on this scroll] when I wrote a Torah scroll according to law.</p> <p class=\"child_title\">The Book of <span class=\"glossary_item\" glossary_item=\"34157\">Genesis</span></p><p>יהי רקיע יקוו המים יהי מאורות ישרצו המים תוצא הארץ ויכלו אלה תולדות השמים כולן פתוחות והן שבע פרשיות אל האשה אמר ולאדם אמר שתיהן סתומות ויאמר יי' אלהים פתוחה והאדם ידע זה ספר ויחי שת ויחי אנוש ויחי קינן ויחי מהללאל ויחי ירד ויחי חנוך ויחי מתושלח ויחי למך ויחי נח אחת עשרה פרשיות אלו כולן סתומות וירא יי' אלה תולדת נח שתיהן פתוחות ויאמר אלהים לנח וידבר אלהים אל נח ויאמר אלהים אל נח שלשתן סתומות ויהיו בני נח ואלה תולדת בני נח שתיהן פתוחות וכנען ילד ולשם ילד שתיהן סתומות ויהי כל הארץ שפה אחת אלה תולדת שם שתיהן פתוחות וארפכשד חי ושלח חי ויחי עבר ויחי פלג ויחי רעו ויחי שרוג ויחי נחור ויחי תרח כולן סתומות השמונה פרשיות ויאמר יי' אל אברם ויהי רעב ויהי בימי אמרפל שלשתן פתוחות אחר הדברים ושרי אשת אברם ויהי אברם ויאמר אלהים אל אברהם ארבעתן סתומות וירא אליו פתוחה ויסע משם ויי' פקד את שרה שתיהן סתומות ויהי בעת ההוא ויהי אחר ויהי אחרי הדברים ויהיו חיי שרה ארבעתן פתוחות ואברהם זקן סתומה ויסף אברהם ואלה תלדת ישמעאל ואלה תולדת יצחק ויהי רעב ארבעתן פתוחות ויהי עשו ויהי כי זקן יצחק ויצא יעקב שלשתן סתומות וישלח יעקב פתוחה ויבא יעקב ותצא דינה שתיהן סתומות ויאמר אלהים וירא אלהים ויהיו בני יעקב ואלה תלדות עשו ארבעתן פתוחות אלה בני שעיר סתומה ואלה המלכים וישב יעקב ויהי בעת שלשתן פתוחות ויוסף הורד מצרימה סתומה ויהי אחר הדברים ויהי מקץ שתיהן פתוחות: ויגש אליו ואלה שמות ואת יהודה שלשתן סתומות ויהי אחרי הדברים ויקרא יעקב שמעון ולוי יהודה זבולן יששכר כולן פתוחות והן שש דן גד מאשר נפתלי בן פרת יוסף חמשתן סתומות בנימין פתוחה </p><p>There are 43 passages that are <i>p'tuchot</i> and 48 passages that are <i>s'tumot</i>, 91 passages in their entirety.<sup class=\"footnote-marker\">11</sup><i class=\"footnote\">The first passage in each book of the Torah is not mentioned, since it is governed by different rules (<i>Kessef Mishneh</i>). There is some debate among the commentaries concerning the exact text of the <i>Mishneh Torah</i>. Also, there are different traditions regarding several of these passages. Accordingly, today, a scribe should write a scroll based on a Torah scroll that is accepted as correct, and not from this list.</i>"
            elif book_ref == "Yesodei haTorah 1.1":
                txt = "<p>The foundation of all foundations and the pillar of wisdom is to know that there is a Primary Being who brought into being all existence. All the beings of the heavens, the earth, and what is between them came into existence only from the truth of His being.</p>"
            else:
                txt = row[1]
            mishneh_torah_list.append({'ref': book_ref, 'text': txt})
            book = re.findall(r"(.*) \d*.\d*", book_ref)[0]
            if book not in chabad_book_names:
                chabad_book_names.append(book)
    return chabad_book_names, mishneh_torah_list


def rename_refs_to_sefaria(mishneh_torah_list, name_map):
    """
    This function massages the Chabad Refs into Sefaria refs for the data list/dictionary
    """
    new_mt_list = []
    for halakha in mishneh_torah_list:
        ref = halakha['ref']
        book = re.findall(r"(.*) \d*.\d*", ref)[0]
        sef_book = name_map[book]
        sefaria_ref = re.sub(r"[^0-9.]+", f"{sef_book} ", ref)
        new_mt_list.append({'ref': sefaria_ref, 'text': halakha['text']})

    return new_mt_list


def flag_no_punc(mt_list):
    count = 0
    new_list = []
    for halakha in mt_list:
        if text[-1] not in [".", "?", "!", ";", "\'", "\"", ">", "”"]:
            count += 1
            new_list.append({'ref': halakha['ref'],
                             'text': text,
                             'flag': True})
        else:
            new_list.append({'ref': halakha['ref'],
                             'text': text,
                             'flag': False})
    print(f"{count} flagged of {len(new_list)}")
    return new_list


def export_cleaned_data_to_csv(mt_list):
    """
    This function writes the cleaned data to a new CSV
    """
    with open('mishneh_torah_data_cleaned.csv', 'w+') as csvfile:
        headers = ['ref', 'text']
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writerows(mt_list)


def strip_p_for_br(mt_list):
    new_list = []
    for halakha in mt_list:
        txt = halakha['text']
        txt = txt.strip()
        br_txt = re.sub(r"</p>\n<p>", "<br>", txt)
        clean_txt = re.sub(r"<p>|</p>", "", br_txt)  # remove remaining <p>
        new_list.append({'ref': halakha['ref'], 'text': clean_txt})
    return new_list


def img_convert(mt_list):
    new_mt_list = []
    for halakha in mt_list:
        cur_dict = {}
        if 'img' in halakha['text']:
            img_txt = convert_base_64_img(halakha)
            cur_dict['ref'] = halakha['ref']
            cur_dict['text'] = img_txt
        else:
            cur_dict['ref'] = halakha['ref']
            cur_dict['text'] = halakha['text']
        new_mt_list.append(cur_dict)
    return new_mt_list


# Hebrew length validation
def generate_stats(mt_list):
    ratio_list = []
    ratio_aggregate = 0

    for halakha in mt_list:
        en_text = halakha['text']
        hebrew_text = Ref(f"Mishneh Torah, {halakha['ref']}").text('he').text

        ratio_he_to_en = len(hebrew_text) / len(en_text)
        ratio_aggregate += ratio_he_to_en
        ratio_list.append(ratio_he_to_en)

    mean_of_ratios = ratio_aggregate / (len(mt_list))
    stdev = statistics.stdev(ratio_list)
    return mean_of_ratios, stdev


def stats_flag(mt_list):
    new_list = []
    mean, stdev = generate_stats(mt_list)
    for halakha in mt_list:
        en_text = halakha['text']
        hebrew_text = Ref(f"Mishneh Torah, {halakha['ref']}").text('he').text

        cur_ratio = len(hebrew_text) / len(en_text)
        two_sd_above = mean + (2 * stdev)
        two_sd_below = mean - (2 * stdev)

        if cur_ratio > two_sd_above or cur_ratio < two_sd_below:
            flag = True
            msg = "Not within 2 stdev"
        else:
            flag = False
            msg = ""

        new_list.append({'ref': halakha['ref'], 'text': halakha['text'], 'flag': flag, 'msg': msg})
    return new_list


def generate_html_report(txt, unique_html_tags, unique_html_tag_dict_list):
    tags = re.findall(r"<(.*?)>", txt)
    for each_tag in tags:
        tag_name = re.findall(r"^(.*?)\s", each_tag)
        if tag_name:
            if tag_name[0] not in unique_html_tags:
                unique_html_tags[tag_name[0]] = 1

                # Save each first occurrence for report
                unique_html_tag_dict_list.append({
                    'tag': tag_name[0],
                    'example_ref': halakha['ref'],
                    'example_text': txt
                })

            else:
                unique_html_tags[tag_name[0]] += 1


def html_clean_up(mt_list, generate_html_report=False, generate_br_report=False):
    unique_html_tags = {}
    unique_html_tag_dict_list = []
    br_report_list = []
    new_list = []
    count=0
    for halakha in mt_list:
        txt = halakha['text']

        # Remove number of quotes from footnote
        if "footnote" in txt:
            txt = re.sub("\"\"", "\"", txt)

        txt = re.sub(r"\r\n", "<br>", txt)
        txt = re.sub(r"\n", "<br>", txt)
        txt = txt.strip()

        # Massage links to text references into Sefaria form
        links = re.findall(r"<a href=.*?>(.*?)<\/a>", txt)
        for link in links:

            # Add escape characters to links data for matching
            if ")" in link or "(" in link:
                re_link = re.sub(r"\)", "\\)", link)
                re_link = re.sub(r"\(", "\\(", re_link)
            else:
                re_link = link
            clean_link = re.sub(r"[^A-Za-z :0-9]", " ", link)
            patt = f"<a href=.*?>{re_link}<\/a>"
            txt = re.sub(patt, clean_link, txt)

        # Add the appropriate superscript class
        sups = re.findall(r"<sup>(.*?)</sup><i class=\"footnote\">", txt)
        for sup in sups:
            patt = f"<sup>{sup}</sup><i class=\"footnote\">"
            replacement = f"<sup class=\"footnote-marker\">{sup}</sup><i class=\"footnote\">"
            txt = re.sub(patt, replacement, txt)

        if generate_html_report:
            generate_html_report(txt, unique_html_tags, unique_html_tag_dict_list)

        txt = bleach.clean(txt,
                           tags=ALLOWED_TAGS,
                           attributes=ALLOWED_ATTRS,
                           strip=True)

        if generate_br_report:
            is_odd_br = re.search(r"[^?.:!]<br>", txt)
            if is_odd_br:
                count+=1
                br_report_list.append({'ref': halakha['ref'], 'text': txt})

        new_list.append({'ref': halakha['ref'], 'text': txt})

    if generate_html_report:
        export_data_to_csv(unique_html_tag_dict_list, 'qa_reports/html_report',
                           headers_list=['tag', 'example_ref', 'example_text'])
        print(unique_html_tags)
    if generate_br_report:
        export_data_to_csv(br_report_list, 'qa_reports/br_tag_report', headers_list=['ref', 'text'])
    return new_list


if __name__ == '__main__':
    chabad_book_names, mishneh_torah_list = setup_data()
    name_map = create_book_name_map(chabad_book_names, sefaria_book_names)
    mishneh_torah_list = rename_refs_to_sefaria(mishneh_torah_list, name_map)
    mishneh_torah_list = strip_p_for_br(mishneh_torah_list)
    mishneh_torah_list = img_convert(mishneh_torah_list)
    mishneh_torah_list = html_clean_up(mishneh_torah_list)
    export_cleaned_data_to_csv(mishneh_torah_list)
