import requests, codecs, json
from bs4 import BeautifulSoup
from sefaria.model import *

wiki_root = u"https://he.wikisource.org"
root_url_list = [u"https://he.wikisource.org/wiki/%D7%91%D7%91%D7%9C%D7%99_%D7%A1%D7%A0%D7%94%D7%93%D7%A8%D7%99%D7%9F",
                 u"https://he.wikisource.org/wiki/%D7%91%D7%91%D7%9C%D7%99_%D7%92%D7%99%D7%98%D7%99%D7%9F"]
out_obj = {}
for root_url in root_url_list:
    mesechet_page = requests.get(root_url)
    mesechet_soup = BeautifulSoup(mesechet_page.text, "lxml")

    daf_links = list(set([(Ref(daf_link["title"]), daf_link["href"]) for daf_link in mesechet_soup.select("tr td p > a")]))

    for r, l in daf_links:
        print "Requesting", r, l
        daf_page = requests.get(wiki_root + l)
        daf_soup = BeautifulSoup(daf_page.text, "lxml")

        super_scripts = [sup_link for sup_link in daf_soup.select(".gmara_text sup > a")]
        print len(super_scripts)
        #print super_scripts

        gmara_text_soup = daf_soup.select(".gmara_text p")
        all_gmara_text = u""
        super_index_list = []
        super_text_list = []
        for para_gmara in gmara_text_soup:
            direct_children = para_gmara.findChildren(recursive=False)
            curr_dir_child_index = 0
            super_scripts = para_gmara.select("sup > a")
            curr_super_index = 0
            all_descendants = para_gmara.descendants
            complex_child = None
            for desc in all_descendants:
                if complex_child is not None:
                    try:
                        next(complex_child)
                    except StopIteration:
                        complex_child = None
                elif len(direct_children) > curr_dir_child_index and unicode(desc) == unicode(direct_children[curr_dir_child_index]):
                    if len(super_scripts) > curr_super_index and unicode(next(desc.descendants)) == unicode(super_scripts[curr_super_index]):
                        super_index_list += [len(all_gmara_text)+1]
                        super_text_list += [unicode(super_scripts[curr_super_index])]
                        curr_super_index += 1
                    complex_child = direct_children[curr_dir_child_index].descendants
                    try:
                        next(complex_child)  # start at second iteration
                    except StopIteration:
                        complex_child = None
                        print
                    curr_dir_child_index += 1
                else:
                    if len(all_gmara_text) > 0:
                        all_gmara_text += " "
                    all_gmara_text += unicode(desc).strip()

        daf_obj = {
            "text": all_gmara_text,
            "super_indices": super_index_list,
            "super_simanim": super_text_list
        }
        try:
            out_obj[r.book][r.normal()] = daf_obj
        except KeyError:
            out_obj[r.book] = {}
            out_obj[r.book][r.normal()] = daf_obj

f = codecs.open("scraper.out", "wb", encoding='utf8')
json.dump(out_obj, f, ensure_ascii=False, indent=4)
f.close()



#//*[@id="mw-content-text"]/div/table/tbody/tr[3]/td/p[1]/a[1]

#unwrap  - remove html around element
#decompose / deconstruct