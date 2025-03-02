import django

django.setup()
from sefaria.model import *

if __name__ == '__main__':
    print("hi")
    passages = PassageSet().array()  # Retrieve all Passage records

    updated_count = 0

    for passage in passages:
        passage.source = "Steinsaltz"
        passage.save()  # Save the updated document
        updated_count += 1

    print(f"Updated {updated_count} documents.")
