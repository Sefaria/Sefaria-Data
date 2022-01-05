from sources.functions import *
essays = defaultdict(list)
subessays = defaultdict(dict)
order_essays = []
with open("essay contents/essays.csv") as f:
    for row in csv.reader(f):
        book, num, comm = row
        essays[book].append(comm)
        if book not in order_essays:
            order_essays.append(book)
with open("essay contents/subessay contents.csv") as f:
    for row in csv.reader(f):
        essay, essay_ref, subessay, subessay_ref, num, comm = row
        essay = essay.strip()
        subessay = subessay.strip()
        if essay not in subessays:
            subessays[essay] = defaultdict(list)
        subessays[essay][subessay].append(comm)

root = SchemaNode()
root.add_primary_titles("Everett Fox Torah", "")
for essay in order_essays:
    if essay in subessays:
        schemanode = SchemaNode()
        schemanode.add_primary_titles(essay, "")
        for subessay in subessays[essay]:
            node = JaggedArrayNode()
            node.add_structure(["Paragraph"])
            node.depth = 1
            node.add_primary_titles(subessay, "")
            schemanode.append(node)
        default = JaggedArrayNode()
        default.default = True
        default.key = "default"
        schemanode.append(default)
        root.append(schemanode)
    else:
        node = JaggedArrayNode()
        node.add_structure(["Paragraph"])
        node.depth = 1
        node.add_primary_titles(essay, "")
        root.append(node)
pass