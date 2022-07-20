import django

django.setup()

from sefaria.model import *

if __name__ == '__main__':

    version_set = VersionSet({'versionTitle': 'Talmud Bavli. German. Lazarus Goldschmidt. 1929 [de]'})
    for v in version_set:
        v.status = "locked"
        v.license = "Public Domain"
        v.digitizedBySefaria = True
        v.save()
