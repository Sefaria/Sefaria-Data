# -*- coding: utf-8 -*-

import urllib2
import urllib
import json
from datetime import datetime
from fuzzywuzzy import fuzz

firstDaf = "2a"
baseline = "Rashi"
f = open('accuracytesterlog.txt','a+')

def matchesList(comm1, comm2):
	global f
	for c2 in comm2:
		if (matchesStr(comm1, c2)):
			ll = "match on "+comm1[0:15]+" and "+c2[0:15]
			#print ll
			f.write(ll.encode('utf-8')+"\n")
			return True
	return False

def matchesStr(comm1, comm2):
	return (fuzz.partial_ratio(comm1, comm2) > 80)

def main(masechet, comentator, baseline):
	global f
	f.write('Starting to check %s against %s at %s\n' %(comentator, baseline, str(datetime.now().strftime('%Y-%m-%d %H:%M'))))
	good = 0
	bad = 0
	next = comentator+" on "+masechet+" "+firstDaf+":1"
	url = "http://dev.sefaria.org/api/texts/"+next.replace(" ", "_")
	while (next != None):
		reqdev = urllib2.Request(url)
		reqdev.add_header("Host", "dev.sefaria.org")
		reqdev.add_header("Accept", "text/html,text/json")
		respdev = urllib2.urlopen(reqdev)
		testRashiJSON = json.loads(respdev.read())
		if ((testRashiJSON["he"]) == []):
			#this shouldn't happen
			print "you shouldn't be here - try rebuilding the counts doc"
			print next
			print url
		else:
			dafline = next.split(masechet+' ',1)[1]
			#line = next.split(":",1)[1]
			url = "http://www.sefaria.org/api/texts/"+baseline+"_on_"+masechet+"."+dafline
			reqtest = urllib2.Request(url)
			reqtest.add_header("Host", "www.sefaria.org")
			reqtest.add_header("Accept", "text/html,text/json")
			resptest = urllib2.urlopen(reqtest)
			goodRashiJSON = json.loads(resptest.read())
			for testcomm in testRashiJSON["he"]:
				if (goodRashiJSON["he"] == []):
					ll = dafline+": not (empty)"
					#print ll
					f.write(ll+"\n")
					bad = bad +1
				elif (matchesList(testcomm, goodRashiJSON["he"])):
					#print dafline+": matches"
					#f.write(str(line)+": matches\n")
					good = good + 1
				else:
					ll = dafline+": not (bad match)"
					print ll
					f.write(ll+'\n')
					#f.write("  location %s test: %s\n" %(dafline, testcomm.encode('utf-8')))
					bad = bad +1
		next = testRashiJSON["next"]
		if (next != None):	
			#print next	
			url = "http://dev.sefaria.org/api/texts/"+next.replace(" ", "_")

	accy = 100.0*good/(good+bad+0.0)
	print "Good: "+str(good)+" bad: "+str(bad)
	print str(accy)

	
	f.write("Good: "+str(good)+"bad: "+str(bad)+"\n"+str(accy))
	final = open('results.txt','a+')
	final.write("results for "+comentator+" accy: "+str(accy)+"\n")

main("Berakhot", 'SMK', 'Rashi')

