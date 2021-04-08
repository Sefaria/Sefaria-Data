import django
django.setup()
from sefaria.sheets import save_sheet
from sefaria.model import *
from sefaria.system.database import db
from sefaria.system.exceptions import InputError

def sheets_to_update():
    cursor = db.sheets.find({'expandedRefs': {'$regex': '^Rif'}})
    return [s['id'] for s in cursor]


def rewrite_source(source):
    requires_save = False
    if "ref" in source:
        try:
            Ref(source["ref"])
        except (InputError, ValueError):
            print("Error: In clean_sheets.rewrite_source: failed to instantiate Ref {}".format(source["ref"]))
        else:
            if source['ref'].startswith('Rif '):
                requires_save = True
                source["ref"] = source["ref"].split(':')[0]
    if "subsources" in source:
        for subsource in source["subsources"]:
            requires_save = rewrite_source(subsource) or requires_save
    return requires_save

ss = sheets_to_update()
print(len(ss))
for sid in ss:
    needs_save = False
    sheet = db.sheets.find_one({"id": sid})
    if not sheet:
        print("Likely error - can't load sheet {}".format(sid))
    for source in sheet["sources"]:
        if rewrite_source(source):
            needs_save = True
    if needs_save:
        sheet["lastModified"] = sheet["dateModified"]
        print(f'saving sheet {sheet["id"]}')
        save_sheet(sheet, sheet["owner"], search_override=True)
