# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup, NavigableString
import urllib, urllib2
from urllib2 import HTTPError
import urlparse
import re
import json

from sefaria.utils.hebrew import encode_hebrew_numeral

apikey = "uK9JdRhOiLfWtaf558CtM9f89M9pclF9VuyMZtFW0as"

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

server = u"localhost:8000"
base = u"http://he.wikisource.org/wiki/"

sections_bases = {
    u"אורות_ארץ_ישראל_פרק" + u"_" : (u"Orot, Lights from Darkness, Land of Israel", 8),
    u"אורות_המלחמה_פרק" + u"_" :  (u"Orot, Lights from Darkness, War", 10),
    u"אורות_ישראל_ותחייתו" + u"_" : (u"Orot, Lights from Darkness, Israel and its Rebirth", 32),
    #u"אורות_התחיה_פרק" + u"_" : (u"Orot, Lights from Darkness, Lights of Rebirth", 72) # 34 - length 4, 12 - length 3, 5 - length 2
}

for url, (node_addr, r) in sections_bases.iteritems():
    print url
    node_data = []
    for i in range(1, r + 1):
        print str(i) + u" "
        full_url = base + url + encode_hebrew_numeral(i, False)
        page = urllib.urlopen(iriToUri(full_url))
        page_soup = BeautifulSoup(page.read())
        contents = page_soup.find(id="mw-content-text").find_all('p')[2:]
        res = []
        for i in contents:
            res += re.split("\n", i.text)
        res = [i for i in res if i != ""]
        node_data += [res]
    j = {
        "versionTitle": "Wikisource",
        "versionSource": "http://he.wikisource.org",
        "language": "he",
        "text": node_data
    }
    postText(server, apikey, node_addr, j)


