from sources.functions import *
fms = {"Foreword": "בראש מילין", "Preface": "פתח דבר", "Acknowledgements": "תודות", "Introduction": "הקדמה",
       "Women and Interpretation of the Torah": "נשים ופרשנות התורה", "Women in Ancient Israel; An Overview": "נשים בישראל בעת העתיקה; סקירה",
       "Women and Post Biblical Commentary": """נשים ופרשנות חז"ל""", "Women and Contemporary Revelation": "נשים וגילויים בני זמננו",
       "The Poetry of Torah and the Torah of Poetry": "שירת התורה ותורת השירה"}
nodes = """Parashah Introductions
Post Biblical Interpretations
Contemporary Reflection
Another View""".splitlines()
he_nodes = """הקדמות לפרשות
פרשנות חז"ל
התבוננות עכשווית
פרספקטיבה נוספת""".splitlines()
root = SchemaNode()
root.key = "The Torah; A Women's Commentary"
root.add_primary_titles(root.key, "פירוש התורה: פרספקטיבה נשית")
for en, he in fms.items():
    child = JaggedArrayNode()
    child.key = en
    child.add_primary_titles(en, he)
    child.add_structure(["Paragraph"])
    child.validate()
    root.append(child)

for n, node in enumerate(nodes):
    child = SchemaNode()
    child.key = node
    child.add_primary_titles(child.key, he_nodes[n])
    child.toc_zoom = 1
    parshiot = []
    for book in ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]:
        parshiot += [Term().load({"name": x["sharedTitle"]}) for x in library.get_index(book).alt_structs["Parasha"]["nodes"]]
    parshiot_nodes = []
    for parsha in parshiot:
        parsha_node = JaggedArrayNode()
        parsha_node.key = parsha.name
        parsha_node.add_primary_titles(parsha.get_primary_title('en'), parsha.get_primary_title('he'))
        parsha_node.add_structure(["Paragraph"])
        parsha_node.depth = 1
        parsha_node.validate()
        child.append(parsha_node)
    child.validate()
    root.append(child)

for book in ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]:
    book_node = JaggedArrayNode()
    book_node.key = book
    book_node.add_primary_titles(book, library.get_index(book).get_title('he'))
    book_node.add_structure(["Chapter", "Verse", "Paragraph"])
    book_node.depth = 3
    book_node.toc_zoom = 2
    book_node.validate()
    root.append(book_node)

root.validate()
Index({"title": root.key, "schema": root.serialize(), "categories": ["Tanakh", "Modern Commentary on Tanakh"], "dependence": "Commentary",
       "base_text_titles": ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]}).save()
