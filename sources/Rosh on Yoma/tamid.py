import django
django.setup()
from sefaria.model import *
from data_utilities.dibur_hamatchil_matcher import *
from sources.functions import *
import re
def dher(str):
    if "." in str:
        return str.split(".", 1)[0]
    else:
        return ""

if __name__ == "__main__":
    daf = 0
    text = {}
    masechet = "Nedarim"
    with open("Perush HaRosh on Nedarim.txt") as f:
        lines = list(f)
        for i, line in enumerate(lines):
            line = line.replace("\r\n", "")
            if not line:
                continue
            line = line.decode('utf-8')
            if len(line.split()) is 1:
                new_daf = getGematria(line)*2
                if not ":" in line:
                    new_daf -= 1
                    assert "." in line
                assert new_daf > daf
                daf = new_daf
                text[daf] = []
            elif "." in line:
                dh, comment = line.split(".", 1)
                text[daf].append(line)
            else:
                text[daf].append(line)



    links = []
    for daf, comments in text.items():
        print daf
        base = TextChunk(Ref("{} {}".format(masechet, AddressTalmud.toStr('en', daf))), lang='he')
        results = match_ref(base, comments, base_tokenizer=lambda x: x.split(), dh_extract_method=dher)
        for match_n, match in enumerate(results["matches"]):
            if match:
                rosh = "Commentary of the Rosh on {} {}:{}".format(masechet, AddressTalmud.toStr("en", daf), match_n+1)
                link = {"refs": [match.normal(), rosh], "generated_by": "Rosh_on_{}".format(masechet), "auto": True, "type": "Commentary"}
                links.append(link)

    post_link(links, server=SEFARIA_SERVER)

    send_text = {
        "language": "he",
        "versionTitle": "Vilna Edition",
        "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957",
        "text": convertDictToArray(text)
    }
    post_text("Commentary of the Rosh on {}".format(masechet), send_text, server=SEFARIA_SERVER)