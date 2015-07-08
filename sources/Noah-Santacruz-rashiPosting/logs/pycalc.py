import os, string

def init(file):
	c = 0
	with open(file, "r") as f:
    		for line in f:
			if (not line):
				continue
			if (line.translate(None, string.whitespace).startswith("text")):
				c+=1
	return c

def doMas(mas):
	dir = mas+"/"
	all = 0
	bad = 0
	for file in os.listdir("./"+dir):
		if (".txt~" in file):
			continue
		if ("All" in file):
			all += init(dir+file)
		elif ("Ambiguous" in file):
			bad += init(dir+file)
		elif ("NotFound" in file):
			bad += init(dir+file)
		else:
			print "we have a problem with %s" %(dir+file)
	good=all-bad
	if (all > 1):
		print '%s: Good: %s  Bad %s' %(mas, good, bad)
	return bad
	#if all <=0, then we know the logs aren't complete so skip

badtot=0
for file in os.listdir("./"):
	if os.path.isdir(file):
		badtot += doMas(file)
print "total number of comments that need to be fixed is %s" %(badtot)
