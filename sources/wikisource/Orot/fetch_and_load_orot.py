# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup, NavigableString
import urllib, urllib2
from urllib2 import HTTPError
import urlparse
import re
import json

from sefaria.utils.hebrew import encode_hebrew_numeral

def urlEncodeNonAscii(b):
    return re.sub('[\x80-\xFF]', lambda c: '%%%02x' % ord(c.group(0)), b)

def iriToUri(iri):
    parts= urlparse.urlparse(iri)
    return urlparse.urlunparse(
        part.encode('idna') if parti==1 else urlEncodeNonAscii(part.encode('utf-8'))
        for parti, part in enumerate(parts)
    )

def postText(server, apikey, ref, text):
    textJSON = json.dumps(text)
    ref = ref.replace(" ", "_")
    url = 'http://' + server + '/api/texts/%s?count_after=0&index_after=0' % ref
    print url
    values = {
        'json': textJSON,
        'apikey': apikey
    }
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    try:
        response = urllib2.urlopen(req)
        print response.read()
    except HTTPError, e:
        print 'Error code: ', e.code
        print e.read()


def get_single(url, offset):
    page = urllib.urlopen(iriToUri(url))
    page_soup = BeautifulSoup(page.read())
    contents = page_soup.find(id="mw-content-text").find_all('p')[offset:]
    res = []
    for i in contents:
        res += re.split("\n", i.text)
    res = [i for i in res if i != ""]
    return res


server = u"staging.sefaria.org"
base = u"http://he.wikisource.org/wiki/"
apikey = "uK9JdRhOiLfWtaf558CtM9f89M9pclF9VuyMZtFW0as"

j = {
    "versionTitle": "Wikisource",
    "versionSource": "http://he.wikisource.org",
    "language": "he",
}

# Single node on a single page
singles = {
    u"קריאה_גדולה" : (u"Orot, Lights from Darkness, Great Calling", 0, 2),
    u"אורות_ישראל_פרק_א" : (u"Orot, Lights of Israel, The Essence of Israel", 16, 2),
    u"אורות_ישראל_פרק_ה" : (u"Orot, Lights of Israel, Israel and the Nations", 16, 2),
    u"אורות_ישראל_פרק_ו" : (u"Orot, Lights of Israel, Nationhood of Israel", 9, 2),
    u"אורות_ישראל_פרק_ז" : (u"Orot, Lights of Israel, Israel's Soul and its Rebirth", 19, 2),
    u"אורות_ישראל_פרק_ח" : (u"Orot, Lights of Israel, Preciousness of Israel", 9, 2),
    u"אורות_ישראל_פרק_ט" : (u"Orot, Lights of Israel, Holiness of Israel", 9, 2),
    u"אורות_-_זרעונים_-_א._צמאון_לאל_חי" : (u"Orot, Seeds, Thirst for the Living God", 0, 1),
    u"אורות_-_זרעונים_-_ב._חכם_עדיף_מנביא" : (u"Orot, Seeds, The Wise is Preferable to Prophet", 0, 1),
    u"אורות_-_זרעונים_-_ג._הנשמות_של_עולם_התוהו" : (u"Orot, Seeds, The Souls of the World of Chaos", 0, 1),
    u"אורות_-_זרעונים_-_ד._מעשי_יצירה" : (u"Orot, Seeds, Acts of Creation", 0, 1),
    u"אורות_-_זרעונים_-_ה._יסורים_ממרקים" : (u"Orot, Seeds, Suffering Cleanses", 0, 1),
    u"אורות_-_זרעונים_-_ו._למלחמת_הדעות_והאמונות" : (u"Orot, Seeds, The War of Ideas", 0, 1),
    u"אורות_-_זרעונים_-_ז._נשמת_הלאומיות_וגופה" : (u"Orot, Seeds, National Soul and Body", 0, 1),
    u"אורות_-_זרעונים_-_ח._ערך_התחיה" : (u"Orot, Seeds, The Value of Rebirth", 0, 1)
}

for url, (node_addr, r, offset) in singles.iteritems():
    print url
    full_url = base + url
    j["text"] = get_single(full_url, offset)
    if r and len(j["text"]) != r:
        print u"{} has length {}, but should have {}".format(url, len(j["text"]), r)
    postText(server, apikey, node_addr, j)



# The Process of Ideals - Multiple sections on one page
m_secs = [
    u"Orot, The Process of Ideals in Israel, The Godly and the National Ideal in the Individual",
    u"Orot, The Process of Ideals in Israel, The Godly and the National Ideal in Israel",
    u"Orot, The Process of Ideals in Israel, Dissolution of Ideals",
    u"Orot, The Process of Ideals in Israel, The Situation in Exile",
    u"Orot, The Process of Ideals in Israel, The First and Second Temples; Religion",
    u"Orot, The Process of Ideals in Israel, Unification of Ideals"
]

res = []
full_url = base + u'למהלך_האידיאות_בישראל'
page = urllib.urlopen(iriToUri(full_url))
page_soup = BeautifulSoup(page.read())

w = page_soup.find(id="mw-content-text")
sub = []
for c in w.children:
    if c.name == "p" and c.text:
        sub += [c.text]
    if c.name == "h2" and sub:
        res += [sub[:]]
        sub = []
res += [sub[:]]

for i, content in enumerate(res):
    j["text"] = content
    node_addr = m_secs[i]
    print node_addr
    postText(server, apikey, node_addr, j)



# 2-Layered texts on numbered sub pages
sections_bases = {
    u"אורות_ארץ_ישראל_פרק" + u"_" : (u"Orot, Lights from Darkness, Land of Israel", 8, 2),
    u"אורות_המלחמה_פרק" + u"_" :  (u"Orot, Lights from Darkness, War", 10, 2),
    u"אורות_ישראל_ותחייתו_פרק" + u"_" : (u"Orot, Lights from Darkness, Israel and its Rebirth", 32, 2),
    u"אורות_התחיה_פרק" + u"_" : (u"Orot, Lights from Darkness, Lights of Rebirth", 72, 2), # 34 - length 4, 12 - length 3, 5 - length 2
}

for url, (node_addr, r, offset) in sections_bases.iteritems():
    print url
    node_data = []
    for i in range(1, r + 1):
        print str(i) + u" "
        full_url = base + url + encode_hebrew_numeral(i, False)
        node_data += [get_single(full_url, offset)]
    j["text"] = node_data
    postText(server, apikey, node_addr, j)

# 1-layered text on numbered sub-pages
sections_bases = {
    u"אורות_ישראל_פרק_ב_פסקה" + u"_" : (u"Orot, Lights of Israel, The Individual and the Collective", 8, 0),
    u"אורות_ישראל_פרק_ג_פסקה" + u"_" : (u"Orot, Lights of Israel, Connection to the Collective", 11, 0),
    u"אורות_ישראל_פרק_ד_פסקה" + u"_" : (u"Orot, Lights of Israel, Love of Israel", 10, 0),
}

for url, (node_addr, r, offset) in sections_bases.iteritems():
    print url
    node_data = []
    for i in range(1, r + 1):
        print str(i) + u" "
        full_url = base + url + encode_hebrew_numeral(i, False)
        node_data += [u" ".join(get_single(full_url, offset))]
    j["text"] = node_data
    postText(server, apikey, node_addr, j)
