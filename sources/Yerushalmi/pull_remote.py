# encoding=utf-8

from sources.Yerushalmi.sefaria_objects import *
from scripts.pull_text_from_server import pull_text_from_server, make_version, version_url_generator

titles = [t for t in library.get_indexes_in_category("Yerushalmi") if "JTmock" in t]
titles
for title in titles:
    print(title)
    version_urls = version_url_generator('https://jtmock.cauldron.sefaria.org', title)
    for u in version_urls:
        remote_text = pull_text_from_server(u)
        make_version(remote_text, 23432)

