# -*- coding: utf-8 -*-
import os, sys, re
import urllib2

p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
from local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "local_settings"

from data_utilities.util import numToHeb

reload(sys)
sys.setdefaultencoding("utf-8")


def wikiGet(url, title):
    print url

    try:
        opener = urllib2.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        page = opener.open(url)
        print "got", title
        with open("./pages/{}".format(title), "w") as file:
            file.write(page.read())

    except:
        print "page doesn't exist", title


for siman in range(1, 697): #696 simanim in O.C
    title = "Biur_Halacha." + str(siman)
    wikiGet(u"https://he.wikisource.org/w/index.php?title=ביאור_הלכה_על_אורח_חיים_%s&printable=yes" %(numToHeb(siman)), title)
