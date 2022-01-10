from sources.functions import *
rows = []
comments = []
with open("Commentary on Genesis.csv", 'r') as f:
	for row in csv.reader(f):
		ref, comm = row
		if ref.startswith("Commentary on Genesis, [text]."):
			if comm.startswith("<b>"):
				comments.append(comm)
			else:
				comments[-1] += "\n" + comm
		else:
			rows.append(row)
with open("Commentary on Genesis2.csv", 'w') as f:
	writer = csv.writer(f)
	for row in rows:
		writer.writerow(row)
	for i, comm in enumerate(comments):
		writer.writerow(["Commentary on Genesis {}".format(i+1), comm])