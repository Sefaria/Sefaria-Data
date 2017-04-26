class Tractate:
    pass

def mord_post_term():
    term_obj = {
        "name": "Mordechai",
        "scheme": "commentary_works",
        "titles": [
            {
                "lang": "en",
                "text": "Mordechai",
                "primary": True
            },
            {
                "lang": "he",
                "text": u'מרדכי',
                "primary": True
            }
        ]
    }
    post_term(term_obj)

def mord_post_index(tractate_object):   
    record = JaggedArrayNode()
    record.add_title('Mordechai on '+tractate_object.record_name_en, 'en', primary=True)
    record.add_title(u'מרדכי על'+' '+tractate_object.record_name_he, 'he', primary=True)
    record.key = 'Mordechai on '+tractate_object.record_name_en
    record.depth = 3
    record.addressTypes = ["Integer", "Integer"]
    record.sectionNames = ["Chapter", "Paragraph"]
    record.validate()

    index = {
        "title":'Mordechai on '+tractate_object.record_name_en,
        "base_text_titles": [
          tractate_object.record_name_en
        ],
        "dependence": "Commentary",
        "categories":["Talmud","Bavli","Commentary","Mordechai"],
        "schema": record.serialize()
    }
    post_index(index,weak_network=True)


with open("מרדכי בבא בתרא - ערוך לתג - סופי.txt") as myfile:
    lines = list(map(labmda(x): x.decode('utf8', 'replace'), myfile.readlines()))
for line in lines:
    print line

posting_term=False
posting_index=False
posting_text=False
linking=False

tractate = Tractate()
tractate.record_name_en = "Bava Batra"
tractate.record_name_he = u"בבא בתרא"

if posting_term:
    mord_post_term()
if posting_index:
    mord_post_index(tractate)
    

    