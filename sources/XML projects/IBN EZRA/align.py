from sources.functions import *
import time
text = {}
for f in os.listdir("."):
    if f.endswith("csv"):
        title = f.replace(".csv", "")
        text[title] = {}
        with open(f) as open_f:
            for row in csv.reader(open_f):
                ch = int(row[0].split(".")[1])
                if ch not in text[title]:
                    text[title][ch] = {}
                    text[title][ch][1] = []
                    pasuk = 1
                pasuk_re = re.search("^\[?(\d+)\. ([A-Z ]{1,}\.?)\]?", row[1])
                if pasuk_re:
                    pasuk_and_text = pasuk_re.group(0)
                    just_text = pasuk_re.group(2)
                    pasuk = int(pasuk_re.group(1))
                    row[1] = row[1].replace(pasuk_and_text, just_text)
                    if pasuk not in text[title][ch]:
                        text[title][ch][pasuk] = []
                is_dh = row[1].split(".")[0].isupper()
                if is_dh:
                    text[title][ch][pasuk].append(row[1])
                elif len(text[title][ch][pasuk]) > 0:
                    text[title][ch][pasuk][-1] += " "+row[1]
                else:
                    text[title][ch][pasuk] = [row[1]]


vsource = "https://www.nli.org.il/he/books/NNL_ALEPH001102376/NLI"
vtitle = "Ibn Ezra's commentary on the Pentateuch, tran. and annot. by H. Norman Strickman and Arthur M. Silver. Menorah Pub., 1988-2004"
ends = {"Genesis": 50, "Exodus": 40, "Deuteronomy": 34, "Numbers": 36, "Leviticus": 27}
for title in text:
    for ch in text[title]:
        text[title][ch] = convertDictToArray(text[title][ch])
    base = title.replace("Ibn Ezra on ", "")
    this_ending = ends[base]
    text[title] = convertDictToArray(text[title])
    text[title] = text[title][:this_ending]
    send_text = {
        "text": text[title],
        "language": "en",
        "versionTitle": vtitle,
        "versionSource": vsource
    }
    time.sleep(30)
    post_text(title, send_text)
