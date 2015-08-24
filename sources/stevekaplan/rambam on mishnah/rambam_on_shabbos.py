import pdb

#WHENEVER THERE'S NO PARENTHESIS, THE REG EXP IS NOT WORKING!!!!!!


open('shabbos.txt', 'r')   #same as bava_metzia.txt,
							#bava_kamma.txt same except daf not inside parentheses so use daf = re.compile('@22.*?')
							#becorot.txt completely different: daf not inside parentheses 
										#and @22 is start of DH, @33 or @44 is end of DH ('@44.*?')
										#and @11 is start of comment
						X	#berkahot_intro.txt replace @11 with <b> and @33 with </b>
							#berakhot.txt has daf inside parentheses, but @11 is start of comment
										#@22 is start of DH, @44 is end of DH ('@44\(.*?\)')
							#gittin.txt has daf inside parenthesis, @33 start of comment, @11 start of DH, @22 end of DH
										#BUT @33 is not a new line but immediately follows ('@22\(.*?\)'), so split on this
						X   #horayot_intro.txt
							#horayot.txt does not have daf inside parenthesis, @11 starts a comment,
										#@22 starts a DH and @44 end of DH ('@44\(.*?\)')
						X	#zevachim is confusing. can't find perek rishon
							
							#chullin.txt has daf not in parenthesis. @11 starts DH and @22 ends DH, @33 starts a comment but
										#like gittin.txt, @33 is not a new line but follows @22 so need to split
							#yevamot.txt has daf inside parenthesis, @11 starts DH @22 ends it, and on a NEW LINE,
										#@33 starts rambam's comment
							#kritot.txt does not have daf  in parenthesis, @11 starts @22 ends DH, but on same line @33 starts comment
										#so need to split on '@33'
						
							#ketubot.txt is same as kritot.  does not have daf in parenthesis, @11 starts @22 ends, same line @33 starts comment
							#megilah.txt is complicated: daf in parenthesis @11, @22, and @33 can do different things.  
										#@11 always starts DH, and @22 usually ends it, and sometimes the comment follow @22 on same line	
										#sometimes the comment is on its own line starting with @33, can deal with this by splitting on
										#daf, if there's stuff after, it's a comment, also a comment is a line starting with @33
							#moed_katan.txt is simpler. daf in parenthesis. @11 starts @22 ends @33 starts comment, all one same line
							#makkot.txt is same as moed_katan except that daf is NOT in parenthesis
							#menachot.txt is exactly the same as makkot.txt
							#meilah.txt daf not in parenthesis, but it is simple as @11 starts, @22 ends, and @33 marks a new line
							#niddah.txt is same as meilah.txt	
							#nazir.txt is same as niddah but has daf in parenthesis
							#sotah.txt has daf not in parenthesis, @33 marks new line, @11 starts @22 ends
						X	#sanhedrin.txt has daf in parenthesis, @11 starts @22 ends, @33 marks new line, HAS WEIRD ENDING
							#pesachim.txt has daf in ( ), @11 s @22 e, @33 marks new line
							#kiddushin.txt has daf in parenthesis, @11 starts @22 ends, @33 marks new line
							#rosh_hashanah.txt has daf in ( ), @11 s @22 e, but @33 is on same line
							#shavuot.txt does not have daf in (  ), but @11 s @22 e and @33 marks new line
							#temurah.txt does not have daf in ( ), @11 s @22 e, but @33 is on same line
							#tamid.txt does not have daf in ( ), @11 s @22 e and @33 marks new line			
f.readline() #just says rambam on shabbos
perek_num = 0
dh_list = []
curr_dh_count = 0 
curr_perek = ""
curr_dh = ""
actual_text = {}
comm = {}
for line in f:
	line = line.replace("\n", "")
	line = line.replace(":", "")
	if line.find("@00") > 0:
		perek_num+=1
		curr_perek = line.replace("@00", "")
		actual_text[curr_perek] = ""
	elif line.find("@11") > 0:
		curr_dh_count += 1
		temp = line.replace("@11", "")
		daf = re.compile('@22\(.*?\)')
		match = re.search(daf, temp)
		if match:
			temp = temp.replace(match.group(0), "")
		dh_list[curr_perek].append(temp)
		actual_text[curr_perek] += "<b>"+temp+"</b>."
		curr_dh = temp	
	elif line.find("@33") > 0:
		line = line.replace("@33", "")
		for i in range(curr_dh_count):
			comm[curr_perek].append(line)
		actual_text[curr_perek] += line + "\n"
		curr_dh_count = 0
f.close()