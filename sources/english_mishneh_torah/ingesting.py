from sources.functions import selenium_get_url
import requests
from requests_html import HTMLSession
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import bs4


def selenium_firefox_get(url):
    profile = webdriver.FirefoxProfile()
    profile.set_preference("javascript.enabled", False);

    options = Options()
    options.headless = True

    driver = webdriver.Firefox(profile, options=options)
    driver.get(url)
    src = driver.page_source
    return src


print(selenium_firefox_get("https://www.chabad.org/dailystudy/rambam.asp?tdate=8/12/2022&rambamChapters=1"))
