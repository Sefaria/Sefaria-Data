# -*- coding: utf-8 -*-
from sefaria.model import *
from sefaria.tracker import add
import urllib
import urllib2
from urllib2 import URLError, HTTPError
import json 
import pdb
import os
import sys
p = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, p)
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from local_settings import *

sys.path.insert(0, SEFARIA_PROJECT_PATH)

from sefaria.model import *


def post_index(index):
	url = SEFARIA_SERVER+'/api/index/' + index["title"].replace(" ", "_")
	indexJSON = json.dumps(index)
	print indexJSON
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


def appendNodes(root_node, subsections, num):
	count=0
	for sub in subsections:
		count+=1
		if count > num:
			break
		n = JaggedArrayNode()
		n.key = "article"+str(count)
		n.add_title(sub, "he", primary=True)
		n.add_title("Article "+str(count), "en", primary=True)
		n.depth = 1
		n.sectionNames = ["Paragraph"]
		n.addressTypes = ["Integer"]
		root_node.append(n)


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

seifim = ["סעיף א", "סעיף ב", "סעיף ג", "סעיף ד", "סעיף ה", "סעיף ו", "סעיף ז", "סעיף ח", "סעיף ט", "סעיף י", "סעיף יא", "סעיף יב", "סעיף יג", "סעיף יד", "סעיף טו",
"סעיף טז", "סעיף יז"]

part1 = SchemaNode()
part1.add_title("Part One, The Prohibition Against Lashon Hara", "en", primary=True)
part1.add_title(u"חלק ראשון: הלכות איסורי לשון הרע", "he", primary=True)
part1.key = "part1"

part1_prin1 = SchemaNode()
part1_prin1.add_title("Principle One", "en", primary=True)
part1_prin1.add_title(u"כלל א", "he", primary=True)
part1_prin1.key="part1_prin1"

part1_prin1_intro = JaggedArrayNode()
part1_prin1_intro.key = "intro1"
part1_prin1_intro.add_title("Opening Comments", "en", primary=True)
part1_prin1_intro.add_title(u"הערות מקדימות", "he", primary=True)
part1_prin1_intro.depth = 1
part1_prin1_intro.sectionNames = ["Paragraph"]
part1_prin1_intro.addressTypes = ["Integer"]

part1_prin1_content = JaggedArrayNode()
part1_prin1_content.default = True
part1_prin1_content.key = "default"
part1_prin1_content.depth = 1
part1_prin1_content.lengths = [9]
part1_prin1_content.sectionNames = ["Article"]
part1_prin1_content.heSectionNames = [u"סעיף"]
part1_prin1_content.addressTypes = ["Integer"]

part1_prin1.append(part1_prin1_intro)
part1_prin1.append(part1_prin1_content)

part1_prin2 = SchemaNode()
part1_prin2.add_title("Principle Two", "en", primary=True)
part1_prin2.add_title(u"כלל ב", "he", primary=True)
part1_prin2.key="part1_prin2"

part1_prin2_intro = JaggedArrayNode()
part1_prin2_intro.key = "intro2"
part1_prin2_intro.add_title("Opening Comments", "en", primary=True)
part1_prin2_intro.add_title(u"הערות מקדימות", "he", primary=True)
part1_prin2_intro.depth = 1
part1_prin2_intro.sectionNames = ["Paragraph"]
part1_prin2_intro.addressTypes = ["Integer"]

part1_prin2_content = JaggedArrayNode()
part1_prin2_content.default = True
part1_prin2_content.key = "default"
part1_prin2_content.sectionNames = ["Article"]
part1_prin2_content.heSectionNames = [u"סעיף"]
part1_prin2_content.addressTypes = ["Integer"]
part1_prin2_content.depth = 1
part1_prin2_content.lengths = [13]

part1_prin2.append(part1_prin2_intro)
part1_prin2.append(part1_prin2_content)

part1_prin3 = SchemaNode()
part1_prin3.add_title("Principle Three", "en", primary=True)
part1_prin3.add_title(u"כלל ג", "he", primary=True)
part1_prin3.key="part1_prin3"

part1_prin3_intro = JaggedArrayNode()
part1_prin3_intro.key = "intro3"
part1_prin3_intro.add_title("Opening Comments", "en", primary=True)
part1_prin3_intro.add_title(u"הערות מקדימות", "he", primary=True)
part1_prin3_intro.depth = 1
part1_prin3_intro.sectionNames = ["Paragraph"]
part1_prin3_intro.addressTypes = ["Integer"]

part1_prin3_content = JaggedArrayNode()
part1_prin3_content.default = True
part1_prin3_content.key = "default"
part1_prin3_content.depth = 1
part1_prin3_content.lengths = [8]
part1_prin3_content.sectionNames = ["Article"]
part1_prin3_content.heSectionNames = [u"סעיף"]
part1_prin3_content.addressTypes = ["Integer"]

part1_prin3.append(part1_prin3_intro)
part1_prin3.append(part1_prin3_content)

part1_prin4 = SchemaNode()
part1_prin4.add_title("Principle Four", "en", primary=True)
part1_prin4.add_title(u"כלל ד", "he", primary=True)
part1_prin4.key="part1_prin4"

part1_prin4_intro = JaggedArrayNode()
part1_prin4_intro.key = "intro4"
part1_prin4_intro.add_title("Opening Comments", "en", primary=True)
part1_prin4_intro.add_title(u"הערות מקדימות", "he", primary=True)
part1_prin4_intro.depth = 1
part1_prin4_intro.sectionNames = ["Paragraph"]
part1_prin4_intro.addressTypes = ["Integer"]

part1_prin4_content = JaggedArrayNode()
part1_prin4_content.default = True
part1_prin4_content.key = "default"
part1_prin4_content.depth = 1
part1_prin4_content.lengths = [12]
part1_prin4_content.sectionNames = ["Article"]
part1_prin4_content.heSectionNames = [u"סעיף"]
part1_prin4_content.addressTypes = ["Integer"]

part1_prin4.append(part1_prin4_intro)
part1_prin4.append(part1_prin4_content)

part1_prin5 = SchemaNode()
part1_prin5.add_title("Principle Five", "en", primary=True)
part1_prin5.add_title(u"כלל ה", "he", primary=True)
part1_prin5.key="part1_prin5"

part1_prin5_intro = JaggedArrayNode()
part1_prin5_intro.key = "intro5"
part1_prin5_intro.add_title("Opening Comments", "en", primary=True)
part1_prin5_intro.add_title(u"הערות מקדימות", "he", primary=True)
part1_prin5_intro.depth = 1
part1_prin5_intro.sectionNames = ["Paragraph"]
part1_prin5_intro.addressTypes = ["Integer"]

part1_prin5_content = JaggedArrayNode()
part1_prin5_content.default = True
part1_prin5_content.key = "default"
part1_prin5_content.depth = 1
part1_prin5_content.lengths = [8]
part1_prin5_content.sectionNames = ["Article"]
part1_prin5_content.heSectionNames = [u"סעיף"]
part1_prin5_content.addressTypes = ["Integer"]

part1_prin5.append(part1_prin5_intro)
part1_prin5.append(part1_prin5_content)


part1_prin6 = SchemaNode()
part1_prin6.add_title("Principle Six", "en", primary=True)
part1_prin6.add_title(u"כלל ו", "he", primary=True)
part1_prin6.key="part1_prin6"

part1_prin6_intro = JaggedArrayNode()
part1_prin6_intro.key = "intro6"
part1_prin6_intro.add_title("Opening Comments", "en", primary=True)
part1_prin6_intro.add_title(u"הערות מקדימות", "he", primary=True)
part1_prin6_intro.depth = 1
part1_prin6_intro.sectionNames = ["Paragraph"]
part1_prin6_intro.addressTypes = ["Integer"]


part1_prin6_content = SchemaNode()
part1_prin6_content.key = "default"
part1_prin6_content.default = True
part1_prin6_content.depth = 1
part1_prin6_content.lengths = [12]
part1_prin6_content.sectionNames = ["Article"]
part1_prin6_content.heSectionNames = [u"סעיף"]
part1_prin6_content.addressTypes = ["Integer"]

part1_prin6.append(part1_prin6_intro)
part1_prin6.append(part1_prin6_intro)


part1_prin7 = SchemaNode()
part1_prin7.add_title("Principle Seven", "en", primary=True)
part1_prin7.add_title(u"כלל ז", "he", primary=True)
part1_prin7.key="part1_prin7"

part1_prin7_intro = JaggedArrayNode()
part1_prin7_intro.key = "intro7"
part1_prin7_intro.add_title("Opening Comments", "en", primary=True)
part1_prin7_intro.add_title(u"הערות מקדימות", "he", primary=True)
part1_prin7_intro.depth = 1
part1_prin7_intro.sectionNames = ["Paragraph"]
part1_prin7_intro.addressTypes = ["Integer"]


part1_prin7_content = JaggedArrayNode()
part1_prin7_content.key = "default"
part1_prin7_content.default = True
part1_prin7_content.depth = 1
part1_prin7_content.lengths = [14]
part1_prin7_content.sectionNames = ["Article"]
part1_prin7_content.heSectionNames = [u"סעיף"]
part1_prin7_content.addressTypes = ["Integer"]

part1_prin7.append(part1_prin7_intro)
part1_prin7.append(part1_prin7_content)


part1_prin8 = SchemaNode()
part1_prin8.add_title("Principle Eight", "en", primary=True)
part1_prin8.add_title(u"כלל ח", "he", primary=True)
part1_prin8.key="part1_prin8"

part1_prin8_intro = JaggedArrayNode()
part1_prin8_intro.key = "intro8"
part1_prin8_intro.add_title("Opening Comments", "en", primary=True)
part1_prin8_intro.add_title(u"הערות מקדימות", "he", primary=True)
part1_prin8_intro.depth = 1
part1_prin8_intro.sectionNames = ["Paragraph"]
part1_prin8_intro.addressTypes = ["Integer"]


part1_prin8_content = JaggedArrayNode()
part1_prin8_content.default = True
part1_prin8_content.key = "default"
part1_prin8_content.depth = 1
part1_prin8_content.lengths = [14]
part1_prin8_content.sectionNames = ["Article"]
part1_prin8_content.heSectionNames = [u"סעיף"]
part1_prin8_content.addressTypes = ["Integer"]


part1_prin8.append(part1_prin8_intro)
part1_prin8.append(part1_prin8_content)


part1_prin9 = SchemaNode()
part1_prin9.add_title("Principle Nine", "en", primary=True)
part1_prin9.add_title(u"כלל ט", "he", primary=True)
part1_prin9.key="part1_prin9"

part1_prin9_intro = JaggedArrayNode()
part1_prin9_intro.key = "intro9"
part1_prin9_intro.add_title("Opening Comments", "en", primary=True)
part1_prin9_intro.add_title(u"הערות מקדימות", "he", primary=True)
part1_prin9_intro.depth = 1
part1_prin9_intro.sectionNames = ["Paragraph"]
part1_prin9_intro.addressTypes = ["Integer"]

part1_prin9_content = JaggedArrayNode()
part1_prin9_content.default = True
part1_prin9_content.key = "default"
part1_prin9_content.depth = 1
part1_prin9_content.lengths = [6]
part1_prin9_content.sectionNames = ["Article"]
part1_prin9_content.heSectionNames = [u"סעיף"]
part1_prin9_content.addressTypes = ["Integer"]

part1_prin9.append(part1_prin9_intro)
part1_prin9.append(part1_prin9_content)


part1_prin10 = SchemaNode()
part1_prin10.add_title("Principle Ten", "en", primary=True)
part1_prin10.add_title(u"כלל י", "he", primary=True)
part1_prin10.key="part1_prin10"

part1_prin10_intro = JaggedArrayNode()
part1_prin10_intro.key = "intro10"
part1_prin10_intro.add_title("Opening Comments", "en", primary=True)
part1_prin10_intro.add_title(u"הערות מקדימות", "he", primary=True)
part1_prin10_intro.depth = 1
part1_prin10_intro.sectionNames = ["Paragraph"]
part1_prin10_intro.addressTypes = ["Integer"]

part1_prin10_content = JaggedArrayNode()
part1_prin10_content.default = True
part1_prin10_content.key = "default"
part1_prin10_content.depth = 1
part1_prin10_content.lengths = [17]
part1_prin10_content.sectionNames = ["Article"]
part1_prin10_content.heSectionNames = [u"סעיף"]
part1_prin10_content.addressTypes = ["Integer"]

part1_prin10.append(part1_prin10_intro)
part1_prin10.append(part1_prin10_content)


part1.append(part1_prin1)
part1.append(part1_prin2)
part1.append(part1_prin3)
part1.append(part1_prin4)
part1.append(part1_prin5)
part1.append(part1_prin6)
part1.append(part1_prin7)
part1.append(part1_prin8)
part1.append(part1_prin9)
part1.append(part1_prin10)


part2 = SchemaNode()
part2.add_title("Part Two, The Prohibition Against Rechilut", "en", primary=True)
part2.add_title(u"חלק שני: הלכות איסורי רכילות", "he", primary=True)
part2.key = "part2"


part2_prin1 = SchemaNode()
part2_prin1.add_title("Principle One", "en", primary=True)
part2_prin1.add_title(u"כלל א", "he", primary=True)
part2_prin1.key="part2_prin1"

part2_prin1_intro = JaggedArrayNode()
part2_prin1_intro.key = "intro1b"
part2_prin1_intro.add_title("Opening Comments", "en", primary=True)
part2_prin1_intro.add_title(u"הערות מקדימות", "he", primary=True)
part2_prin1_intro.depth = 1
part2_prin1_intro.sectionNames = ["Paragraph"]
part2_prin1_intro.addressTypes = ["Integer"]

part2_prin1_content = JaggedArrayNode()
part2_prin1_content.default = True
part2_prin1_content.key = "default"
part2_prin1_content.depth = 1
part2_prin1_content.lengths = [11]
part2_prin1_content.sectionNames = ["Article"]
part2_prin1_content.heSectionNames = [u"סעיף"]
part2_prin1_content.addressTypes = ["Integer"]

part2_prin1.append(part2_prin1_intro)
part2_prin1.append(part2_prin1_content)

part2_prin2 = SchemaNode()
part2_prin2.add_title("Principle Two", "en", primary=True)
part2_prin2.add_title(u"כלל ב", "he", primary=True)
part2_prin2.key="part2_prin2"

part2_prin2_intro = JaggedArrayNode()
part2_prin2_intro.key = "intro2b"
part2_prin2_intro.add_title("Opening Comments", "en", primary=True)
part2_prin2_intro.add_title(u"הערות מקדימות", "he", primary=True)
part2_prin2_intro.depth = 1
part2_prin2_intro.sectionNames = ["Paragraph"]
part2_prin2_intro.addressTypes = ["Integer"]

part2_prin2_content = JaggedArrayNode()
part2_prin2_content.default = True
part2_prin2_content.key = "default"
part2_prin2_content.depth = 1
part2_prin2_content.lengths = [4]
part2_prin2_content.sectionNames = ["Article"]
part2_prin2_content.heSectionNames = [u"סעיף"]
part2_prin2_content.addressTypes = ["Integer"]


part2_prin2.append(part2_prin2_intro)
part2_prin2.append(part2_prin2_content)

part2_prin3 = SchemaNode()
part2_prin3.add_title("Principle Three", "en", primary=True)
part2_prin3.add_title(u"כלל ג", "he", primary=True)
part2_prin3.key="part2_prin3"

part2_prin3_intro = JaggedArrayNode()
part2_prin3_intro.key = "intro3b"
part2_prin3_intro.add_title("Opening Comments", "en", primary=True)
part2_prin3_intro.add_title(u"הערות מקדימות", "he", primary=True)
part2_prin3_intro.depth = 1
part2_prin3_intro.sectionNames = ["Paragraph"]
part2_prin3_intro.addressTypes = ["Integer"]

part2_prin3_content = JaggedArrayNode()
part2_prin3_content.default = True
part2_prin3_content.key = "default"
part2_prin3_content.depth = 1
part2_prin3_content.lengths = [4]
part2_prin3_content.sectionNames = ["Article"]
part2_prin3_content.heSectionNames = [u"סעיף"]
part2_prin3_content.addressTypes = ["Integer"]

part2_prin3.append(part2_prin3_intro)
part2_prin3.append(part2_prin3_content)

part2_prin4 = SchemaNode()
part2_prin4.add_title("Principle Four", "en", primary=True)
part2_prin4.add_title(u"כלל ד", "he", primary=True)
part2_prin4.key="part2_prin4"

part2_prin4_intro = JaggedArrayNode()
part2_prin4_intro.key = "intro4b"
part2_prin4_intro.add_title("Opening Comments", "en", primary=True)
part2_prin4_intro.add_title(u"הערות מקדימות", "he", primary=True)
part2_prin4_intro.depth = 1
part2_prin4_intro.sectionNames = ["Paragraph"]
part2_prin4_intro.addressTypes = ["Integer"]

part2_prin4_content = JaggedArrayNode()
part2_prin4_content.default = True
part2_prin4_content.key = "default"
part2_prin4_content.depth = 1
part2_prin4_content.lengths = [3]
part2_prin4_content.sectionNames = ["Article"]
part2_prin4_content.heSectionNames = [u"סעיף"]
part2_prin4_content.addressTypes = ["Integer"]


part2_prin4.append(part2_prin4_intro)
part2_prin4.append(part2_prin4_content)


part2_prin5 = SchemaNode()
part2_prin5.add_title("Principle Five", "en", primary=True)
part2_prin5.add_title(u"כלל ה", "he", primary=True)
part2_prin5.key="part2_prin5"

part2_prin5_intro = JaggedArrayNode()
part2_prin5_intro.key = "intro5b"
part2_prin5_intro.add_title("Opening Comments", "en", primary=True)
part2_prin5_intro.add_title(u"הערות מקדימות", "he", primary=True)
part2_prin5_intro.depth = 1
part2_prin5_intro.sectionNames = ["Paragraph"]
part2_prin5_intro.addressTypes = ["Integer"]

part2_prin5_content = JaggedArrayNode()
part2_prin5_content.default = True
part2_prin5_content.key = "default"
part2_prin5_content.depth = 1
part2_prin5_content.lengths = [7]
part2_prin5_content.sectionNames = ["Article"]
part2_prin5_content.heSectionNames = [u"סעיף"]
part2_prin5_content.addressTypes = ["Integer"]

part2_prin5.append(part2_prin5_intro)
part2_prin5.append(part2_prin5_content)


part2_prin6 = SchemaNode()
part2_prin6.add_title("Principle Six", "en", primary=True)
part2_prin6.add_title(u"כלל ו", "he", primary=True)
part2_prin6.key="part2_prin6"

part2_prin6_intro = JaggedArrayNode()
part2_prin6_intro.key = "intro6b"
part2_prin6_intro.add_title("Opening Comments", "en", primary=True)
part2_prin6_intro.add_title(u"הערות מקדימות", "he", primary=True)
part2_prin6_intro.depth = 1
part2_prin6_intro.sectionNames = ["Paragraph"]
part2_prin6_intro.addressTypes = ["Integer"]


part2_prin6_content = JaggedArrayNode()
part2_prin6_content.default = True
part2_prin6_content.key = "default"
part2_prin6_content.depth = 1
part2_prin6_content.lengths = [10]
part2_prin6_content.sectionNames = ["Article"]
part2_prin6_content.heSectionNames = [u"סעיף"]
part2_prin6_content.addressTypes = ["Integer"]


part2_prin6.append(part2_prin6_intro)
part2_prin6.append(part2_prin6_content)



part2_prin7 = SchemaNode()
part2_prin7.add_title("Principle Seven", "en", primary=True)
part2_prin7.add_title(u"כלל ז", "he", primary=True)
part2_prin7.key="part2_prin7"

part2_prin7_intro = JaggedArrayNode()
part2_prin7_intro.key = "intro7b"
part2_prin7_intro.add_title("Opening Comments", "en", primary=True)
part2_prin7_intro.add_title(u"הערות מקדימות", "he", primary=True)
part2_prin7_intro.depth = 1
part2_prin7_intro.sectionNames = ["Paragraph"]
part2_prin7_intro.addressTypes = ["Integer"]

part2_prin7_content = JaggedArrayNode()
part2_prin7_content.default = True
part2_prin7_content.key = "default"
part2_prin7_content.depth = 1
part2_prin7_content.lengths = [5]
part2_prin7_content.sectionNames = ["Article"]
part2_prin7_content.heSectionNames = [u"סעיף"]
part2_prin7_content.addressTypes = ["Integer"]

part2_prin7.append(part2_prin7_intro)
part2_prin7.append(part2_prin7_content)


part2_prin8 = SchemaNode()
part2_prin8.add_title("Principle Eight", "en", primary=True)
part2_prin8.add_title(u"כלל ח", "he", primary=True)
part2_prin8.key="part2_prin8"

part2_prin8_intro = JaggedArrayNode()
part2_prin8_intro.key = "intro8b"
part2_prin8_intro.add_title("Opening Comments", "en", primary=True)
part2_prin8_intro.add_title(u"הערות מקדימות", "he", primary=True)
part2_prin8_intro.depth = 1
part2_prin8_intro.sectionNames = ["Paragraph"]
part2_prin8_intro.addressTypes = ["Integer"]

part2_prin8_content = JaggedArrayNode()
part2_prin8_content.key = "default"
part2_prin8_content.default = True
part2_prin8_content.depth = 1
part2_prin8_content.lengths = [5]
part2_prin8_content.sectionNames = ["Article"]
part2_prin8_content.heSectionNames = [u"סעיף"]
part2_prin8_content.addressTypes = ["Integer"]

part2_prin8.append(part2_prin8_intro)
part2_prin8.append(part2_prin8_content)


part2_prin9 = SchemaNode()
part2_prin9.add_title("Principle Nine", "en", primary=True)
part2_prin9.add_title(u"כלל ט", "he", primary=True)
part2_prin9.key="part2_prin9"

part2_prin9_intro = JaggedArrayNode()
part2_prin9_intro.key = "intro9b"
part2_prin9_intro.add_title("Opening Comments", "en", primary=True)
part2_prin9_intro.add_title(u"הערות מקדימות", "he", primary=True)
part2_prin9_intro.depth = 1
part2_prin9_intro.sectionNames = ["Paragraph"]
part2_prin9_intro.addressTypes = ["Integer"]

part2_prin9_content = JaggedArrayNode()
part2_prin9_content.default = True
part2_prin9_content.key = "default"
part2_prin9_content.depth = 1
part2_prin9_content.lengths = [16]
part2_prin9_content.sectionNames = ["Article"]
part2_prin9_content.heSectionNames = [u"סעיף"]
part2_prin9_content.addressTypes = ["Integer"]

part2_prin9.append(part2_prin9_intro)
part2_prin9.append(part2_prin9_content)

part2.append(part2_prin1)
#part2.append(part2_prin2)
part2.append(part2_prin3)
part2.append(part2_prin4)
part2.append(part2_prin5)
part2.append(part2_prin6)
part2.append(part2_prin7)
part2.append(part2_prin8)
part2.append(part2_prin9)

illustration = SchemaNode()
illustration.key = "il"
illustration.add_title("Illustrations", "en", primary=True)
illustration.add_title(u"ציורים", "he", primary=True)

illustration1 = JaggedArrayNode()
illustration1.key = "il1"
illustration1.depth = 1
illustration1.sectionNames = ["Paragraph"]
illustration1.addressTypes = ["Integer"]
illustration1.add_title("Illustration One", "en", primary=True)
illustration1.add_title(u"ציור א", "he", primary=True)

illustration2 = JaggedArrayNode()
illustration2.key = "il2"
illustration2.depth = 1
illustration2.sectionNames = ["Paragraph"]
illustration2.addressTypes = ["Integer"]
illustration2.add_title("Illustration Two", "en", primary=True)
illustration2.add_title(u"ציור ב", "he", primary=True)

illustration3 = JaggedArrayNode()
illustration3.key = "il3"
illustration3.depth = 1
illustration3.sectionNames = ["Paragraph"]
illustration3.addressTypes = ["Integer"]
illustration3.add_title("Illustration Three", "en", primary=True)
illustration3.add_title(u"ציור ג", "he", primary=True)

illustration4 = JaggedArrayNode()
illustration4.key = "il4"
illustration4.depth = 1
illustration4.sectionNames = ["Paragraph"]
illustration4.addressTypes = ["Integer"]
illustration4.add_title("Illustration Four", "en", primary=True)
illustration4.add_title(u"ציור ד", "he", primary=True)

illustration5 = JaggedArrayNode()
illustration5.key = "il5"
illustration5.depth = 1
illustration5.sectionNames = ["Paragraph"]
illustration5.addressTypes = ["Integer"]
illustration5.add_title("Illustration Five", "en", primary=True)
illustration5.add_title(u"ציור ה", "he", primary=True)

illustration6 = JaggedArrayNode()
illustration6.key = "il6"
illustration6.depth = 1
illustration6.sectionNames = ["Paragraph"]
illustration6.addressTypes = ["Integer"]
illustration6.add_title("Illustration Six", "en", primary=True)
illustration6.add_title(u"ציור ו", "he", primary=True)

illustration7 = JaggedArrayNode()
illustration7.key = "il7"
illustration7.depth = 1
illustration7.sectionNames = ["Paragraph"]
illustration7.addressTypes = ["Integer"]
illustration7.add_title("Illustration Seven", "en", primary=True)
illustration7.add_title(u"ציור ז", "he", primary=True)

illustration8 = JaggedArrayNode()
illustration8.key = "il8"
illustration8.depth = 1
illustration8.sectionNames = ["Paragraph"]
illustration8.addressTypes = ["Integer"]
illustration8.add_title("Illustration Eight", "en", primary=True)
illustration8.add_title(u"ציור ח", "he", primary=True)

illustration9 = JaggedArrayNode()
illustration9.key = "il9"
illustration9.depth = 1
illustration9.sectionNames = ["Paragraph"]
illustration9.addressTypes = ["Integer"]
illustration9.add_title("Illustration Nine", "en", primary=True)
illustration9.add_title(u"ציור ט", "he", primary=True)

illustration10 = JaggedArrayNode()
illustration10.key = "il10"
illustration10.depth = 1
illustration10.sectionNames = ["Paragraph"]
illustration10.addressTypes = ["Integer"]
illustration10.add_title("Illustration Ten", "en", primary=True)
illustration10.add_title(u"ציור י", "he", primary=True)

illustration11 = JaggedArrayNode()
illustration11.key = "il11"
illustration11.depth = 1
illustration11.sectionNames = ["Paragraph"]
illustration11.addressTypes = ["Integer"]
illustration11.add_title("Illustration Eleven", "en", primary=True)
illustration11.add_title(u"ציור יא", "he", primary=True)


illustration.append(illustration1)
illustration.append(illustration2)
illustration.append(illustration3)
illustration.append(illustration4)
illustration.append(illustration5)
illustration.append(illustration6)
illustration.append(illustration7)
illustration.append(illustration8)
illustration.append(illustration9)
illustration.append(illustration10)
illustration.append(illustration11)

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

