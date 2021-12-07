from sources.functions import *
def parse_ftnotes():
	files = ["Netiv/footnotes.txt"]
	lines = ""
	for f in files:
		with open(f, 'r') as open_f:
			for line_n, line in enumerate(open_f):
				lines += line
	ftnotes_by_ch = {}
	ftnotes_by_ch_str = re.split("\(1\)", lines)[1:]
	for ch, ftnotes in enumerate(ftnotes_by_ch_str):
		ftnotes_by_ch[ch+1] = {}
		for ftnote_n, ftnote in enumerate(re.split("\(\d+\)", "(1)"+ftnotes)):
			if ftnote_n > 0:
				ftnote = ftnote.strip()
				ftnotes_by_ch[ch+1][ftnote_n] = ftnote
	return ftnotes_by_ch

def parse_text(ftnotes_to_insert, title="Netivot Olam, Netiv Hatshuva"):
	files = ["Netiv/netiv hateshuva.txt"]
	ch = 0
	text = {}
	links = []
	for f in files:
		with open(f, 'r') as open_f:
			for line_n, line in enumerate(open_f):
				found_ftnotes = re.findall("\d+", line)
				txt_wout_ftnotes = re.split("\d+", line)
				running_txt = ""
				for found_ftnote, txt in zip(found_ftnotes, txt_wout_ftnotes):
					found_ftnote = int(found_ftnote)
					if found_ftnote == 1:
						ch += 1
						text[ch] = []
					try:
						#found_ftnote corresponds to ftnotes_to_insert[ch][found_ftnote]
						verse = len(text[ch]) + 1
						links.append({"refs": ["Notes by Rabbi Yehoshua Hartman on {} {}:{}".format(title, ch, found_ftnote),
																	 "{} {}:{}".format(title, ch, verse)],
													"inline_reference": {"data-commentator": "Notes by Rabbi Yehoshua Hartman",
																							 "data-order": int(found_ftnote)},
													"generated_by": "ftnotes_netiv", "auto": True, "type": "Commentary"})
						curr_ftnote_str = "<i data-commentator='Notes by Rabbi Yehoshua Hartman' data-order='{}'></i>".format(found_ftnote)
						running_txt += txt.strip() + curr_ftnote_str + " "
						skip = False
					except:
						print(ch)
						print(found_ftnote)
						skip = True
				assert len(found_ftnotes) + 1 == len(txt_wout_ftnotes)
				running_txt += txt_wout_ftnotes[-1]
				running_txt = running_txt.replace(" ,", ",")
				if not skip:
					running_txt = running_txt.replace("</i> .", "</i>.")
					text[ch].append(running_txt)


	print(ch)
	return text, links

ftnotes_to_insert = parse_ftnotes()
text, links = parse_text(ftnotes_to_insert)
text = convertDictToArray(text)
for i in ftnotes_to_insert.keys():
	ftnotes_to_insert[i] = convertDictToArray(ftnotes_to_insert[i])
ftnotes_to_insert = convertDictToArray(ftnotes_to_insert)
send_text = {
	"versionSource": "https://www.nli.org.il/he/books/NNL_ALEPH001742939/NLI",
	"language": "he",
	"versionTitle": "Netivot Olam, Netiv Hatshuva, with footnotes and annotations by Rabbi Yehoshua D. Hartman, Machon Yerushalyim, 1997",
	"text": text
}
post_text("Netivot Olam, Netiv Hatshuva", send_text, server="http://localhost:8000")

send_text["text"] = ftnotes_to_insert
post_text("Notes by Rabbi Yehoshua Hartman on Netivot Olam, Netiv Hatshuva", send_text, server="http://localhost:8000")

json.dump(links, open("links_netivot.json", 'w'))
