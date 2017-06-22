import requests
from bs4 import BeautifulSoup
from sefaria.model import *

wiki_root = u"https://he.wikisource.org"
root_url = u"https://he.wikisource.org/wiki/%D7%91%D7%91%D7%9C%D7%99_%D7%A1%D7%A0%D7%94%D7%93%D7%A8%D7%99%D7%9F"

mesechet_page = requests.get(root_url)
mesechet_soup = BeautifulSoup(mesechet_page.text, "lxml")

daf_links = list(set([(Ref(daf_link["title"]), daf_link["href"]) for daf_link in mesechet_soup.select("tr td p > a")]))

for r, l in daf_links[0:1]:
    print "Requesting", r, l
    daf_page = requests.get(wiki_root + l)
    daf_soup = BeautifulSoup(daf_page.text, "lxml")

    super_scripts = [ (sup_link.get_text(), sup_link["href"]) for sup_link in daf_soup.select(".gmara_text sup > a")]
    print len(super_scripts)
    #print super_scripts
    yo = [y for y in daf_soup.select(".gmara_text p")[0].descendants]
    for y in yo:
        print yo
#//*[@id="mw-content-text"]/div/table/tbody/tr[3]/td/p[1]/a[1]

#unwrap  - remove html around element
#decompose / deconstruct