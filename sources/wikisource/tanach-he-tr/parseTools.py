import urllib
import urllib2
from urllib2 import URLError, HTTPError
import json
import os
from pprint import pprint
from BeautifulSoup import BeautifulSoup

POSTHOST = "http://www.sefaria.org" 


def parseChapter(name):
    f = open("./pages/%s" % (name), "r")
    page = f.read()
    f.close()

    soup = BeautifulSoup(page)

    spans = soup.findAll(style="font-size:60%;")

    parsed = {
        "language": "he",
        "versionTitle": "Wikisource Tanach with Trop",
        "versionSource": "http://he.wikisource.org/wiki/%D7%9E%D7%A7%D7%A8%D7%90",
        "text": []
    }

    for i in range(len(spans)):
        line = ""
        next = spans[i].nextSibling
        while next:
            if hasattr(next, "name"): # Not a text node, either a span or a small
                if next.name == "span": # This is the next verse marker
                    break
                else: # This is a small
                    if next.name != "small":
                        print "Unexpected tag: %s (%s)" % (next.name, name)
                    line += next.text.encode("utf-8")
            else: # This is text
                line += next.encode("utf-8")
            next = next.nextSibling
        parsed["text"].append(line.strip())

    f = open("./parsed/%s" % (name), "w")

    json.dump(parsed, f, ensure_ascii=False)
    f.close()

    return parsed


def parseLinks(seedFile):
    print "Getting links from %s" % (seedFile)
    f = open("./pages/%s" % (seedFile), "r")
    page = f.read()
    f.close

    soup = BeautifulSoup(page)

    start = soup.findAll("strong", "selflink")

    if len(start) < 2:
        print "No links found in %s" % (seedFile)
        return
    else:
        start = start[1]

    p = start.parent

    a = p.findAll("a")

    links = ["", ""]
    for link in a:
        links.append("http://he.wikisource.org" + link["href"])

    return links


def wikiGet(url, name):
    ls = os.listdir("./pages")

    if name in ls:
        print "Already have %s" % (name)
        return

    print "Getting %s" % (name)
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    page = opener.open(url)

    print "Ok"
    f = open("./pages/%s" %(name), "w")
    f.write(page.read())
    f.close()


def getSeeds():
    for seed in seeds:
        wikiGet(seeds[seed], "%s.1" % (seed))


def getAll():
    for seed in seeds:
        links = parseLinks("%s.1" % (seed))
        for i in range(2, len(links)):
            wikiGet(links[i], "%s.%d" % (seed, i))


def parseAll():
    files = os.listdir("./pages")

    for f in files:
        print "parsing %s" % f
        parsed = parseChapter(f)
        f = open("./parsed/%s" %(f), "w")
        f.write(json.dumps(parsed, indent=4))
        f.close()


def postText(filename):
    f = open("./parsed/%s" % (filename), "r")
    textJSON = f.read()
    f.close()
    ref = filename.replace("-", "_").replace("_1", "_I").replace("_2", "_II")

    url = '%s/api/texts/%s' % (POSTHOST, ref)
    values = {'json': textJSON, 'apikey': 'VCmaCDRYFADsixeW3njZUnDhEMqkBm7N9EhCmreuyyI'}
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    try:
        response = urllib2.urlopen(req)
        print "Posted %s" % (ref)
    except HTTPError, e:
        print 'Error code: ', e.code
        print e.read()


def postAll(prefix=None, after=None):
    files = os.listdir("./parsed")

    for f in files:
        if prefix and f.startswith(prefix):
            continue
        if after and f < after:
            continue

        parsed = postText(f)


seeds = {
    "Amos": "http://he.wikisource.org/wiki/%D7%A2%D7%9E%D7%95%D7%A1_%D7%90/%D7%98%D7%A2%D7%9E%D7%99%D7%9D",
    "Chronicles-1": "http://he.wikisource.org/wiki/%D7%93%D7%91%D7%A8%D7%99_%D7%94%D7%99%D7%9E%D7%99%D7%9D_%D7%90_%D7%90/%D7%98%D7%A2%D7%9E%D7%99%D7%9D",
    "Chronicles-2": "http://he.wikisource.org/wiki/%D7%93%D7%91%D7%A8%D7%99_%D7%94%D7%99%D7%9E%D7%99%D7%9D_%D7%91_%D7%90/%D7%98%D7%A2%D7%9E%D7%99%D7%9D",
    "Daniel": "http://he.wikisource.org/wiki/%D7%93%D7%A0%D7%99%D7%90%D7%9C_%D7%90/%D7%98%D7%A2%D7%9E%D7%99%D7%9D",
    "Deuteronomy": "http://he.wikisource.org/wiki/%D7%93%D7%91%D7%A8%D7%99%D7%9D_%D7%90/%D7%98%D7%A2%D7%9E%D7%99%D7%9D",
    "Ecclesiastes": "http://he.wikisource.org/wiki/%D7%A7%D7%94%D7%9C%D7%AA_%D7%90/%D7%98%D7%A2%D7%9E%D7%99%D7%9D",
    "Esther": "http://he.wikisource.org/wiki/%D7%90%D7%A1%D7%AA%D7%A8_%D7%90/%D7%98%D7%A2%D7%9E%D7%99%D7%9D",
    "Exodus": "http://he.wikisource.org/wiki/%D7%A9%D7%9E%D7%95%D7%AA_%D7%90/%D7%98%D7%A2%D7%9E%D7%99%D7%9D",
    "Ezekiel": "http://he.wikisource.org/wiki/%D7%99%D7%97%D7%96%D7%A7%D7%90%D7%9C_%D7%90/%D7%98%D7%A2%D7%9E%D7%99%D7%9D",
    "Ezra": "http://he.wikisource.org/wiki/%D7%A2%D7%96%D7%A8%D7%90_%D7%90/%D7%98%D7%A2%D7%9E%D7%99%D7%9D",
    "Genesis": "http://he.wikisource.org/wiki/%D7%91%D7%A8%D7%90%D7%A9%D7%99%D7%AA_%D7%90/%D7%98%D7%A2%D7%9E%D7%99%D7%9D",
    "Habakkuk": "http://he.wikisource.org/wiki/%D7%97%D7%91%D7%A7%D7%95%D7%A7_%D7%90/%D7%98%D7%A2%D7%9E%D7%99%D7%9D",
    "Haggai": "http://he.wikisource.org/wiki/%D7%97%D7%92%D7%99_%D7%90/%D7%98%D7%A2%D7%9E%D7%99%D7%9D",
    "Hosea": "http://he.wikisource.org/wiki/%D7%94%D7%95%D7%A9%D7%A2_%D7%90/%D7%98%D7%A2%D7%9E%D7%99%D7%9D",
    "Isaiah": "http://he.wikisource.org/wiki/%D7%99%D7%A9%D7%A2%D7%99%D7%94%D7%95_%D7%90/%D7%98%D7%A2%D7%9E%D7%99%D7%9D",
    "Jeremiah": "http://he.wikisource.org/wiki/%D7%99%D7%A8%D7%9E%D7%99%D7%94%D7%95_%D7%90/%D7%98%D7%A2%D7%9E%D7%99%D7%9D",
    "Job": "http://he.wikisource.org/wiki/%D7%90%D7%99%D7%95%D7%91_%D7%90/%D7%98%D7%A2%D7%9E%D7%99%D7%9D",
    "Joel": "http://he.wikisource.org/wiki/%D7%99%D7%95%D7%90%D7%9C_%D7%90/%D7%98%D7%A2%D7%9E%D7%99%D7%9D",
    "Jonah": "http://he.wikisource.org/wiki/%D7%99%D7%95%D7%A0%D7%94_%D7%90/%D7%98%D7%A2%D7%9E%D7%99%D7%9D",
    "Joshua": "http://he.wikisource.org/wiki/%D7%99%D7%94%D7%95%D7%A9%D7%A2_%D7%90/%D7%98%D7%A2%D7%9E%D7%99%D7%9D",
    "Judges": "http://he.wikisource.org/wiki/%D7%A9%D7%95%D7%A4%D7%98%D7%99%D7%9D_%D7%90/%D7%98%D7%A2%D7%9E%D7%99%D7%9D",
    "Kings-1": "http://he.wikisource.org/wiki/%D7%9E%D7%9C%D7%9B%D7%99%D7%9D_%D7%90_%D7%90/%D7%98%D7%A2%D7%9E%D7%99%D7%9D",
    "Kings-2": "http://he.wikisource.org/wiki/%D7%9E%D7%9C%D7%9B%D7%99%D7%9D_%D7%91_%D7%90/%D7%98%D7%A2%D7%9E%D7%99%D7%9D",
    "Lamentations": "http://he.wikisource.org/wiki/%D7%90%D7%99%D7%9B%D7%94_%D7%90/%D7%98%D7%A2%D7%9E%D7%99%D7%9D",
    "Leviticus": "http://he.wikisource.org/wiki/%D7%95%D7%99%D7%A7%D7%A8%D7%90_%D7%90/%D7%98%D7%A2%D7%9E%D7%99%D7%9D",
    "Malachi": "http://he.wikisource.org/wiki/%D7%9E%D7%9C%D7%90%D7%9B%D7%99_%D7%90/%D7%98%D7%A2%D7%9E%D7%99%D7%9D",
    "Micah": "http://he.wikisource.org/wiki/%D7%9E%D7%99%D7%9B%D7%94_%D7%90/%D7%98%D7%A2%D7%9E%D7%99%D7%9D",
    "Nahum": "http://he.wikisource.org/wiki/%D7%A0%D7%97%D7%95%D7%9D_%D7%90/%D7%98%D7%A2%D7%9E%D7%99%D7%9D",
    "Nehemiah": "http://he.wikisource.org/wiki/%D7%A0%D7%97%D7%9E%D7%99%D7%94_%D7%90/%D7%98%D7%A2%D7%9E%D7%99%D7%9D",
    "Numbers": "http://he.wikisource.org/wiki/%D7%91%D7%9E%D7%93%D7%91%D7%A8_%D7%90/%D7%98%D7%A2%D7%9E%D7%99%D7%9D",
    "Obadiah": "http://he.wikisource.org/wiki/%D7%A2%D7%95%D7%91%D7%93%D7%99%D7%94_%D7%90/%D7%98%D7%A2%D7%9E%D7%99%D7%9D",
    "Proverbs": "http://he.wikisource.org/wiki/%D7%9E%D7%A9%D7%9C%D7%99_%D7%90/%D7%98%D7%A2%D7%9E%D7%99%D7%9D",
    "Psalms": "http://he.wikisource.org/wiki/%D7%AA%D7%94%D7%9C%D7%99%D7%9D_%D7%90/%D7%98%D7%A2%D7%9E%D7%99%D7%9D",
    "Ruth": "http://he.wikisource.org/wiki/%D7%A8%D7%95%D7%AA_%D7%90/%D7%98%D7%A2%D7%9E%D7%99%D7%9D",
    "Samuel-1": "http://he.wikisource.org/wiki/%D7%A9%D7%9E%D7%95%D7%90%D7%9C_%D7%90_%D7%90/%D7%98%D7%A2%D7%9E%D7%99%D7%9D",
    "Samuel-2": "http://he.wikisource.org/wiki/%D7%A9%D7%9E%D7%95%D7%90%D7%9C_%D7%91_%D7%90/%D7%98%D7%A2%D7%9E%D7%99%D7%9D",
    "Song-of-Songs": "http://he.wikisource.org/wiki/%D7%A9%D7%99%D7%A8_%D7%94%D7%A9%D7%99%D7%A8%D7%99%D7%9D_%D7%90/%D7%98%D7%A2%D7%9E%D7%99%D7%9D",
    "Zechariah": "http://he.wikisource.org/wiki/%D7%96%D7%9B%D7%A8%D7%99%D7%94_%D7%90/%D7%98%D7%A2%D7%9E%D7%99%D7%9D",
    "Zephaniah": "http://he.wikisource.org/wiki/%D7%A6%D7%A4%D7%A0%D7%99%D7%94_%D7%90/%D7%98%D7%A2%D7%9E%D7%99%D7%9D"

}

