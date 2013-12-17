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
    currentMesechet = ""
    mesechet_list = {}
    reSeder = re.compile(r'Seder\s\S+\n')
    reMishnayot = re.compile(r'Mishnayot Notes')
    reMesechet = re.compile(r'Mesechet\s(\S+)\n?\s?(\S+)?\n')
    for line in f:
        sederMatchCheck = reSeder.search(line)
        mishnayotMatchCheck = reMishnayot.search(line)
        mesechetMatchCheck = reMesechet.search(line)
        if mishnayotMatchCheck or sederMatchCheck:
            pass
        elif mesechetMatchCheck:
            line = line.strip()
            mesechet_list[line] = ""
            currentMesechet = line
        else:
            if currentMesechet:
                mesechet_list[currentMesechet] += line
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
    that splits every Mesechet into each chapter. If the Mesechet is Berakhot
    the file it creates are Berakhot.1, Berakhot.2, etc...
    """
    for key, value in mesechet_list.iteritems():
        name = ''
        for segment in key.split():
            # Don't add Mesechet part of dictionary to name
            if segment == key.split()[0]:
                pass
            else:
                name += segment + " "
        print name.strip()
        # text = ""
        # count = 1
        for line in value.splitlines():
            # regex for chapters
            match_perek = re.search(r'Perek\s.+', line)
            if line == '':
                pass
            if match_perek:  # if a line is a chapter
                print line
                pass
            #     if not text:
            # pass  # if its the first chapter, dont do anything
            #     else:
            # regex for the name
            #         match = re.search(r'\.(\d)+', name)
            #         if match:
            #             result = match.group()
            # if len(result) == 2:  # 1 digit after dot
            # name = name[:-2]  # cut off digit + dot
            # else:  # 2 digits after dot
            # name = name[:-3]  # cut off digits + dot
            # change name to new name
            #         name = "%s.%d" % (name, count)
            #         count += 1
            # makePage(name, text)  # actually make the page
            # text = ""  # reset text
            # else:
            # text += line + "\n"  # build text, adding in new lines


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
        "versionTitle": "Natan Stein Mishnah",
        "versionSource": "www.sefaria.org/contributed-text"
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

    url = '%s/api/texts/Mishna_%s' % (POSTHOST, ref)
    values = {'json': textJSON,
              'apikey': 'VCmaCDRYFADsixeW3njZUnDhEMqkBm7N9EhCmreuyyI'}
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    try:
        response = urllib2.urlopen(req)
        print response.read()
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
        postText(f)
