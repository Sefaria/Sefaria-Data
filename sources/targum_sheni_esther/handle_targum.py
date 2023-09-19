import django

django.setup()

django.setup()
superuser_id = 171118
# import statistics
import csv
from sefaria.model import *
from sefaria.helper.schema import insert_last_child, reorder_children
from sefaria.helper.schema import remove_branch
from sefaria.tracker import modify_bulk_text
from sefaria.helper.category import create_category
from sefaria.system.database import db
# import time

def post_indices():
    from sources.functions import post_index, add_term
    add_term("Targum Sheni", "תרגום שני", server="https://new-shmuel.cauldron.sefaria.org")
    # add_term("Targum Sheni", "תרגום שני")
    # add_term("Targum Sheni", "תרגום שני", server="https://new-shmuel.cauldron.sefaria.org")
    # index = post_index({'title': 'Targum_Sheni_on_Esther'}, server="https://new-shmuel.cauldron.sefaria.org", method="GET")
    # index["dependence"] = "targum"
    # index["base_text_titles"] = ["Esther"]
    # index["collective_titpsqlle"] = "Targum Sheni"
    # post_index(index, server="https://new-shmuel.cauldron.sefaria.org")




if __name__ == '__main__':
    print("hello world")
    post_indices()









