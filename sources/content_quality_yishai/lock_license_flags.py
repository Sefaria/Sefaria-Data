import django
django.setup()
from sefaria.model import *

def set_heComplete(title):
    vs = VersionState().load({'title': title})
    vs.flags['heComplete'] = True
    vs.save()

def lock_license_and_flags(query, license=None, lock=True, digitizedBySefaria=None, heComplete=None):
    for version in VersionSet(query):
        print(version.title, version.versionTitle, license, lock, digitizedBySefaria, heComplete)
        if lock:
            version.status = 'locked'
        if license:
            version.license = licenselinker-v3


        if digitizedBySefaria:
            version.digitizedBySefaria = True
        version.save()
        if heComplete:
            set_heComplete(version.title)

if __name__ == '__main__':
    lock_license_and_flags({'versionTitle': 'Vilna Edition'}, license='Public Domain')
    lock_license_and_flags({'versionTitle': 'Piotrków, 1898-1900'}, license='Public Domain', heComplete=True, digitizedBySefaria=True)
    lock_license_and_flags({'versionTitle': {'$in': ['The Tosefta according to to codex Vienna. Third Augmented Edition, JTS 2001', 'Tosefta Kifshuta. Third Augmented Edition, JTS 2001']}},
                           license='CC-BY', digitizedBySefaria=True, heComplete=True)

