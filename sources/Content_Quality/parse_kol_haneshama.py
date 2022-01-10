from sources.functions import *
finds = {}
from collections import Counter
from memory_profiler import profile


column_a = []
column_c = []
with open("../Kol_Haneshama/legend for hebrew and nikkud - Sheet2.csv", 'r') as f:
	for row in csv.reader(f):
		column_a.append(row[0])
		column_c.append(row[1])




x = Counter()
assert len(column_c) == len(column_a)
tags = []
tags_in_hebrew = []
for f in os.listdir("../Kol_Haneshama/original_shabbat_vehagim"):
	with open('../Kol_Haneshama/original_shabbat_vehagim/'+f, 'r', encoding="ISO-8859-1") as open_f:
		lines = list(open_f)
		for l, line in enumerate(lines):
			for col_chr, col_chr_a in zip(column_c, column_a):
				if len(col_chr) == 0:
					continue
				line_as_nums = [str(ord(c)) for c in line]
				if col_chr in line_as_nums:
					x[col_chr] += 1
					lines[l] = lines[l].replace(chr(int(col_chr)), col_chr_a)

			for k, v in {u'\u05b1': ['/11'],
						u'\u05b2': ['/13'],
						 u'\u05b6': ['/14'],
						 u'\u05b5': ['/15'],
						 u'\u05b4': ['/16'],
						 u'\u05b0': ['/17'],
						 u'\u05b8': ['/18', '/10'],
						 u'\u05b7': ['/19'],
						 u'\u05bb': ['/20'],
						 u'\u05b9': ['/21'],
						 u'שׁ': ['/22'],
						 u'שּׁ': ['/23'],
						 u'שׂ': ['/24']}.items():
				for item in v:
					if item in lines[l]:
						lines[l] = lines[l].replace(item, k)
			lines[l] = re.sub("([\u0591-\u05EA]{1,})(/)([\u0591-\u05EA]{1,})", "\g<1>"+u"\u05bc"+"\g<3>", lines[l])
		for line in lines:
			tags += re.findall("/[A-Z0-9]{2}", line)
			cases = re.findall("([\u0591-\u05EA ]+(/[A-Z0-9]{2})[\u0591-\u05EA ]+)", line)
			for c in cases:
				if c[1] not in tags_in_hebrew:
					tags_in_hebrew.append(c[1])
					print(f)
					print(line)
		with open("../Kol_Haneshama/new/"+f+".txt", 'w') as new_f:
			new_f.writelines(lines)


print(set(tags))
print(set(tags_in_hebrew))