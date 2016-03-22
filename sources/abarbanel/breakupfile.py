# -*- coding: utf-8 -*-


f=open("abarbanel.txt", 'r')
g=open('genesis.txt', 'w')
e=open('exodus.txt', 'w')
l=open('leviticus.txt', 'w')
n=open('numbers.txt', 'w')
d=open('deuteronomy.txt', 'w')

text=""
current_book = "Genesis"
for line in f:
	if line.find("@00")>=0:
		if line.find("שמות")>=0:
			if current_book=="Genesis":
				g.write(text)
				text=""
			current_book = "Exodus"
		elif line.find("ויקרא")>=0:
			e.write(text)
			text=""
			current_book = "Leviticus"
		elif line.find("במדבר")>=0:
			l.write(text)
			text=""
			current_book = "Numbers"
		elif line.find("דברים")>=0:
			n.write(text)
			text=""
			current_book = "Deuteronomy"
	text+=line
d.write(text)

f.close()
g.close()
e.close()
l.close()
n.close()
d.close()