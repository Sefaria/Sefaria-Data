import django
django.setup()
from sefaria.model import *

if __name__ == '__main__':
    s = """מיי' פ' י"ד מהל' מאכלות אסורות הלכה ג':"""
    linker = library.get_linker("he")
    assert isinstance(linker, Linker)
    doc = linker.link(s, type_filter="citation", with_failures=False)
    print(doc.resolved_refs[0].ref)

    s = """טור ושו"ע או"ח סי' שמ"ו סעיף א'"""
    doc = linker.link(s, type_filter="citation", with_failures=False)
    print(doc.resolved_refs[0].ref)