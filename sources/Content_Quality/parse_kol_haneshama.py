from sources.functions import *
finds = {}
from collections import Counter


column_a = []
column_c = []
with open("../Kol_Haneshama/legend for hebrew and nikkud - Sheet2.csv", 'r') as f:
	for row in csv.reader(f):
		column_a.append(row[0])
		column_c.append(row[2])




x = Counter()
assert len(column_c) == len(column_a)
for f in os.listdir("../Kol_Haneshama/original_shabbat_vehagim"):
	print(f)
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

			for k, v in {u'\u05b2': '/13',
						 u'\u05b6': '/14',
						 u'\u05b5': '/15',
						 u'\u05c5': '/16',
						 u'\u05b0': '/17',
						 u'\u05b8': '/18',
						 u'\u05b7': '/19',
						 u'\u05bb': '/20',
						 u'\u05ba': '/21'}.items():
				if v in lines[l]:
					lines[l] = lines[l].replace(v, k)

		with open("../Kol_Haneshama/new/"+f, 'w') as new_f:
			new_f.writelines(lines)


