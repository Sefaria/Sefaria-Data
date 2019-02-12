# encoding=utf-8

import re
import codecs
import requests
from bs4 import BeautifulSoup
from multiprocessing.dummy import Pool


def is_link(element):
    return element.name == 'a' and re.search(u'התורה והמצוה ויקרא', element.get('title', u'')) is not None


def get_and_dump((num, link_element)):
    doc_url = link_element['href']
    if not re.match(u'^https', doc_url):
        doc_url = u'https://he.wikisource.org{}'.format(link_element['href'])
    try:
        web_response = requests.get(doc_url)
    except requests.exceptions.ConnectionError:
        print u"Problem with {}".format(doc_url)
        return
    with codecs.open(u'./webpages/{}.html'.format(num), 'w', 'utf-8') as fp:
        fp.write(web_response.text)


url = u'https://he.wikisource.org/wiki/%D7%A7%D7%98%D7%92%D7%95%D7%A8%D7%99%D7%94:%D7%94%D7%AA%D7%95%D7%A8%D7%94_%D7%95%D7%94%D7%9E%D7%A6%D7%95%D7%94_%D7%A2%D7%9C_%D7%95%D7%99%D7%A7%D7%A8%D7%90'
response = requests.get(url)
soup = BeautifulSoup(response.text, 'lxml')

links = list(soup.find_all(is_link))

# no static link to the second page, so I downloaded it
with codecs.open('links_page2.html', 'r', 'utf-8') as fp:
    soup = BeautifulSoup(fp, 'lxml')
links.extend(list(soup.find_all(is_link)))

pool = Pool(25)
pool.map(get_and_dump, enumerate(links))
