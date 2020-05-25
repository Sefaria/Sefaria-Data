import django
django.setup()
from sefaria.model import *
if __name__ == '__main__':
titles = ["I", "II", "III", "IV", "V", "VI"]
for title in titles:
	actual_title = "Contemporary Halakhic Problems, Vol {}".format(title)
	i = library.get_index(actual_title)
	versions = i.versionSet()
	for v in versions:
		print v.versionTitle
		v.versionTitle = v.versionTitle.replace(";", "")
		v.save()
	i.save()
