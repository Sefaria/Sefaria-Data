import django

django.setup()

superuser_id = 171118
# import statistics
import csv
from sefaria.model import *
import re


# from sefaria.helper.schema import insert_last_child, reorder_children
# from sefaria.helper.schema import remove_branch
from sefaria.tracker import modify_bulk_text

# from sefaria.helper.category import create_category
# from sefaria.system.database import db

class AltStructNode:
    def __init__(self, en_title, he_title, start_tref, end_tref):
        # Instance attributes
        self.en_title = en_title
        self.he_title = he_title
        self.whole_ref = Ref(start_tref).to(Ref(end_tref)).normal()

    def get_alt_struct_json_node(self):
        template = f'''               {{
                    "nodeType" : "ArrayMapNode",
                    "depth" : NumberInt(0),
                    "wholeRef" : "{self.whole_ref}",
                    "includeSections" : false,
                    "titles" : [
                        {{
                            "primary" : true,
                            "text" : "{self.en_title}",
                            "lang" : "en"
                        }},
                        {{
                            "primary" : true,
                            "text" : "{self.he_title}",
                            "lang" : "he"
                        }}
                    ]
                }}
        '''

        return template



if __name__ == '__main__':
    print("hello world")
    nodes = []
    with open('alt_struct.csv', 'r') as file:
        csv_reader = csv.reader(file)
        next(csv_reader, None)
        for row in csv_reader:
            node = AltStructNode(row[1], row[0], row[2], row[3])
            nodes += [node]

    print(
        '''
           "alt_structs" : {
    "Topic" : {
        "nodes" : [
        '''
    )
    last_node = nodes[-1]
    for node in nodes:
        print(node.get_alt_struct_json_node())
        if node != last_node:
            print(',')

    print(
        '''
                    ]
        }
    },
        '''
    )
    # print("end")



