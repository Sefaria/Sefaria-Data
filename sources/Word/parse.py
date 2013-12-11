import re
import os
import json
import urllib
import urllib2
from urllib2 import HTTPError

POSTHOST = "http://dev.sefaria.org"


def getChapters(filename):
    """
    Builds Mesechet List from MishnayotNotes.txt
    """
    f = open(filename)
    mesechet = ""
    mesechet_list = []
    for line in f:
        if line.strip() == '':
            pass
        elif re.search(r'Seder\s\S+\n', line):
            pass
        elif re.search(r'Mishnayot Notes', line):
            pass
        elif re.search(r'Mesechet\s(\S+)\n', line):
            if not mesechet:
                mesechet = line
            else:
                mesechet_list.append(mesechet)
                mesechet = line
        else:
            mesechet += line
    return mesechet_list


def makePage(name, text):
    """
    Take a name and text, and create a file in ./pages corresponding
    to that information
    """
    ls = os.listdir("./pages")
    if name in ls:
        print "Already have %s" % (name)
        return
    print "Building %s" % (name)
    f = open("./pages/%s" % (name), "w")
    f.write(text)
    f.close()

    print 'OK'


def buildPages(mesechet_list):
    """
    Take a list of Mesechet and then build a directory ./pages/:ref:
    that splits every Mesechet into each chapter. If the Mesechet is Brachot
    the file it creates are Brachot.1, Brachot.2, etc...
    """
    for mesechet in mesechet_list:
        name = ""
        match = re.search('Mesechet\s(\S+)\n', mesechet)
        if not match:
            print "Problem in buildPages"
        else:
            name = match.group(1)
            text = ""
            count = 1
            for line in mesechet.splitlines():
                # regex for chapters
                match_perek = re.search(r'Perek\s.+', line)
                # regex for headers
                match_mesechet = re.search(r'Mesechet\s.+', line)
                if match_mesechet:  # if the line is a header skip it
                    continue
                if match_perek:  # if a line is a chapter
                    if not text:
                        pass  # if its the first chapter, dont do anything
                    else:
                        match = re.search(r'\.(\d)+', name)  # regex for the name
                        if match:
                            result = match.group()
                            if len(result) == 2:  # 1 digit after dot
                                name = name[:-2]  # cut off digit + dot
                            else:  # 2 digits after dot
                                name = name[:-3]  # cut off digits + dot
                        name = "%s.%d" % (name, count)  # change name to new name
                        count += 1
                        makePage(name, text)  # actually make the page
                        text = ""  # reset text
                else:
                    text += line + "\n"  # build text, adding in new lines


def parseChapter(filename):
    f = open("./pages/%s" % (filename))
    chapter = f.read()
    f.close()
    text = []
    # count = 1

    for line in chapter.splitlines():
        line = re.sub(r'\w+:\s', "", line)
        text.append(line)

    parsed = {
        "language": "en",
        "versionTitle": "TBD",
        "versionUrl": "TBD"
    }

    parsed["text"] = text
    return parsed


def parseAll():
    ls = os.listdir("./pages")
    for filename in ls:
        if not "." in filename or filename == ".DS_Store":
            continue
        print filename
        parsed = parseChapter("%s" % (filename))

        if parsed:
            f = open("parsed/%s" % (filename), "w")
            json.dump(parsed, f, ensure_ascii=False, indent=4)
            f.close()
            print "ok: found %d mishnas" % len(parsed["text"])


def postText(filename):
    f = open("./parsed/%s" % (filename), "r")
    textJSON = f.read()
    f.close()
    ref = filename.replace("-", "_").replace("_1", "_I").replace("_2", "_II")

    url = '%s/api/texts/%s' % (POSTHOST, ref)
    values = {'json': textJSON,
              'apikey': 'VCmaCDRYFADsixeW3njZUnDhEMqkBm7N9EhCmreuyyI'}
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
