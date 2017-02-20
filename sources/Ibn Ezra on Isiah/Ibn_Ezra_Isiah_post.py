import xml.etree.ElementTree as ET

tree = ET.parse('IbnEzra_Isiah.xml')
root = tree.getroot()
for chapter in root.iter('chapter'):
    print chapter.find('title').text
    for p in chapter.findall('p'):
        text = "".join(p.itertext())
        for pitem in p.iter():
            if pitem.tag == 'italic':
                text = text.replace(pitem.text,"<b>"+pitem.text+"</b>")

    print text

"""
    for pitem in p[tag='italic']:
    text = text.replace(pitem.text,"<b>"+pitem.text+"</b>")
    print text
    """