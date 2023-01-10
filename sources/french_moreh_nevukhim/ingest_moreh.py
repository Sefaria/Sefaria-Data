import django, csv
django.setup()
import re
from sefaria.model import *
import csv
from sefaria.tracker import modify_bulk_text
csv.field_size_limit(1000000)



if __name__ == "__main__":
    print("The fair Ophelia!—Nymph, in thy orisons Be all my sins remember'd.")
    superuser_id = 171118
    ref_dict = {}

    # delete version if already exits:
    cur_version = VersionSet({'title': 'Guide for the Perplexed',
                              'versionTitle': "Guide des égarés, trans. by Salomon Munk, Paris, 1856 [fr]"})
    if cur_version.count() > 0:
        cur_version.delete()

    # parse csv into dictionary of refs:
    with open('moreh_fixed_all_parts_with_imgs.csv', newline='') as csvfile:
        r = csv.reader(csvfile, delimiter=',')
        for row in r:
            if('Guide for the Perplexed' in row[0]):
                ref_dict[row[0]] = row[2]

    # create new version:
    index = library.get_index("Guide for the Perplexed")

    chapter = index.nodes.create_skeleton()
    new_version = Version({"versionTitle": "Guide des égarés, trans. by Salomon Munk, Paris, 1856 [fr]",
                           "versionSource": "https://www.nli.org.il/he/books/NNL_ALEPH990012364290205171/NLI",
                           "title": "Guide for the Perplexed",
                           "chapter": chapter,
                           "language": "en",
                           "digitizedBySefaria": True,
                           "license": "PD",
                           "status": "locked"
                           })
# put in db
modify_bulk_text(superuser_id, new_version, ref_dict)
print("finished update")





# Print the list of sup tags with ref tags

