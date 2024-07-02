from sources.functions import *
nodes = """Introductions
Post-biblical Interpretations"
Contemporary Reflection
Another View""".splitlines()

root = SchemaNode()
root.key = "The Torah; A Women's Commentary"
root.add_primary_titles(root.key, "")
for book in ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]:
    book_node = JaggedArrayNode()
    book_node.key = book
    book_node.add_primary_titles(book, library.get_index(book).get_primary_title('he'))
    book_node.add_structure(["Chapter", "Verse", "Paragraph"])
    book_node.depth = 3
    book_node.validate()
    root.append(book_node)

for node in nodes:
    child = SchemaNode()
    child.key = node
    child.add_primary_titles(child.key, "")
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
