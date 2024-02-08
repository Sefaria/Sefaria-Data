import django
django.setup()
from sefaria.model import *
from sefaria.helper.schema import attach_branch, change_node_title, remove_branch, convert_simple_index_to_complex
from sefaria.helper.text import modify_many_texts_and_make_report
import re

def create_intro():
    intro = JaggedArrayNode()
    intro.add_structure(["Paragraph"])
    intro.add_shared_term("Introduction")
    intro.key = "Introduction"
    intro.validate()
    return intro

#intro for Avodat HaKodesh (Gabbai)
convert_simple_index_to_complex(Ref('Avodat HaKodesh (Gabbai)').index)
parent = Ref('Avodat HaKodesh (Gabbai)').index_node
attach_branch(create_intro(), parent)

#fix hebrew node name in Orot
node = Ref('Orot, Lights of Israel, Nationhood of Israel').index_node
change_node_title(node, 'לומיות ישראל', 'he', 'לאומיות ישראל')

#fix node names in likeuti halakhot
node = Ref('Likutei Halakhot, Choshen Mishpat, Laws of a Deathly Ill Person').index_node
change_node_title(node, 'הלכות מתנה ומתנת שכיב מרע', 'he', 'הלכות מתנה')
change_node_title(node, 'Laws of a Deathly Ill Person', 'en', 'Temp')
node = Ref('Likutei Halakhot, Choshen Mishpat, Laws of Gifting ').index_node
change_node_title(node, 'הלכות מתנה', 'he', 'הלכות מתנת שכיב מרע')
change_node_title(node, 'Laws of Gifting', 'en', 'Laws of a Deathly Ill Person')
node = Ref('Likutei Halakhot, Choshen Mishpat, Temp').index_node
change_node_title(node, 'Temp', 'en', 'Laws of Gifting')

#change name of node (when another node has the same name
index = library.get_index('Likutei Halakhot')
index.nodes.children[4].children[-14].title_group.titles[0]['text'] = 'Laws of Deposit and Four Guards'
index.save()

# change names for Collected Responsa in Wartime node
#change name of node (when another node has the same name
index = library.get_index('Collected Responsa in Wartime')
index.nodes.children[31].title_group.titles[0]['text'] = 'Position of Tallith in Military Burial'
index.nodes.children[31].title_group.titles[1]['text'] = 'מיקום הטלית בקבורה צבאית'
index.save()
node = Ref('Collected Responsa in Wartime, Talleithim For the Dead').index_node
change_node_title(node, 'Talleithim For the Dead', 'en', 'Fringes on Talleithim For the Dead')
change_node_title(node, 'טליתות למתים', 'he', 'ציציות על טליתות למתים')

#change node names in siddur sefard
for child in Ref('Siddur Sefard').index_node.children:
    for node in child.children:
        he_name = node.get_primary_title('he')
        if 'תפילת שמונה עשרה' in he_name:
            new_name = he_name.replace('תפילת שמונה עשרה', 'תפילת עמידה')
            change_node_title(node, he_name, 'he', new_name)

# change node names on siddur ashkenaz
node = Ref('Siddur Ashkenaz, Weekday, Shacharit, Amidah, Keduasha').index_node
change_node_title(node, 'Keduasha', 'en', 'Kedushah')
node = Ref('Siddur Ashkenaz, Weekday, Shacharit, Torah Reading, Reading from Sefer, Birkat Hatorah').index_node
change_node_title(node, 'Birkat Hatorah', 'en', 'Birkat HaTorah')
node = Ref('Siddur Ashkenaz, Weekday, Shacharit, Torah Reading, Reading from Sefer, Birkat Hagomel').index_node
change_node_title(node, 'Birkat Hagomel', 'en', 'Birkat HaGomel')
node = Ref('Siddur Ashkenaz, Shabbat, Shacharit, Torah Reading, Reading from Sefer, Birkat Haotrah').index_node
change_node_title(node, 'Birkat Haotrah', 'en', 'Birkat HaTorah')
node = Ref('Siddur Ashkenaz, Shabbat, Shacharit, Torah Reading, Reading from Sefer, Birkat Hagomel').index_node
change_node_title(node, 'Birkat Hagomel', 'en', 'Birkat HaGomel')

#delete mizmor letoda
node = Ref('Siddur Ashkenaz, Shabbat, Shacharit, Pesukei Dezimra, Mizmor Letoda').index_node
remove_branch(node)

#change katak to katav
change = lambda x: (re.sub(r'\bכתכ\b', 'כתב', x), len(re.findall(r'\bכתכ\b', x)))
r = modify_many_texts_and_make_report(change)
with open('katak.csv', 'wb') as fp:
    fp.write(r)

#change onkelom
change = lambda x: (re.sub('(או?נקלו)ם', r'\1ס', x), len(re.findall('(או?נקלו)ם', x)))
r = modify_many_texts_and_make_report(change)
with open('onkelom.csv', 'wb') as fp:
    fp.write(r)

# change g-d and l-rd
change = lambda x: (x.replace('G-d', 'G‑d').replace('L-rd', 'L‑rd'), len(re.findall('G-d|L-rd', x)))
r = modify_many_texts_and_make_report(change)
with open('names.csv', 'wb') as fp:
    fp.write(r)

# double links on alshich
links = LinkSet({'generated_by': 'Alshich'})
refs = [tuple(l.refs) for l in links]
refs_del = set()
for link in links:
    if refs.count(link.refs) > 1 and tuple(link.refs) not in refs_del:
        refs_del.add(link.refs)
        link.delete()
