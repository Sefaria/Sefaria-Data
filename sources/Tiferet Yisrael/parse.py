from sources.functions import *
def parse_ftnotes():
	files = ["Footnotes 1.txt", "Footnotes 2.txt"]
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







def parse_text(ftnotes_to_insert):
	files = ["Part 1.txt", "Part 2.txt"]
	ch = 0
	curr_ftnote = 0
	text = {}
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
						curr_ftnote_str = "<sup>{}</sup><i class='footnote'>{}</i>".format(found_ftnote, ftnotes_to_insert[ch][found_ftnote])
						running_txt += txt + curr_ftnote_str
						skip = False
					except:
						print(ch)
						print(found_ftnote)
						skip = True
				if not skip:
					text[ch].append(running_txt)

	print(ch)
	return text
ftnotes_to_insert = parse_ftnotes()
text = parse_text(ftnotes_to_insert)
text = convertDictToArray(text)
for i, ch in enumerate(text[1:]):
	send_text = {
		"versionTitle": "Tiferet Yisrael, with footnotes and annotations by Rabbi Yehoshua D. Hartman, Machon Yerushalyim, 2010",
		"versionSource": "https://www.nli.org.il/he/books/NNL_ALEPH002042478/NLI",
		"language": "he",
		"text": ch
	}
	post_text("Tiferet Yisrael {}".format(i+1), send_text, server="https://arukhtanakh.cauldron.sefaria.org")
send_text = {
	"versionTitle": "Tiferet Yisrael, with footnotes and annotations by Rabbi Yehoshua D. Hartman, Machon Yerushalyim, 2010",
	"versionSource": "https://www.nli.org.il/he/books/NNL_ALEPH002042478/NLI",
	"language": "he",
	"text": text[0]
}
post_text("Tiferet Yisrael, Introduction to Tiferet Yisrael", send_text, server="https://arukhtanakh.cauldron.sefaria.org")
