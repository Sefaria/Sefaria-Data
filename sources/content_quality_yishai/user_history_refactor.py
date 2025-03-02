import django
django.setup()
from pymongo import UpdateOne
from sefaria.system.database import db

text_col = db.texts
user_hist_col = db.user_history

docs = user_hist_col.find({'versions': {'$exists': True}})
bulk_ops = []
for doc in docs:
    if isinstance(doc.get('he'), dict):
        continue
    else:
        old_ver = doc['versions']
        new_ver = {}
        for lang in ['he', 'en']:
            version_title = old_ver.get(lang)
            if version_title and not isinstance(version_title, dict):
                query = {'versionTitle': version_title, 'title': doc['book']}
                if lang == 'he':
                    query['isPrimary'] = True
                else:
                    query['isSource'] = False
                version = text_col.find_one(query)
                if not version:
                    if old_ver['en'] not in ['test [pt]', 'Yishai']:
                        print(old_ver, query)
                    continue
                new_ver[lang] = {'versionTitle': version['versionTitle'], 'languageFamilyName': version['languageFamilyName']}
            else:
                new_ver[lang] = {'versionTitle': '', 'languageFamilyName': ''}
        if new_ver:
            bulk_ops.append(UpdateOne({'_id': doc['_id']}, {'$set': {'versions': new_ver}}))

# if bulk_ops:
#     result = user_hist_col.bulk_write(bulk_ops)
#     print(f"{result.modified_count} documents updated.")
# else:
#     print("No updates required.")

