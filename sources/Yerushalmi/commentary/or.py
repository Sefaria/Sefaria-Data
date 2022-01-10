import django
django.setup()
from sefaria.model import *
from sources.functions import add_term, add_category, post_text, post_index

ohr = 'Ohr LaYesharim'
hohr = 'אור לישרים'
jt = ' on Jerusalem Talmud'
hjt = ' על תלמוד ירושלמי'
categories = ["Talmud", "Yerushalmi", "Commentary", "Modern Commentary on Talmud", ohr+jt]
server = 'http://localhost:9000'
server = 'https://shorashim.cauldron.sefaria.org'

def create_index(mas):
    record = SchemaNode()
    he_bt = library.get_index(f'Jerusalem Talmud {mas}').get_title('he')
    record.add_primary_titles(f'{ohr}{jt} {mas}', f'{he_bt} על {hohr}')
    intro = JaggedArrayNode()
    intro.add_primary_titles('Introduction', 'הקדמה')
    intro.addressTypes = ['Integer']
    intro.sectionNames = ['Segment']
    intro.depth = 1
    default = JaggedArrayNode()
    default.default = True
    default.key = 'default'
    default.add_structure(['Chapter', 'Halakhah', 'Segment'])
    default.addressTypes = ['Perek', 'Halakhah', 'Integer']
    record.append(intro)
    record.append(default)
    record.validate()
    index_dict = {'collective_title': ohr,
                  'title': f'{ohr}{jt} {mas}',
                  'categories': categories,
                  'schema': record.serialize(),
                  'dependence': 'Commentary',
                  'base_text_titles': [f'Jerusalem Talmud {mas}'],
                  'base_text_mapping': 'one_to_one'
                  }
    post_index(index_dict, server=server)

add_term(ohr, hohr, server=server)
add_term(ohr+jt, hohr+hjt, server=server)
add_category(ohr+jt, categories, server=server)
mases = ['Taanit', 'Sukkah', 'Shekalim', 'Sanhedrin', 'Rosh Hashanah', 'Peah', 'Moed Katan', 'Megillah', 'Chagigah', 'Berakhot', 'Beitzah']
for mas in mases:
    create_index(mas)
    text_version = {
        'versionTitle': "Machon HaYerushalmi, Rabbi Yehoshua Buch",
        'versionSource': "",
        'language': 'he',
        'text': [[['']]]
    }
    post_text(f'{ohr}{jt} {mas}', text_version, server=server, index_count='on')
