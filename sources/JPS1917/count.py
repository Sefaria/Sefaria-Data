import json
import os

f = open('counts.json', 'r')
chapters = f.read()
f.close()

chapters = json.loads(chapters)

files = os.listdir("./json")
total_wrong = 0
total_right = 0
for fname in files:
	if fname in (".DS_Store"):
		continue
	f = open("./json/%s" % fname, 'r')
	text = f.read()
	f.close()
	name = fname[:-4].title()
	text = json.loads(text)
	
	wrong = 0
	right = 0
	for i, c in enumerate(text["text"]):
		try:
			have = len(c)
			should = chapters[name][i]
			if have != should:
				wrong += 1
				print "%s chapter %d should have %d verses, seeing %d" % (name, i+1, should, have)
			else:
				right += 1
		except IndexError:
			print "*** %s should have %d chapters, seeing %d" % (name, len(chapters[name]), len(text["text"]))
			break

	total_wrong += wrong
	total_right += right
	print "* %s: %d wrong, %d right\n" % (name, wrong, right)

print "***\nTOTAL: %d wrong, %d right" % (total_wrong, total_right)