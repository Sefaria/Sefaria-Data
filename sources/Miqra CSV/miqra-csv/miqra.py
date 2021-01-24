from sefaria.export import *
import os
import codecs
files = os.listdir(".")
for f in files:
    with codecs.open(f, 'r', encoding='utf-8') as open_f:
        import_versions_from_stream(open_f, [1], 1)
