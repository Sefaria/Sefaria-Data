# -*- coding: utf-8 -*-
import json
import os
import sys
import pprint
import pdb
import urllib
import urllib2
from urllib2 import URLError, HTTPError
p = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, p)
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from local_settings import *

sys.path.insert(0, SEFARIA_PROJECT_PATH)

from sefaria.model import *

def post_index(index):
	url = SEFARIA_SERVER + '/api/v2/raw/index/Tikkunei_Zohar'
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

title = "Tikkunei Zohar"
tikkunim_eng = ["First Tikkun", "Second Tikkun", "Third Tikkun", "Third Tikkun K’Gavna Da", "Fourth Tikkun",
	"Fifth Tikkun", "Sixth Tikkun", "Seventh Tikkun", "Eighth Tikkun", "Ninth Tikkun", "Tenth Tikkun", "Eleventh Tikkun",
	"Twelth Tikkun", "Thirteenth Tikkun", "Fourteenth Tikkun", "Fifteenth Tikkun", "Sixteenth Tikkun", "Seventeenth Tikkun",
	"Eighteenth Tikkun", "Nineteenth Tikkun", "Twentieth Tikkun", "Twenty-First Tikkun", "Twenty-Second Tikkun", "Twenty-Third Tikkun",
	"Twenty-Fourth Tikkun", "Twenty-Fifth Tikkun", "Twenty-Sixth Tikkun", "Twenty-Eighth Tikkun",
	"Twenty-Ninth Tikkun", "Thirtieth Tikkun", "Thirty-First Tikkun", "Thirty-Second Tikkun", "Thirty-Third Tikkun", "Thirty-Fourth Tikkun",
	"Thirty-Fifth Tikkun", "Thirty-Sixth Tikkun", "Thirty-Seventh Tikkun", "Thirty-Eighth Tikkun", "Thirty-Ninth Tikkun",
	"Fourtieth Tikkun", "Fourty-First Tikkun", "Fourty-Second Tikkun", "Fourty-Third Tikkun", "Fourty-Fourth Tikkun",
	"Fourty-Fifth Tikkun", "Fourty-Sixth Tikkun", "Fourty-Seventh Tikkun", "Fourty-Eighth Tikkun", "Fourty-Ninth Tikkun",
	"Fiftieth Tikkun", "Fifty-First Tikkun", "Fifty-Second Tikkun", "Fifty-Third Tikkun", "Fifty-Fourth Tikkun", "Fifty-Fifth Tikkun",
	"Fifty-Sixth Tikkun", "Fifty-Seventh Tikkun", "Fifty-Eighth Tikkun", "Fifty-Ninth Tikkun", "Sixtieth Tikkun", "Sixty-First Tikkun",
	"Sixty-Second Tikkun", "Sixty-Third Tikkun", "Sixty-Fourth Tikkun", "Sixty-Fifth Tikkun", "Sixty-Sixth Tikkun", "Sixty-Seventh Tikkun",
	"Sixty-Eighth Tikkun", "Sixty-Ninth Tikkun", "Seventieth Tikkun"]
		
tikkunim_heb = ["תקונא קדמאה", "[ודא תקונא תניינא]", "[תקונא תליתאה] תקונא תניינא", "ודא תקונא תליתאה כגוונא דא", "תקונא רביעאה", "תקונא חמישאה",
"תקונא שתיתאה", "תקונא שביעאה", "תקונא תמינאה", "תקונא תשיעאה", "תקונא עשיראה", "תקונא חד סר", "תקונא תריסר",
"תקונא תליסר", "תקונא ארביסר", "תקונא חמיסר", "תקונא שיתסר", "תקונא שיבסר", "תקונא תמני סרי", "תקונא תשסרי", "תקונא עשרין",
"תקונא חד ועשרין", "תקונא עשרין ותרין", "תקונא עשרין ותלת", "תקונא עשרין וארבע", "תקונא עשרין וחמשא", "תקונא עשרין ושית", "תקונא עשרין ותמניא",
"תקונא עשרין ותשע", "תקונא תלתין", "תקונא תלתין וחד", "תקונא תלתין ותרין", "תקונא תלתין ותלת", "תקונא תלתין וארבע", "תקונא תלתין וחמשא",
"תקונא תלתין ושתא", "תקונא שבע ותלתין", "תקונא תמניא ותלתין", "תקונא תשע ותלתין", "תקונא ארבעין", "תקונא חד וארבעין", "תקונא ארבעין ותרין",
"תקונא ארבעין ותלת", "תקונא ארבעין וארבע", "תקונא ארבעין וחמשא", "תקונא שית וארבעין", "תקונא שבע וארבעין", "תקונא תמניא וארבעין",
"תקונא תשע וארבעין", "תקונא חמשין", "תקונא חד וחמשין", "תקונא תרין וחמשין", "תקונא חמשין ותלת", "תקונא חמשין וארבע",
"תקונא חמשין וחמש", "תקונא חמשין ושתא", "תקונא שבע וחמשין", "תקונא תמניא וחמשין", "תקונא תשעה וחמשין", "תקונא שתין",
"תקונא חד ושתין", "תקונא שתין ותרין", "תקונא שתין ותלת", "תקונא שתין וארבע", "תקונא שתין וחמש", "תקונא שתין ושתא", "תקונא שתין ושבע",
"תקונא תמניא ושתין", "תקונא שתין ותשעה", "תקונא שבעין"]

add_tikkunim_heb = ["תקונא תניינא", "תקונא תליתאה", "תקונא רביעאה", "תקונא חמישאה", "תקונא שתיתאה", "תקונא שביעאה", "תקונא תמינאה", 
"תקונא תשיעאה", "תקונא עשיראה", "תקונא אחת עשרה"]
add_tikkunim_eng = ["Second Tikkun", "Third Tikkun", "Fourth Tikkun", "Fifth Tikkun", "Sixth Tikkun", "Seventh Tikkun",
"Eighth Tikkun", "Ninth Tikkun", "Tenth Tikkun", "Eleventh Tikkun"]

structs = {}
structs = { "nodes" : [] }
f = open("ranges", 'r')

intro_start = Ref("Tikkunei Zohar "+f.readline())
intro_end = Ref("Tikkunei Zohar "+f.readline())
whole_ref = intro_start.to(intro_end).normal()
intro_node = ArrayMapNode()
intro_node.add_title(u"הקדמת תקוני הזהר", "he", primary=True)
intro_node.add_title("Introduction to Tikkunei HaZohar", "en", primary=True)
intro_node.key = "intro"
intro_node.includeSections = True
intro_node.depth = 0
intro_node.addressTypes = []
intro_node.sectionNames = []
intro_node.wholeRef = whole_ref
intro_node.refs = []
intro_node.validate()
structs["nodes"].append(intro_node.serialize())
		
intro2_start = Ref("Tikkunei Zohar "+f.readline())
intro2_end = Ref("Tikkunei Zohar "+f.readline())
whole_ref = intro2_start.to(intro2_end).normal()
intro2_node = ArrayMapNode()
intro2_node.add_title(u"הקדמה אחרת לתקוני הזהר", "he", primary=True)
intro2_node.add_title("Second Introduction to Tikkunei HaZohar", "en", primary=True)
intro2_node.key = "intro"
intro2_node.includeSections = True
intro2_node.depth = 0
intro2_node.addressTypes = []
intro2_node.sectionNames = []
intro2_node.wholeRef = whole_ref
intro2_node.refs = []
intro2_node.validate()
structs["nodes"].append(intro2_node.serialize())


start_tikkun = {}
end_tikkun = {}
refs = []

max = len(tikkunim_heb)-1
for count, word in enumerate(tikkunim_heb):
	start_tikkun[count] = Ref("Tikkunei Zohar "+f.readline())
	end_tikkun[count] = Ref("Tikkunei Zohar " + f.readline())
	refs.append(start_tikkun[count].to(end_tikkun[count]).normal())
whole_ref = start_tikkun[0].to(end_tikkun[max]).normal()
tikkunim_node = ArrayMapNode()
tikkunim_node.add_title(u"תיקונים", "he", primary=True)
tikkunim_node.add_title("Tikkunim", "en", primary=True)
tikkunim_node.key = "tikkunim"
tikkunim_node.includeSections = True
tikkunim_node.addressTypes = ["Integer"]
tikkunim_node.sectionNames = ["Tikkun"]
tikkunim_node.depth = 1
tikkunim_node.wholeRef = whole_ref
tikkunim_node.refs = refs
tikkunim_node.validate()
structs["nodes"].append(tikkunim_node.serialize())

		
start_tikkun_add = {}
end_tikkun_add = {}
refs = []

max = len(add_tikkunim_heb)-1
for count, word in enumerate(add_tikkunim_heb):
	start_tikkun_add[count] = Ref("Tikkunei Zohar "+f.readline())
	end_tikkun_add[count] = Ref("Tikkunei Zohar " + f.readline())
	refs.append(start_tikkun_add[count].to(end_tikkun_add[count]).normal())
whole_ref = start_tikkun_add[0].to(end_tikkun_add[max]).normal()

tikkunim2_node = ArrayMapNode()
tikkunim2_node.add_title(u"תיקונים נוספים", "he", primary=True)
tikkunim2_node.add_title("Additional Tikkunim", "en", primary=True)
tikkunim2_node.key = "tikkunim"
tikkunim2_node.includeSections = True
tikkunim2_node.addressTypes = ["Integer"]
tikkunim2_node.sectionNames = ["Additional Tikkun"]
tikkunim2_node.depth = 1
tikkunim2_node.wholeRef = whole_ref
tikkunim2_node.refs = refs
tikkunim2_node.validate()
structs["nodes"].append(tikkunim2_node.serialize())


f.close()

root = JaggedArrayNode()
root.add_title("Tikkunei Zohar", "en", primary=True)
root.add_title(u"תקוני הזהר", "he", primary=True)
root.key = "tikkunei_zohar"
root.depth = 2
root.sectionNames = ["Daf", "Paragraph"]
root.addressTypes = ["Talmud", "Integer"]

root.validate()

index = {
	"title": "Tikkunei Zohar",
	"titleVariants": ["Tikkunei haZohar"],
	"sectionNames": ["Daf", "Paragraph"],
	"categories": ["Kabbalah"],
	"addressTypes": ["Talmud", "Integer"],
	"alt_structs": {"Tikkunim": structs},
	"default_struct": "Tikkunim",
	"schema": root.serialize()
}


post_index(index)
