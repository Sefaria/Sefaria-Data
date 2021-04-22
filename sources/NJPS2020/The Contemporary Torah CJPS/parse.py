import os
from lxml import etree
tags = set()
attrib = set()
attrib_values = set()
for f in os.listdir("."):
    lines = ""
    with open(f, 'r') as f:
        lines = "\n".join(list(f))
        asdf = etree.XML(lines)
        for s in asdf:
            tags.add(s.tag)
            for attrib_key, attrib_value in s.attrib.items():
                if " " not in attrib_value and attrib_key != "number":
                    attrib.add((attrib_key, attrib_value))
            for el in s:
                tags.add(el.tag)
                for attrib_key, attrib_value in el.attrib.items():
                    if " " not in attrib_value and attrib_key != "number":
                        attrib.add((attrib_key, attrib_value))

print(tags)
print(attrib)
