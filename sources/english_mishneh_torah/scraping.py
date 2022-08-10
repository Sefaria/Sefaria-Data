from selenium import webdriver
from selenium.webdriver.firefox.options import Options
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
    "Chapter Twenty": 20
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


def scrape_text(soup, book, num_chapter):
    text_array = soup.find_all(class_='co_verse')
    halakha_dict = {}
    for halakha in text_array:
        halakha_str = str(halakha)
        num = re.findall(r"<span class=\"co_verse\" index=\"(\d*?)\">", halakha_str)
        num = num[0] if len(num) > 0 else None # None in case of end / sikum etc
        # print(num)
        txt = re.findall(r"<span class=\"co_verse\" index=\"\d*\">.*?</a>(.*)</span>", halakha_str, re.DOTALL)
        txt = txt[0] if len(txt) > 0 else None
        # print(txt)
        if num and txt:
            halakha_dict[f"{book} {num_chapter}.{num}"] = txt

    return halakha_dict



def scrape_chapter(src):
    soup = BeautifulSoup(src, 'html.parser')
    book, num_chapter = extract_book_chapter(soup)
    print(scrape_text(soup, book, num_chapter))


# start_date = 7/22/2020
# end date = 4/22/2023
if __name__ == '__main__':
    src = selenium_firefox_get("https://www.chabad.org/dailystudy/rambam.asp?tdate=4/22/2023&rambamChapters=1")
    scrape_chapter(src)
