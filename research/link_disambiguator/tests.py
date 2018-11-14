import codecs
import json
import pytest
import django
django.setup()
from sefaria.model import *
from main import *
# {'quote': Ref('Yevamot 91a'), 'main': Ref('Maharam on Yevamot 88b:1')}
# {'quote': Ref('Yevamot 91a'), 'main': Ref('Maharam on Yevamot 88b:1')}
# {'quote': Ref('Zevachim 9b'), 'main': Ref('Commentary on Sefer Hamitzvot of Rasag, Positive Commandments 136:3')}
# {'quote': Ref('Nedarim 46a'), 'main': Ref('Rashba on Bava Kamma 108b:9')}
# {'quote': Ref('Ketubot 35b:4'), 'main': Ref('Gur Aryeh on Devarim 23:4:1')}
# {'quote': Ref('Bava Metzia 23a:15'), 'main': Ref('Chiddushei Ramban on Bava Metzia 21a:1')}

def get_input_output():
    input_output = []
    with codecs.open("test_good_links.json", "rb", encoding="utf8") as fin:
        jin = json.load(fin)
        for item in jin:
            main = Ref(item[0])
            quote = Ref(item[1])
            input_output += [{
                "in": {
                    "main": main,
                    "quote": quote.section_ref()
                },
                "out": {
                    "main": main,
                    "quote": quote
                }
            }]
    with codecs.open("test_bad_links.json", "rb", encoding="utf8") as fin:
        jin = json.load(fin)
        for item in jin:
            main = Ref(item[0])
            quote = Ref(item[1])
            input_output += [{
                "in": {
                    "main": main,
                    "quote": quote
                },
                "out": {
                    "main": main
                }
            }]
    return input_output


@pytest.mark.parametrize('test_items', get_input_output())
def test_link_disambiguator(test_items):

    ld = Link_Disambiguator()
    good, bad = disambiguate_one(ld, test_items["in"]["main"], test_items["in"]["main"].text('he'), test_items["in"]["quote"], test_items["in"]["quote"].text('he'))
    print test_items["in"]
    if "quote" not in test_items["out"]:
        # output should be bad
        assert good == []
        assert bad == [] or bad[0][0] == test_items["out"]["main"].normal()
    else:
        # output is good
        assert good[0][1] == test_items["out"]["quote"].normal()
        assert bad == []



# Makkot 10b:3 --> 4
# Yevamot 91a:13 --> 12