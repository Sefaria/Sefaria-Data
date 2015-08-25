# -*- coding: utf-8 -*-
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
	url = SEFARIA_SERVER+'api/v2/raw/index/'+index["title"].replace(" ", "_")
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


def appendNodes(root_node, heb_subsections, en_subsections):
	for count, sub in enumerate(heb_subsections):
		n = JaggedArrayNode()
		n.key = en_subsections[count]+str(count)
		n.add_title(sub, "he", primary=True)
		n.add_title(en_subsections[count], "en", primary=True)
		n.depth = 1
		n.sectionNames = ["Paragraph"]
		n.addressTypes = ["Integer"]
		root_node.append(n)


		
root = SchemaNode()
root.add_title("Derech Hashem", "en", primary=True)
root.add_title("The Way of God", "en", primary=False)
root.add_title(u"דרך ה'", "he", primary=True)
root.key = 'root'

intro=JaggedArrayNode()
intro.depth = 1
intro.sectionNames = ["Paragraph"]
intro.addressTypes = ["Integer"]
intro.add_title("Introduction", "en", primary=True)
intro.add_title(u"הקדמה", "he", primary=True)
intro.key='intro'
intro.validate()

part1 = SchemaNode()
part1.key = 'part1'
part1.add_title(u"חלק א", "he", primary=True)
part1.add_title("Part One", "en", primary=True)


heb_subsections = [u"בבורא יתברך שמו", u"בתכלית הבריאה", u"במין האנושי", u"במצב של האדם בעולם הזה והדרכים שלפניו",
u"בחלקי הבריאה ומצביהם"]

en_subsections = ["On the Creator", "On the Purpose of Creation", "On Mankind", "On Human Responsibility", "On the Spiritual Realm"]
appendNodes(part1, heb_subsections, en_subsections)

part2 = SchemaNode()
part2.key = 'part2'
part2.add_title("Part Two", "en", primary=True)
part2.add_title(u"חלק ב", "he", primary=True)

heb_subsections = [u"בעניין השגחתו יתברך בכלל", u"במקרי המין האנושי בעולם הזה", u"בהשגחה האישית", u"בעניין ישראל ואומות העולם",
u"באופן ההשגחה", u"בסדר ההשגחה", u"השפעת הכוכבים", u"בהבחנות פרטיות בהשגחה"]

en_subsections = ["On Divine Providence in General", "On Mankind in This World", "On Personal Providence", 
"On Israel and the Nations", "On How Providence Works", "On the System of Providence", "On the Influence of the Stars",
"On Specific Modes of Providence"]

appendNodes(part2, heb_subsections, en_subsections)



part3 = SchemaNode()
part3.key = 'part3'
part3.add_title("Part Three", "en", primary=True)
part3.add_title(u"חלק ג", "he", primary=True)

heb_subsections = [u"בעניין הנפש ופעולותיה", u"בעניין הפעולה בשמות ובכישוף", u"בעניין רוח הקודש והנבואה",
u"במקרי הנבואה", u"בהבדל שבין נבואת כל הנביאים למשה"]
en_subsections = ["On the Soul and Its Activities", "On Divine Names and Witchcraft", "On Divine Inspiration and Prophecy",
"On the Prophetic Experience", "On Moshe's Unique Status"]

appendNodes(part3, heb_subsections, en_subsections)


part4 = SchemaNode()
part4.key = 'part4'
part4.add_title("Part Four", "en", primary=True)
part4.add_title(u"חלק ד", "he", primary=True)

heb_subsections = [u"בחלקי העבודה", u"בתלמוד תורה", u"באהבה ויראה", u"""בק"ש וברכותיה""", u"בעניין התפילה", u"סדר היום והתפילות",
u"בעבודה הזמניית", u"במצוות הזמנים", u"בברכות"]
en_subsections = ["On Divine Service", "On Torah Study", "On Love and Fear of God", "On the Sh'ma and Its Blessings",
"On Prayer", "On the Daily Order of Prayer", "On Divine Service and the Calendar", "On Seasonal Commandments", "On Blessings"]

appendNodes(part4, heb_subsections, en_subsections)

part1.validate()
part2.validate()
part3.validate()
part4.validate()


root.append(intro)
root.append(part1)
root.append(part2)
root.append(part3)
root.append(part4)



root.validate()


index = {
    "title": u"Derech Hashem",
    "categories": ["Philosophy"],
    "schema": root.serialize()
}


post_index(index)
