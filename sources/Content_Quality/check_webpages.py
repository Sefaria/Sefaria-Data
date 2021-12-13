from sources.functions import *
from sefaria.model.webpage import *
from collections import Counter
w = WebPage().load({"url": "https://yutorah.org/daf.cfm/6040/taanit/2/a/static/rand=0.9185715476199539&amp;iit=1635769073858&amp;tmr=load=1635769073708&amp;core=1635769073742&amp;main=1635769073854&amp;ifr=1635769073861&amp;cb=0&amp;cdn=0&amp;md=0&amp;kw=&amp;ab=-&amp;dh=yutorah.org&amp;dr=https://www.google.com/&amp;du=https://www.yutorah.org/daf.cfm/6040/taanit/2/a/&amp;href=https://www.yutorah.org/daf.cfm/6040/taanit/2/a/&amp;dt=YUTorah%20Online%20-%20On%20the%20Daf%20-%20Taanit/2/static/rand=0.9185715476199539&amp;iit=1635769078335&amp;tmr=load=1635769078210&amp;core=1635769078235&amp;main=1635769078332&amp;ifr=1635769078337&amp;cb=0&amp;cdn=0&amp;md=0&amp;kw=&amp;ab=-&amp;dh=www.yutorah.org&amp;dr=https://www.yutorah.org/daf.cfm/6040/taanit/2/a/&amp;du=https://www.yutorah.org/daf.cfm/6040/taanit/2/a/static/rand=0.9185715476199539&amp;iit=1635769073858&amp;tmr=load=1635769073708&amp;core=1635769073742&amp;main=1635769073854&amp;ifr=1635769073861&amp;cb=0&amp;cdn=0&amp;md=0&amp;kw=&amp;ab=-&amp;dh=www.yutorah.org&amp;dr=https://www.google.com&amp;href=https://www.yutorah.org/daf.cfm/6040/taanit/2/a/static/static/sh.f48a1a04fe8dbf021b4cda1d.html"})
for page in WebPageSet({"$expr": {"$gt": [{"$strLenCP": "$url"}, 1000]}}):
    # url field is indexed. Mongo doesn't allow indexing a field over 1000 bytes
    from sefaria.system.database import db

    db.webpages_long_urls.insert_one(page.contents())
    print(f"Moving {page.url} to long urls DB...")
    page.delete()