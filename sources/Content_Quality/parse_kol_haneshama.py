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


# /IT = italics, /BB = bold, /UN = underline; /SC = small caps; /XX means stop whatever's going on but /XX means start when in /SC

x = Counter()
assert len(column_c) == len(column_a)
tags = defaultdict(list)
tags_in_hebrew = []
all_lines = []
for f in sorted(os.listdir("../Kol_Haneshama/original_shabbat_vehagim"), key=lambda x: x.replace("T", ""))[9:]:
	if not f.startswith("T"):
		continue
	with open('../Kol_Haneshama/original_shabbat_vehagim/'+f, 'r', encoding="ISO-8859-1") as open_f:
		lines = list(open_f)
		for l, line in enumerate(lines):
			if line.startswith("/PL") or line.startswith("/PG") or line.startswith("/CD"): 	# title
				lines[l] = ""
				continue
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
						 '\u05bb': ['/20'],
						 '\u05b9': ['/21'],
						 'שׁ': ['/22'],
						 'שּׁ': ['/23'],
						 'שׂ': ['/24'],
						 '\u05bdֽֽ': ['/SI'],
						 "<b>": ["/KB", "/CC", "/CB", "/CE"],
						 "שּׂ": ["/25"],
						 "\u05b3": ["/12"],
						 "'": ["Ú"],
						 "\u0323": ["/±"],
						 "": ["/PR", "/PI", "/CA", "/PH", "/HH", "/HY", "/CR"]}.items(): #"": ["/KA", "/PR"]}.items():

				for item in v:
					if item in lines[l]:
						lines[l] = lines[l].replace(item, k)
			if re.search("([\u0591-\u05EA ]{1,})(/)([\u0591-\u05EA]{1,})", lines[l]):
				lines[l] = lines[l].split("/")
				for i, segment in enumerate(lines[l]):
					lines[l][i] = lines[l][i][0] + "\u05bc" + lines[l][i][1:] if len(lines[l][i]) > 0 else "\u05bc"
				lines[l] = "".join(lines[l])
			if lines[l].startswith("/SC"):
				lines[l] = re.sub("/XX(.*?)/XX", "<small>\g<1></small>", lines[l])
			lines[l] = re.sub("/IT(.*?)/XX", "<i>\g<1></i>", lines[l])
			lines[l] = re.sub("/BB(.*?)/XX", "<b>\g<1></b>", lines[l])
			lines[l] = re.sub("/UN(.*?)/XX", "<u>\g<1></u>", lines[l])
			lines[l] = re.sub("/[BB|IT|UN|SC|XX]{2}", "", lines[l])

			lines[l] = lines[l].replace("/IT", "<i>").replace("/BB", "<b>").replace("/UN", "<u>")
			if len(lines[l].split("<i>")) != len(lines[l].split("</i>")) or len(lines[l].split("<u>")) != len(lines[l].split("</u>")) or len(lines[l].split("<b>")) != len(lines[l].split("</b>")):
				lines[l] = lines[l].strip() + "</b>"
				print(lines[l])

		for line in lines:
			for tag in re.findall("/[A-Z0-9]{2}", line):
				tags[tag].append((f, line))
			cases = re.findall("([\u0591-\u05EA]+(/[A-Z0-9]{2})[\u0591-\u05EA ]+)", line)+re.findall("([\u0591-\u05EA ]+(/[A-Z0-9]{2})[\u0591-\u05EA]+)", line)
			for c in cases:
				tags_in_hebrew.append(c[1])
		with open("../Kol_Haneshama/new/"+f+".txt", 'w') as new_f:
			lines = "\n".join(lines).replace("ò", "'").splitlines()
			new_f.writelines(lines)
		all_lines += [l for l in lines if len(l) > 0 and l != "/HN"]


headers = [title for title in all_lines if title.isupper()]
for h in headers:
	if h.startswith("/KA"):
		print(h[3:])