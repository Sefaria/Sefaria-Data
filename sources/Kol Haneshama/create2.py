from sources.functions import *
finds = {}
other = set()#['xf2', 'x90', 'x98', 'x80', 'x99', 'x84', 'x85', 'x95', 'x9a', 'x86', 'x8a', 'x83', 'x8e', 'x92', 'x8f', 'x87', 'x8c', 'x88', 'x02', 'x91', 'x94', 'x89', 'x81', 'x93', 'x8b', 'x96', 'xb1', 'x8d', 'x01', 'x82', 'x97']
#
# with open("tags2.csv", 'r') as f:
# 	for row in csv.reader(f):
# 		tag, comm = row
# 		for f in re.findall(r"\\x.{2}", comm):
# 			other.add(f)
# print(other)
for f in os.listdir("./original_shabbat_vehagim/"):
	with open("./original_shabbat_vehagim/"+f, 'r', encoding='mac-roman') as open_f:
		prev_line = next_line = ""
		lines = list(open_f)
		if f.startswith("."):
			continue
		for i, line in enumerate(lines):
			line = str(line)

			for ex in re.findall("\/[A-Z0-9]{1,2}", str(line)) + re.findall("|".join(other), str(line)):
				if ex in finds:
					if len(finds[ex]) < 10:
						next_line = str(lines[i + 1]) if i + 1 < len(lines) else ""
						finds[ex].append((prev_line+"\n"+str(line)+"\n"+next_line).replace("b'", "").replace("\r\n", ""))
				else:
					finds[ex] = []
			prev_line = str(line)
		with open("Mac_"+f+".txt", 'w') as f:
			f.writelines(lines)



with open("tags2.csv", 'w') as f:
	writer = csv.writer(f)
	for k, v in finds.items():
		for i, item in enumerate(v):
			item = item.replace("\r\n", "").replace("\r", "")
			writer.writerow([k + " " + str(i + 1), item])

