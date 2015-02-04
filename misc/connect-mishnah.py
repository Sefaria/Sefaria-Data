import urllib2
import re
import json
#def is_there_bavli():
# Get list of mesechtot
mesechtot = [u'Mishnah Berakhot',
u'Mishnah Peah',
u'Mishnah Demai',
u'Mishnah Kilayim',
u'Mishnah Sheviit',
u'Mishnah Terumot',
u'Mishnah Maasrot',
u'Mishnah Maaser Sheni',
u'Mishnah Challah',
u'Mishnah Orlah',
u'Mishnah Bikkurim',
u'Mishnah Shabbat',
u'Mishnah Eruvin',
u'Mishnah Pesachim',
u'Mishnah Shekalim',
u'Mishnah Yoma',
u'Mishnah Sukkah',
u'Mishnah Beitzah',
u'Mishnah Rosh Hashanah',
u'Mishnah Taanit',
u'Mishnah Megillah',
u'Mishnah Moed Katan',
u'Mishnah Chagigah',
u'Mishnah Yevamot',
u'Mishnah Ketubot',
u'Mishnah Nedarim',
u'Mishnah Nazir',
u'Mishnah Sotah',
u'Mishnah Gittin',
u'Mishnah Kiddushin',
u'Mishnah Bava Kamma',
u'Mishnah Bava Metzia',
u'Mishnah Bava Batra',
u'Mishnah Sanhedrin',
u'Mishnah Makkot',
u'Mishnah Shevuot',
u'Mishnah Eduyot',
u'Mishnah Avodah Zarah',
u'Pirkei Avot',
u'Mishnah Horayot',
u'Mishnah Zevachim',
u'Mishnah Menachot',
u'Mishnah Chullin',
u'Mishnah Bekhorot',
u'Mishnah Arakhin',
u'Mishnah Temurah',
u'Mishnah Keritot',
u'Mishnah Meilah',
u'Mishnah Tamid',
u'Mishnah Middot',
u'Mishnah Kinnim',
u'Mishnah Kelim',
u'Mishnah Oholot',
u'Mishnah Negaim',
u'Mishnah Parah',
u'Mishnah Tahorot',
u'Mishnah Mikvaot',
u'Mishnah Niddah',
u'Mishnah Makhshirin',
u'Mishnah Zavim',
u'Mishnah Tevul Yom',
u'Mishnah Yadayim',
u'Mishnah Oktzin']
# For each Mesechet of Mishnah check wether there is a talmud
for mesechet in mesechtot:
     try:
         ref = mesechet[8:]
         ref=re.sub(" ", "_", ref)
         url = 'http://www.sefaria.org/api/index/'+ str(ref)
         response = urllib2.urlopen(url)
         resp = response.read()
         bavli= json.loads(resp)
         print bavli["title"]
         print bavli["lengths"]
         mesechet=re.sub(" ", "_", mesechet)
         url = 'http://www.sefaria.org/api/index/'+ str(mesechet)
         response = urllib2.urlopen(url)
         resp = response.read()
         mishna= json.loads(resp)
         print mishna["title"]
         print "mishna length", mishna["length"]
         (bavli["title"],bavli["length"],mishna["length"])
         #need to take the length from the index of the mishna and the talmud
     except:
         print 'no bavli for '+ref

#def find(title, length, mishna_length):
j=1 #seder chapter index
i=2 #daf index
while i<(length/2)+2: #move thru gemara
	while j<mishna_length+1: #move thru mishna chapters
		ref="Mishna_"+title
		url='http://www.sefaria.org/api/texts/'+ref+ '.' + str(j)
		response = urllib2.urlopen(url)
		resp = response.read()
		a= json.loads(resp)
		tana=a["he"]
		k=0 #mishnayot in chapter index
		while k<len(tana):
			tana[k]=re.sub(r'[,\.]',"",tana[k])
			wd=1 #amud index
			while wd<3:
				if wd==1:
					amud="a"
				else:
					amud="b"
				url='http://www.sefaria.org/api/texts/'+title+"."+str(i)+amud
				response = urllib2.urlopen(url)
				resp = response.read()
				a= json.loads(resp)
				bavli=a["he"]
				l=0
				while l<len(bavli):
					if u"\u05de\u05ea\u05e0\u05d9' " in bavli[l]:
						if bavli[l+1] in tana[k]:
							a=l+1
							while bavli[a] in tana[k]:								
								print tana[k].find(bavli[a])
								a=a+1
								l=a
							
							print "daf "+str(i)+" amud "+ amud+" line "+str(l)
					if bavli[l][0:8]==u'\u05d4\u05d3\u05e8\u05df \u05e2\u05dc\u05da':
						print "end of perek: daf "+str(i)+" amud "+ amud+" line "+str(l) 
						j=j+1
						
					l=l+1
					#k=k+1
				wd=wd+1
			k=k+1
		i=i+1

			

	
import urllib2
import re
import json
title="Niddah"
length=143
mishna_length=10