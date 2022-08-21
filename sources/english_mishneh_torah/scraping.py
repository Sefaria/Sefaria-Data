from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from datetime import date, timedelta
from bs4 import BeautifulSoup
import re
import csv

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


# TODO - rewrite code in OOP way
# Object variables - halakhot, footnote dict, soup etc

def selenium_firefox_get(url):
    profile = webdriver.FirefoxProfile()
    profile.set_preference("javascript.enabled", False);

    options = Options()
    options.headless = True

    driver = webdriver.Firefox(profile, options=options)
    driver.get(url)
    src = driver.page_source
    driver.quit()
    return src


def extract_book_chapter(soup, date_string):
    capture = soup.find_all(class_="rambam_h2")[0]
    capture = str(capture)
    regex_tuple = re.findall(r">(.*) - (.*)<", capture)[0]
    book = regex_tuple[0]
    en_chapter = regex_tuple[1]

    # Special cases
    if en_chapter == 'Text of the Haggadah':
        num_chapter = 1

    elif book == "Order of Prayers":
        if date_string == "10/22/2020":
            num_chapter = 1
        elif date_string == "10/23/2020":
            num_chapter = 2
        elif date_string == "10/24/2020":
            num_chapter = 3
        elif date_string == "10/25/2020":
            num_chapter = 4
    else:
        num_chapter = number_map[en_chapter]

    print(f"Scraping {book},  {en_chapter} - date: {date_string}")
    return book, num_chapter


def scrape_text(soup, book, num_chapter, halakhot, footnote_dict):
    text_array = soup.find_all(class_='co_verse')

    if book == "Order of Prayers":  # Since the format isn't exactly with halacha numbers, slightly different regexes
        num_patt = r"<span class=\"co_verse\" hideversenumber=\"true\" index=\"(\d*?)\">"
        txt_patt = r"<span class=\"co_verse\" hideversenumber=\"true\" index=\"\d*\">(.*?)</span>"
    else:
        num_patt = r"<span class=\"co_verse\" index=\"(\d*?)\">"
        txt_patt = r"<span class=\"co_verse\" index=\"\d*\">.*?</a>(.*)</span>"

    for halakha in text_array:
        halakha_str = str(halakha)
        num = re.findall(num_patt, halakha_str)
        num = num[0] if len(num) > 0 else None  # None in case of end / sikum etc
        txt = re.findall(txt_patt, halakha_str, re.DOTALL)
        txt = txt[0] if len(txt) > 0 else None

        if num and txt:
            txt = insert_footnotes(txt, footnote_dict)
            # halakhot.append({"ref": f"{book} {num_chapter}.{num}", "text": txt})
            add_to_csv([{"ref": f"{book} {num_chapter}.{num}", "text": txt}])


def get_chapter(src, halakhot, date_string):
    soup = BeautifulSoup(src, 'html.parser')
    book, num_chapter = extract_book_chapter(soup, date_string)
    footnote_dict = get_footnotes(soup)
    scrape_text(soup, book, num_chapter, halakhot, footnote_dict)


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


def add_to_csv(row):
    with open('mishneh_torah_data_scraped_ftns.csv', 'a') as csvfile:
        headers = ['ref', 'text']
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writerows(row)


def scrape():
    halakhot = []
    start_date = date(2020, 7, 22)
    end_date = date(2023, 4, 23)

    for single_date in daterange(start_date, end_date):
        date_string = single_date.strftime("%m/%d/%Y")

        # Missing data
        if date_string != '08/10/2022':
            src = selenium_firefox_get(
                f"https://www.chabad.org/dailystudy/rambam.asp?tdate={date_string}&rambamChapters=1")
            get_chapter(src, halakhot, date_string)

    # with open('mishneh_torah_data_scraped_ftns.csv', 'a') as csvfile:
    #     headers = ['ref', 'text']
    #     writer = csv.DictWriter(csvfile, fieldnames=headers)
    #     writer.writerows(halakhot)

    print("Data Scraping complete")
    return halakhot


# Gets footnotes for a given chapter
# returns a dict with the key being the ID, and the value being a tuple of the footnote number and text
# i.e. {'idNumber12345: (1, 'this is footnote one')'}
def get_footnotes(soup):
    footnote_dict = {}
    capture = soup.find_all(class_="footnote")

    for ftn in capture:
        ftn = str(ftn)
        id = re.findall(r"id=\"footnoteTR(.*?)\"", ftn)[0]
        num = re.findall(r"\">(\d*?)\.</a>", ftn)[0]
        ftn_text = re.findall(r"<div class=\"footnoteBody\">(.*?)</div>", ftn, re.DOTALL)[0]
        ftn_text = ftn_text.strip()  # Leading and trailing \n, clear out
        footnote_dict[id] = (num, ftn_text)
    return footnote_dict


# For the given halakha, insert the footnotes appropriately
def insert_footnotes(txt, footnote_dict):
    ftn_ids = re.findall(
        r"<a class=\"footnote_ref\" href=\"javascript:doFootnote\('.*?'\);\" name=\"footnoteRef(.*?)\">\d*?</a>", txt)

    for id in ftn_ids:
        ftn_num, ftn_text = footnote_dict[id]
        ftn_string = f"<sup>{ftn_num}</sup><i class=\"\"footnote\"\">{ftn_text}</i>"
        patt = f"<a class=\"footnote_ref\" href=\"javascript:doFootnote\('.*?'\);\" name=\"footnoteRef{id}\">\d*?</a>"
        txt = re.sub(patt, ftn_string, txt)
    return txt


# start_date = 7/22/2020
# end date = 4/22/2023
if __name__ == '__main__':
    scrape()

# TODO
# Put number map in a separate file?
# Make into a class modifying the shared list with a run() function
