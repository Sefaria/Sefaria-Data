from sources.functions import *
import time

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

def parse_text(ftnotes_to_insert, title="Tiferet Yisrael"):
	files = ["Part 1.txt", "Part 2.txt"]
	ch = 0
	curr_ftnote = 0
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
						links.append({"refs": ["Notes by Rabbi Yehoshua Hartman on {} {}:{}".format(title, ch-1, found_ftnote),
																	 "{} {}:{}".format(title, ch-1, verse)],
													"inline_reference": {"data-commentator": "Notes by Rabbi Yehoshua Hartman",
																							 "data-label": found_ftnote},
													"generated_by": "ftnotes_tiferet", "auto": True, "type": "Commentary"})
						if ch == 1:
							links[-1]["refs"] = ["Notes by Rabbi Yehoshua Hartman on {}, Introduction {}".format(title, found_ftnote),
																	 "{}, Introduction to {} {}".format(title, title, verse)]
						curr_ftnote_str = "<i data-commentator='Notes by Rabbi Yehoshua Hartman' data-label='{}'></i>".format(found_ftnote)
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


footnotes = SchemaNode()
footnotes.add_primary_titles("Notes by Rabbi Yehoshua Hartman on Tiferet Yisrael", "הערות ומקורות על תפארת ישראל")
footnotes.key = "Notes by Rabbi Yehoshua Hartman on Tiferet Yisrael"
intro = create_intro()
footnotes.append(intro)
default = JaggedArrayNode()
default.default = True
default.key = "default"
default.add_structure(["Chapter", "Paragraph"])
footnotes.append(default)
footnotes.validate()
indx = {
	"title": footnotes.key,
	"schema": footnotes.serialize(),
	"categories": ["Jewish Thought", "Acharonim", "Maharal"],
	"dependence": "Commentary",
	"base_text_titles": ["Tiferet Yisrael"],
	"collective_title": "Notes by Rabbi Yehoshua Hartman"
}
#post_index(indx, server="https://ste.cauldron.sefaria.org")
ftnotes_to_insert = parse_ftnotes()
text, links = parse_text(ftnotes_to_insert)
text = convertDictToArray(text)

for i in ftnotes_to_insert.keys():
	ftnotes_to_insert[i] = convertDictToArray(ftnotes_to_insert[i])
ftnotes_to_insert = convertDictToArray(ftnotes_to_insert)
ftnotes_send_text = {
	"language": "he",
	"text": ftnotes_to_insert[0],
	"versionTitle": "Tiferet Yisrael, with footnotes and annotations by Rabbi Yehoshua D. Hartman, Machon Yerushalyim, 2010",
	"versionSource": "https://www.nli.org.il/he/books/NNL_ALEPH002042478/NLI"
}
#post_text("Notes by Rabbi Yehoshua Hartman on Tiferet Yisrael, Introduction", ftnotes_send_text, server="https://ste.cauldron.sefaria.org")
for i, ch in enumerate(text[1:]):
	send_text = {
		"versionTitle": "Tiferet Yisrael, with footnotes and annotations by Rabbi Yehoshua D. Hartman, Machon Yerushalyim, 2010",
		"versionSource": "https://www.nli.org.il/he/books/NNL_ALEPH002042478/NLI",
		"language": "he",
		"text": ch
	}
	ftnotes_send_text["text"] = ftnotes_to_insert[i+1]
	#post_text("Tiferet Yisrael {}".format(i+1), send_text, server="https://ste.cauldron.sefaria.org")
	time.sleep(2)
	#post_text("Notes by Rabbi Yehoshua Hartman on Tiferet Yisrael {}".format(i+1), ftnotes_send_text, server="https://ste.cauldron.sefaria.org")
	time.sleep(2)
send_text = {
	"versionTitle": "Tiferet Yisrael, with footnotes and annotations by Rabbi Yehoshua D. Hartman, Machon Yerushalyim, 2010",
	"versionSource": "https://www.nli.org.il/he/books/NNL_ALEPH002042478/NLI",
	"language": "he",
	"text": text[0]
}
print(len(links))

#post_text("Tiferet Yisrael, Introduction to Tiferet Yisrael", send_text, server="https://ste.cauldron.sefaria.org")
post_link_in_steps(links, step=500, server="https://ste.cauldron.sefaria.org")
