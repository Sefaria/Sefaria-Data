from sources.functions import *
with open("German Mishnah/mischnaiothdiese04samm.csv", 'r') as f:
    actual_ch = 0
    text = {}
    for row in csv.reader(f):
        actual_ch += 1
        chs = re.findall("<b>\d+\.</b> ", row[1])
        assert int(chs[-1].replace("<b>", "").replace("</b>", "").replace(".", "")) == len(chs)
        mishnayot = re.split("<b>\d+\.</b> ", row[1])[1:]
        text[actual_ch] = mishnayot
text = convertDictToArray(text)
send_text = {"language": "en", "versionTitle": "German Mishnah", "versionSource": "https://www.sefaria.org", "text": text}
post_text("Mishnah Makkot", send_text, server="https://ste.cauldron.sefaria.org")