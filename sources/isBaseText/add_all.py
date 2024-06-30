import django
django.setup()
from sefaria.model import *
import re
from sefaria.constants import model as constants
from sefaria.system.database import db
from pymongo import ReplaceOne

col = db['texts']
requests = []
for version in col.find():
    actualLanguage = version.get("actualLanguage")
    versionTitle = version.get("versionTitle")
    if not actualLanguage and versionTitle:
        languageCode = re.search(r"\[([a-z]{2})\]$", versionTitle)
        if languageCode and languageCode.group(1):
            actualLanguage = languageCode.group(1)
    if not actualLanguage:
        actualLanguage = version['language']
    version['actualLanguage'] = actualLanguage

    if not version.get('languageFamilyName'):
        try:
            version['languageFamilyName'] = constants.LANGUAGE_CODES[actualLanguage]
        except KeyError:
            version['languageFamilyName'] = constants.LANGUAGE_CODES[version['language']]

    if not version.get("isSource", False):
        version['isSource'] = True if version['actualLanguage'] == 'he' else False
    if version['versionTitle'] == 'Tikkun Midot HaNefesh, Jerusalem 1996':
        version['isSource'] = False
    if not version.get("isPrimary", False):
        if version['isSource'] or len(VersionSet({'title': version['title']})) == 1:
            version['isPrimary'] = True
        else:
            version['isPrimary'] = False

    if not version.get('direction'):
        version['direction'] = 'rtl' if version['language'] == 'he' else 'ltr'

    try:
        del version['isBaseText']
    except KeyError:
        pass

    requests.append(ReplaceOne({'_id': version['_id']}, version))
    if len(requests) > 999:
        col.bulk_write(requests, ordered=False)
        requests = []
