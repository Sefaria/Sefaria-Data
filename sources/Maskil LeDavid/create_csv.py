from sources.functions import *
from linking_utilities.weighted_levenshtein import WeightedLevenshtein
def get_dh(txt, ref):
	just_dh = txt.split("</b>")[0]
	num_words_just_dh = just_dh.count(" ")
	for i, w in enumerate(txt.split()[:num_words_just_dh+2]):
		if "</b>" in w:
			pos = i
			break
	dh_plus = " ".join(txt.split()[:pos+5]).replace("<b>", "").replace("</b>", "")
	just_dh = just_dh.replace("<b>", "")
	return (ref, just_dh, dh_plus)

rashi_refs = {}
maskil_refs = {}
new_csv = []
with open("Maskil LeDavid, Genesis - FINAL - Maskil LeDavid, Genesis - FINAL.csv", 'r') as f:
	for line in csv.reader(f):
		if line[0].startswith("Maskil"):
			ref, comm, found_ref, relevant_text = line
			rashi_ref = ref.replace("Maskil LeDavid, ", "Rashi on ")
			genesis_ref = ":".join(ref.replace("Maskil LeDavid, ", "").split(":")[:-1])
			if genesis_ref not in maskil_refs:
				maskil_refs[genesis_ref] = []
			maskil_refs[genesis_ref].append((ref, comm))
		else:
			new_csv.append(line)


exact_match = 0
more_than_2 = []
not_found = []
weighted = WeightedLevenshtein()
for genesis_ref in maskil_refs:
	these_maskil_refs = maskil_refs[genesis_ref]
	these_rashi_refs = Ref("Rashi on {}".format(genesis_ref)).all_segment_refs()

	rashi_dhs = [get_dh(strip_nekud(ref.text('he').text), ref) for ref in these_rashi_refs]
	for maskil_ref, maskil_comm in these_maskil_refs:
		finds = []
		for rashi_dh_tuple in rashi_dhs:
			rashi_ref, rashi_dh, rashi_dh_plus = rashi_dh_tuple
			rashi_dh = rashi_dh.replace(".", "")
			if maskil_comm.startswith(rashi_dh) or maskil_comm.startswith(rashi_dh.split()[0] + " "):
				finds.append((rashi_dh_tuple, maskil_ref, maskil_comm))

		if len(finds) == 1:
			exact_match += 1
			rashi_found_ref = finds[0][0][0].normal()
		elif len(finds) > 1:
			more_than_2.append(genesis_ref)
			arr = []
			max_score = 0
			rashi_found_ref = ""
			for find in finds:
				rashi_tuple, ref, maskil = find
				rashi_ref, rashi, rashi_plus = rashi_tuple
				maskil = " ".join(maskil.split("וכו׳")[0].split()[:6])
				score = weighted.calculate(rashi_plus, maskil)
				if score > max_score:
					max_score = score
					rashi_found_ref = rashi_ref.normal()
		else:
			rashi_found_ref = ""
			if len(rashi_dhs) == 1:
				rashi_ref, rashi_dh, rashi_dh_plus = rashi_dhs[0]
				rashi_found_ref = rashi_ref.normal()
			else:
				for rashi_dh_tuple in rashi_dhs:
					rashi_ref, rashi_dh, rashi_dh_plus = rashi_dh_tuple
					rashi_dh = rashi_dh.replace(".", "")
					maskil = " ".join(maskil_comm.split("וכו׳")[0].split()[:6])
					score = weighted.calculate(rashi_dh_plus, maskil)
					if score > 80:
						print(score)
						rashi_found_ref = rashi_ref.normal()
			if rashi_found_ref == "":
				not_found.append(genesis_ref)

		if len(rashi_found_ref) > 0:
			new_csv.append([maskil_ref, maskil_comm, rashi_found_ref,
											TextChunk(Ref(rashi_found_ref), lang='he', vtitle='Rashi Chumash, Metsudah Publications, 2009').text])
		else:
			new_csv.append([maskil_ref, maskil_comm, "", ""])

print(len(not_found))
with open("new csv.csv", 'w') as f:
	writer = csv.writer(f)
	for row in new_csv:
		writer.writerow(row)

