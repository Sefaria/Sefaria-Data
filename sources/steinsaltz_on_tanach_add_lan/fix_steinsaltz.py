import django

django.setup()

superuser_id = 171118
# import statistics
import csv
from sefaria.model import *
# from sefaria.helper.schema import insert_last_child, reorder_children
# from sefaria.helper.schema import remove_branch
from sefaria.tracker import modify_bulk_text
from sefaria.helper.category import create_category
from sefaria.system.database import db
from sefaria.utils.talmud import daf_to_section, section_to_daf
import re
import copy




if __name__ == '__main__':
    print("hello world")
    hebrew_versions = VersionSet({"versionTitle": "The Koren Steinsaltz Tanakh HaMevoar - Hebrew"}).array()
    english_versions = VersionSet({"versionTitle": "The Steinsaltz Tanakh - English"}).array()
    for version in hebrew_versions:
        version.languageFamilyName = 'hebrew'
        version.isPrimary = True
        version.isSource = True
        version.save()
        print("fixed: " + version.title)
    for version in english_versions:
        version.languageFamilyName = 'english'
        version.save()
        print("fixed: " + version.title)
    print('finished')











