import django
django.setup()
import urllib
import json
from sources import functions
from sefaria.model.schema import *
from sefaria.model import *

server = 'http://draft.sandbox.sefaria.org'
#server = 'http://localhost:8000'
record = SchemaNode()
record.add_primary_titles('Halakhot Gedolot', 'הלכות גדולות')


node = JaggedArrayNode()
node.add_primary_titles('Introduction', 'הקדמה')
node.add_structure(['Pararaph'])
record.append(node)
node = JaggedArrayNode()
node.key = 'default'
node.default = True
node.add_structure(['Siman', 'Pararaph'])
record.append(node)
record.validate()

alts = ["Introduction / הקדמה", "Hilkhot Berakhot / הלכות ברכות", "Hilkhot Kiddush veHavdalah / הלכות קידוש והבדלה", "Hilkhot Peah / הלכות פאה", "Hilkhot Challah / הלכות חלה", "Hilkhot Kilayim / הלכות כלאים", "Hilkhot Orlah / הלכות ערלה", "Hilkhot Shabbat / הלכות שבת", "Hilkhot Milah / הלכות מילה", "Hilkhot Chanukah / חלכות חנוכה", "Hilkhot Eruvin / הלכות עירובין", "Hilkhot Pesach / הלכות פסח", "Hilkhot Atzeret / הלכות עצרת", "Hilkhot Yom haKippurim / הלכות יום הכפורים", "Hilkhot Sukkah / הלכות סוכה", "Hilkhot Lulav / הלכות לולב", "Hilkhot Yom Tov / הלכות יום טוב", "Hilkhot Rosh haShanah / הלכות ראש השנה", "Hilkhot Tisha beAv veTaaniyot / הלכות תשעה באב ותעניות", "Hilkhot Megillah / הלכות מגילה", "Hilkhot Chol haMoed / הלכות מועד", "Hilkhot Avel / הלכות אבל", "Hilkhot Tumah / הלכות טומאה", "Hilkhot Kohanim / הלכות כהנים", "Hilkhot Tzorchei Tzibbur / הלכות צרכי צבור", "Hilkhot Tefillin / הלכות תפלין", "Hilkhot Mezuzah / הלכות מזוזה", "Hilkhot Tzitzit / הלכות ציצית", "Hilkhot Yevamot / הלכות יבמות", "Hilkhot Arayot / הלכות עריות", "Tosefta Yevamot / תוספתא דיבמות", "Hilkhot Yibbum veChalitza / הלכות יבום וחליצה", "Hilkhot Miun / הלכות מיאון", "Sidurah deChalitzah / סדורא דחליצה", "Get Chalitzh / גט חליצה", "Hilkhot Avadim / הלכות עבדים", "Hilkhot Ketubot / הלכות כתובות", "Hilkhot Nedarim / הלכות נדרים", "Hilkhot Nazir / הלכות נזיר", "Hilkhot Gittin / הלכות גיטין", "Hilkhot Kiddushin / הלכות קידושין", "Hilkhot Niddah / הלכות נדה", "Hilkhot Yoledet / הלכות יולדת", "Hilkhot Bava Kamma / הלכות בבא קמא", "Hilkhot Bava Metzia / הלכות בבא מציעא", "Hilkhot Ribit / הלכות רבית", "Hilkhot Bava Batra / הלכות בבא בתרא", "Hilkhot Nidui / הלכות נידוי", "Hilkhot Nachalot / הלכות נחלות", "Hilkhot Halva'ah / הלכות הלוואה", "Hilkhot haDayanim / הלכות הדיינים", "Hilkhot Edut / הלכות עדות", "Hilkhot Shevuah / הלכות שבועה", "Halakhot Ketzuvot diBnei Ma'arva / הלכות קצובות דבני מערבא", "Hilkhot Avodah Zarah / הלכות עבודה זרה", "Hilkhot Yein Nesekh / הלכות יין נסך", "Hilkhot Kibbud Av vaEm / הלכות כבוד אב ואם", "Hilkhot Malkot / הלכות מלקות", "Hilkhot Horaot / הלכות הוראות", "Hilkhot Zevachim / הלכות זבחים", "Hilkhot Shechitah / הלכות שחיטת חולין", "Hilkhot Terefot / הלכות טריפות", "Hilkhot Dagim / הלכות דגים", "Hilkhot Beitzim / הלכות ביצים", "Hilkhot Chelev / הלכות חלב", "Hilkhot Dam / הלכות דם", "Hilkhot Oto veEt Beno / הלכות אותו ואת בנו", "Hilkhot Gid Hanashe / הלכות גיד הנשה", "Hilkhot Ever Min Hachai / הלכות אבר מן החי", "Hilkhot Kisui Hadam / הלכות כסוי הדם", "Hilkhot Keritot / הלכות כריתות", "Hilkhot Menachot / הלכות מנחות", "Hilkhot Meilah / הלכות מעילה", "Hilkhot Bekhorot / הלכות בכורות", "Hilkhot Temurah / הלכות תמורה", "Hilkhot Soferim / הלכות סופרים", "Hilkhot Hesped / הלכות הספד"]
nodes = []
for n, title in enumerate(alts):
    titles = title.split(' / ')
    node = ArrayMapNode()
    node.depth = 0
    node.wholeRef = "Halakhot Gedolot{}".format(', Introduction' if n == 0 else ' ' + str(n))
    node.includeSections = False
    node.add_primary_titles(*titles)
    nodes.append(node.serialize())

index_dict = {
    "title": "Halakhot Gedolot",
    "categories": ["Halakhah"],
    "schema": record.serialize(),
    'default_struct': "Topic",
    "alt_structs": {'Topic': {'nodes': nodes}}
}
functions.post_index(index_dict, server)

with open('bahag.txt', encoding = 'utf-8') as file:
    data = file.readlines()
version = {
    'versionTitle': 'Halakhot Gedolot, Warsaw 1874',
    'versionSource': 'http://primo.nli.org.il/primo-explore/fulldisplay?vid=NLI&docid=NNL_ALEPH990020573270205171',
    'language': 'he'
}

text = []
part = []
n = 0

for line in data:
    for word in ['@66', '@77', '\n', '\ufeff']:
        line = line.replace(word, '')
    if line == '':
        continue
    if '@88' in line:
        intros = True
        continue
    if '@99' in line:
        if intros:
            version['text'] = part
            functions.post_text('Halakhot Gedolot, Introduction', version, server=server)
        else:
            text.append(part)
        part = []
        intros = False
        continue
    if '@22' in line:
        line = '<b>' + line[3:] + '</b>'
    if '@11' in line:
        if '@11(' in line or '@11 (' in line:
            line = line.replace('@11 ', '').replace('@11', '')
        else:
            line = line.replace('@11 ', '<b>').replace('@11', '<b>').replace(' ', '</b> ', 1)
    breaks = [r'(\.) (\([^\)]*?\) ' + t for t in ['תני)', 'תניא)', 'תנו רבנן)', 'ת"ר)']] + [r'(:) (\(פסק\))']
    for br in breaks:
        line = re.sub(br, r'\1@\2', line)
    part += line.split('@')
text.append(part)

version['text'] = text
functions.post_text('Halakhot Gedolot', version, server=server)
