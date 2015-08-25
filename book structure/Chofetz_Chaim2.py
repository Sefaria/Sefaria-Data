# -*- coding: utf-8 -*-
import urllib
import urllib2
from urllib2 import URLError, HTTPError
import json 
import pdb
import os
import re
import sys
p = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, p)
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from local_settings import *

sys.path.insert(0, SEFARIA_PROJECT_PATH)

from sefaria.model import *

def numToHeb(engnum=""):
	engnum = str(engnum)
	numdig = len(engnum)
	hebnum = ""
	letters = [["" for i in range(3)] for j in range(10)]
	letters[0]=["", "א", "ב", "ג", "ד", "ה", "ו", "ז", "ח", "ט"]
	letters[1]=["", "י", "כ", "ל", "מ", "נ", "ס", "ע", "פ", "צ"]
	letters[2]=["", "ק", "ר", "ש", "ת", "תק", "תר", "תש", "תת", "תתק"]
	if (numdig > 3):
		print "We currently can't handle numbers larger than 999"
		exit()
	for count in range(numdig):
		hebnum += letters[numdig-count-1][int(engnum[count])]
	hebnum = re.sub('יה', 'טו', hebnum)
	hebnum = re.sub('יו', 'טז', hebnum)
	return hebnum.decode('utf-8')

def post_index(index):
	url = SEFARIA_SERVER+'/api/v2/raw/index/' + index["title"].replace(" ", "_")
	indexJSON = json.dumps(index)
	values = {
		'json': indexJSON, 
		'apikey': API_KEY
	}
	data = urllib.urlencode(values)
	req = urllib2.Request(url, data)
	try:
		response = urllib2.urlopen(req)
		print response.read()
	except HTTPError, e:
		print 'Error code: ', e.code


root = SchemaNode()
root.add_title("Chofetz Chaim", "en", primary=True)
root.add_title("Chafetz Chaim", "en", primary=False)
root.add_title("Hafetz Hayim", "en", primary=False)
root.add_title(u"חפץ חיים", "he", primary=True)
root.add_title(u"ספר חפץ חיים", "he", primary=False)
root.key = "chofetz_chaim"

intro = JaggedArrayNode()
intro.add_title("Preface", "en", primary=True)
intro.add_title(u"הקדמה", "he", primary=True)
intro.key = "intro"
intro.depth = 1
intro.sectionNames = ["Paragraph"]
intro.addressTypes = ["Integer"]


intro2 = SchemaNode()
intro2.add_title("Introduction to the Laws of the Prohibition of Lashon Hara and Rechilut", "en", primary=True)
intro2.add_title(u"פתיחה להלכות לשון הרע ורכילות", "he", primary=True)
intro2.key = "intro2"

intro2a = JaggedArrayNode()
intro2a.add_title("Opening Comments", "en", primary=True)
intro2a.add_title(u"הקדמה", "he", primary=True)
intro2a.key = "intro2a"
intro2a.depth = 1
intro2a.sectionNames = ["Paragraph"]
intro2a.addressTypes = ["Integer"]

intro2_neg = JaggedArrayNode()
intro2_neg.add_title("Negative Commandments", "en", primary=True)
intro2_neg.add_title(u"לאוין", "he", primary=True)
intro2_neg.key = "intro2-neg"
intro2_neg.depth = 1
intro2_neg.sectionNames = ["Paragraph"]
intro2_neg.addressTypes = ["Integer"]

intro2_pos = JaggedArrayNode()
intro2_pos.add_title("Positive Commandments", "en", primary=True)
intro2_pos.add_title(u"עשיין", "he", primary=True)
intro2_pos.key = "intro2-pos"
intro2_pos.depth = 1
intro2_pos.sectionNames = ["Paragraph"]
intro2_pos.addressTypes = ["Integer"]

intro2_curses = JaggedArrayNode()
intro2_curses.add_title("Curses", "en", primary=True)
intro2_curses.add_title(u"ארורין", "he", primary=True)
intro2_curses.key = "intro2-curses"
intro2_curses.depth = 1
intro2_curses.sectionNames = ["Paragraph"]
intro2_curses.addressTypes = ["Integer"]

intro2.append(intro2a)
intro2.append(intro2_neg)
intro2.append(intro2_pos)
intro2.append(intro2_curses)


part1 = SchemaNode()
part1.add_title("Part One, The Prohibition Against Lashon Hara", "en", primary=True)
part1.add_title(u"חלק ראשון: הלכות איסורי לשון הרע", "he", primary=True)
part1.key = "part1"
lengths = [9, 13, 8, 12, 8, 12, 14, 14, 6, 17]
for count in range(10):
	part1_prin1 = SchemaNode()
	part1_prin1.add_title("Principle "+str(count+1), "en", primary=True)
	part1_prin1.add_title(u"כלל "+numToHeb(count+1), "he", primary=True)
	part1_prin1.key="part1_prin"+str(count)

	part1_prin1_intro = JaggedArrayNode()
	part1_prin1_intro.key = "intro"+str(count+1)
	part1_prin1_intro.add_title("Opening Comments", "en", primary=True)
	part1_prin1_intro.add_title(u"הערות מקדימות", "he", primary=True)
	part1_prin1_intro.depth = 1
	part1_prin1_intro.sectionNames = ["Paragraph"]
	part1_prin1_intro.addressTypes = ["Integer"]

	part1_prin1_content = JaggedArrayNode()
	part1_prin1_content.default = True
	part1_prin1_content.key = "default"
	part1_prin1_content.depth = 1
	part1_prin1_content.lengths = [lengths[count]]
	part1_prin1_content.sectionNames = ["Article"]
	part1_prin1_content.heSectionNames = [u"סעיף"]
	part1_prin1_content.addressTypes = ["Integer"]

	part1_prin1.append(part1_prin1_intro)
	part1_prin1.append(part1_prin1_content)
	part1.append(part1_prin1)
part1.validate()

part2 = SchemaNode()
part2.add_title("Part Two, The Prohibition Against Rechilut", "en", primary=True)
part2.add_title(u"חלק שני: הלכות איסורי רכילות", "he", primary=True)
part2.key = "part2"

lengths = [11, 4, 4, 3, 7, 10, 5, 5, 15]
for count in range(9):
	part2_prin1 = SchemaNode()
	part2_prin1.add_title("Principle "+str(count+1), "en", primary=True)
	part2_prin1.add_title(u"כלל "+numToHeb(count+1), "he", primary=True)
	part2_prin1.key="part2_prin"+str(count)

	part2_prin1_intro = JaggedArrayNode()
	part2_prin1_intro.key = "intro"+str(count+1)+"b"
	part2_prin1_intro.add_title("Opening Comments", "en", primary=True)
	part2_prin1_intro.add_title(u"הערות מקדימות", "he", primary=True)
	part2_prin1_intro.depth = 1
	part2_prin1_intro.sectionNames = ["Paragraph"]
	part2_prin1_intro.addressTypes = ["Integer"]

	part2_prin1_content = JaggedArrayNode()
	part2_prin1_content.default = True
	part2_prin1_content.key = "default"
	part2_prin1_content.depth = 1
	part2_prin1_content.lengths = [lengths[count]]
	part2_prin1_content.sectionNames = ["Article"]
	part2_prin1_content.heSectionNames = [u"סעיף"]
	part2_prin1_content.addressTypes = ["Integer"]

	part2_prin1.append(part2_prin1_intro)
	part2_prin1.append(part2_prin1_content)
	part2.append(part2_prin1)
part2.validate()

illustration = SchemaNode()
illustration.key = "il"
illustration.add_title("Illustrations", "en", primary=True)
illustration.add_title(u"ציורים", "he", primary=True)

for count in range(11):
	illustration1 = JaggedArrayNode()
	illustration1.key = "il"+str(count)
	illustration1.depth = 1
	illustration1.sectionNames = ["Paragraph"]
	illustration1.addressTypes = ["Integer"]
	illustration1.add_title("Illustration "+str(count+1), "en", primary=True)
	illustration1.add_title(u"ציור "+numToHeb(count+1), "he", primary=True)
	illustration.append(illustration1)

teshuva1 = JaggedArrayNode()
teshuva1.key = "t1"
teshuva1.depth = 1
teshuva1.sectionNames = ["Paragraph"]
teshuva1.addressTypes = ["Integer"]
teshuva1.add_title(u"תשובת חות יאיר", "he", primary=True)
teshuva1.add_title("Responsa of the Chavot Yair", "en", primary=True)

teshuva2 = JaggedArrayNode()
teshuva2.key = "t2"
teshuva2.depth = 1
teshuva2.sectionNames = ["Paragraph"]
teshuva2.addressTypes = ["Integer"]
teshuva2.add_title("Responsa of the Maharik", "en", primary=True)
teshuva2.add_title(u"""תשובת מהרי"ק""", "he", primary=True)

teshuva3 = JaggedArrayNode()
teshuva3.key = "t3"
teshuva3.depth = 1
teshuva3.sectionNames = ["Paragraph"]
teshuva3.addressTypes = ["Integer"]
teshuva3.add_title(u"""תשובת מהרי"ק סי' קכ"ט""", "he", primary=True)
teshuva3.add_title("Responsa of the Maharik Siman 129", "en", primary=True)

teshuva4 = JaggedArrayNode()
teshuva4.key = "t4"
teshuva4.depth = 1
teshuva4.sectionNames = ["Paragraph"]
teshuva4.addressTypes = ["Integer"]
teshuva4.add_title("Aliyot d'Rabeinu Yonah, from the Shitah Mekubetzet", "en", primary=True)
teshuva4.add_title(u"עליות רבינו יונה משיטה מקובצת", "he", primary=True)



root.append(intro)
root.append(intro2)
root.append(part1)
root.append(part2)
root.append(illustration)
root.append(teshuva1)
root.append(teshuva2)
root.append(teshuva3)
root.append(teshuva4)


root.validate()


index = {
    "title": "Chofetz Chaim",
    "categories": ["Halakhah"],
    "schema": root.serialize()
}


post_index(index)

