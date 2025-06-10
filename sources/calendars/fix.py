from datetime import datetime
from sefaria.system.database import db

collection = db.tanakh_yomi

today = datetime.combine(datetime.today().date(), datetime.min.time())

find_and_replace = (('סדר יו', 'סדר טז'), ('סדר יה', 'סדר טו'))

for find, replace, in find_and_replace:
    query = {
        "heDisplayValue": {"$regex": f"{find}$"},
        "date": {"$gte": today}
    }

    # Find all matching documents
    docs = collection.find(query)

    for doc in docs:
        original_value = doc['heDisplayValue']
        new_value = original_value[:-6] + replace
        # Update document with new value
        collection.update_one(
            {"_id": doc["_id"]},
            {"$set": {"heDisplayValue": new_value}}
        )
        print(f"Updated _id={doc['_id']} from '{original_value}' to '{new_value}'")
