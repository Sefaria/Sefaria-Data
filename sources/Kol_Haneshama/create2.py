from sources.functions import *
finds = {}
from collections import Counter


column_a = []
column_c = []
with open("legend for hebrew and nikkud - Sheet2.csv", 'r') as f:
	for row in csv.reader(f):
		column_a.append(row[0])
		column_c.append(row[1])

x = Counter()
assert len(column_c) == len(column_a)
for f in os.listdir("./original_shabbat_vehagim/"):
	print(f)
	with open("./original_shabbat_vehagim/"+f, 'r', encoding="ISO-8859-1") as open_f:
		lines = list(open_f)
		for l in lines:
			for col_chr in column_c:
				if col_chr in l and len(col_chr) > 0:
					x[col_chr] += 1

with open("results2.csv", 'w') as f:
	writer = csv.writer(f)
	for chr in x:
		writer.writerow([chr, x[chr]])


