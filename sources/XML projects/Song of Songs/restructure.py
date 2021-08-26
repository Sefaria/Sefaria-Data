from sources.functions import *
rows = []
curr_perek = 0
curr_pasuk = 0
text = {}
if __name__ == "__main__":
	with open("Commentary on Song of Songs.csv", 'r') as f:
		for row in csv.reader(f):
			print(row)
			ref, comm = row
			if ref.startswith("Commentary on Song of Songs, Text."):
				print(ref)
				match = re.search("^<b>\[(\d+):(\d+)\]", comm)
				if match:
					print(match.group(0))
					poss_perek = int(match.group(1))
					poss_pasuk = int(match.group(2))
					assert poss_perek - curr_perek in [0, 1]
					if poss_perek == curr_perek and poss_pasuk > 1:
						assert 10 > poss_pasuk - curr_pasuk > 0
					curr_perek = poss_perek
					curr_pasuk = poss_pasuk
					if curr_perek not in text:
						text[curr_perek] = {}
					if curr_pasuk not in text[curr_perek]:
						text[curr_perek][curr_pasuk] = []
					text[curr_perek][curr_pasuk].append(comm.replace(match.group(0), "<b>"))
				else:
					text[curr_perek][curr_pasuk].append(comm)
			else:
				rows.append(row)

		with open("Commentary on Song of Songs2.csv", 'w') as new_f:
			writer = csv.writer(new_f)
			for row in rows:
				writer.writerow(row)
			for c in text.keys():
				for v in text[c].keys():
					writer.writerow(["Commentary on Song of Songs {}:{}".format(c, v), "\n".join(text[c][v])])