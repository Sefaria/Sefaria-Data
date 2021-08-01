import django
django.setup()
import yutil
from sefaria.model import *

VersionSet({"title": {"$regex": "^JT"}, "versionTitle": "With Venice Columns"}).delete()
VersionSet({"title": {"$regex": "^JT"}, "versionTitle": "With Vilna Pages"}).delete()

yutil.load_guggenheimer_data()

va = yutil.VersionAlignment(yutil.venice, yutil.gugg, "./v_comp", skip_mishnah=True)
va.annotate_base()
print(va.errors)

yutil.load_guggenheimer_data("With Venice Columns")

va = yutil.VersionAlignment(yutil.mm, yutil.gugg, "./comparison", skip_mishnah=False)
va.annotate_base()
print(va.errors)



