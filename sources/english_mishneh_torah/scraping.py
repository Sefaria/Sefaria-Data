from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from datetime import date, timedelta
from bs4 import BeautifulSoup
import re

number_map = {
    "Chapter One": 1,
    "Chapter Two": 2,
    "Chapter Three": 3,
    "Chapter Four": 4,
    "Chapter Five": 5,
    "Chapter Six": 6,
    "Chapter Seven": 7,
    "Chapter Eight": 8,
    "Chapter Nine": 9,
    "Chapter Ten": 10,
    "Chapter Eleven": 11,
    "Chapter Twelve": 12,
    "Chapter 12": 12,
    "Chapter Thirteen": 13,
    "Chapter Fourteen": 14,
    "Chapter Fifteen": 15,
    "Chapter Sixteen": 16,
    "Chapter Seventeen": 17,
    "Chapter Eighteen": 18,
    "Chapter Nineteen": 19,
    "Chapter Twenty": 20,
    "Chapter Twenty One": 21,
    "Chapter Twenty Two": 22,
    "Chapter Twenty Three": 23,
    "Chapter Twenty Four": 24,
    "Chapter Twenty Five": 25,
    "Chapter Twenty Six": 26,
    "Chapter Twenty Seven": 27,
    "Chapter Twenty Eight": 28,
    "Chapter Twenty Nine": 29,
    "Chapter Thirty": 30,
}


# print(soup.prettify())

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


def extract_book_chapter(soup):
    capture = soup.find_all(class_="rambam_h2")[0]
    capture = str(capture)
    regex_tuple = re.findall(r">(.*) - (.*)<", capture)[0]
    book = regex_tuple[0]
    en_chapter = regex_tuple[1]
    num_chapter = number_map[en_chapter]
    print(f"book: {book}, en_chap: {en_chapter}, num_chap: {num_chapter}")
    return book, num_chapter


def scrape_text(soup, book, num_chapter, halakha_dict):
    text_array = soup.find_all(class_='co_verse')
    for halakha in text_array:
        halakha_str = str(halakha)
        num = re.findall(r"<span class=\"co_verse\" index=\"(\d*?)\">", halakha_str)
        num = num[0] if len(num) > 0 else None  # None in case of end / sikum etc
        # print(num)
        txt = re.findall(r"<span class=\"co_verse\" index=\"\d*\">.*?</a>(.*)</span>", halakha_str, re.DOTALL)
        txt = txt[0] if len(txt) > 0 else None
        # print(txt)
        if num and txt:
            halakha_dict[f"{book} {num_chapter}.{num}"] = txt


def get_chapter(src, halakha_dict):
    soup = BeautifulSoup(src, 'html.parser')
    book, num_chapter = extract_book_chapter(soup)
    scrape_text(soup, book, num_chapter, halakha_dict)


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


def scrape():
    halakha_dict = {}
    start_date = date(2020, 7, 22)
    # end_date = date(2023, 4, 22)
    end_date = date(2020, 8, 22)

    for single_date in daterange(start_date, end_date):
        date_string = single_date.strftime("%m/%d/%Y")
        src = selenium_firefox_get(f"https://www.chabad.org/dailystudy/rambam.asp?tdate={date_string}&rambamChapters=1")
        get_chapter(src, halakha_dict)

    print(halakha_dict)


# start_date = 7/22/2020
# end date = 4/22/2023
if __name__ == '__main__':
    scrape()
