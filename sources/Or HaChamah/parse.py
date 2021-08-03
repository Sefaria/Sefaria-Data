from sources.functions import *
def dher(txt):
	return txt[txt.find("<b>")+3:txt.find("</b>")]

files = [open("bereshit noach.txt", 'r'), open("lech lecha vayechi.txt", 'r'), open("shemot.txt", 'r'),
				 open("vayikra.txt", 'r'), open("bamidbar devarim.txt", 'r')]
lines = []
text = {1: {1: []}, 2: {4: []}, 3: {3: []}}
daf = prev_daf = 1
curr_vol = 1
prev_daf_line = ""
for f in files:
	lines = list(f)
	for i, line in enumerate(lines):
		orig_line = line
		line = line.strip()
		if line.startswith("@22"):
			line = line.replace('@22דף\'', '').replace("@22(", "").replace("@22", "").replace("דף", "", 1).strip()
			if line.count(" ") == 1:
				daf, amud = " ".join(line.split()[0:]).split()
				daf = AddressTalmud(0).toNumber("he", daf)
				amud = amud.replace('"', '')
				if not amud.startswith('ע') and len(amud) != 2:
					print(line)
				if "ב" not in amud:
					daf -= 1
			elif line.count(" ") == 0:
				daf = AddressTalmud(0).toNumber("he", line) * 2
			else:
				print(line)
				continue

			if daf < prev_daf - 200:
				curr_vol += 1
			elif daf < prev_daf:
				print(prev_daf_line.strip())
				print("comes before")
				print(orig_line.strip())
				print(f.name)
				print()
			#text[curr_vol][daf] = []
			prev_daf_line = orig_line
		elif line.startswith("@11"):
			if "@33" in line and line.find("@33") == line.rfind("@33"):
				dh, comm = line.split("@33")
				dh = dh.replace("@11", "")
				#text[curr_vol][daf].append("<b>{}</b>{}".format(dh, comm))
			else:
				print(line)
		prev_daf = daf
	#
	# for daf in text:
	# 	results = match_ref_interface("Zohar {}".format(daf), "Or HaChamah {}".format(daf), text[daf], lambda x: x.split(), dher)
