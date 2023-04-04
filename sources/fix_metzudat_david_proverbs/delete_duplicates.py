import django

django.setup()

django.setup()
from sefaria.model import *
from sefaria.system.database import db
from bson.objectid import ObjectId

import json

def delete_links(list_of_links):
    for l in list_of_links:
        # print("deleted link with refs: " + str(l.refs))
        print("deleted link with id " + l._id)

        to_del = LinkSet({'_id': ObjectId(l._id)}).array()[0]
        to_del.delete()

if __name__ == '__main__':
    print("hello world")
    query = {"refs": {"$regex": "Metzudat David on Proverbs"}}
    list_of_links = LinkSet(query).array()
    # print(len(list_of_links))
    list_of_links = [link for link in list_of_links if link.type == "commentary"]
    # print(len(list_of_links))
    link_refs_list = []
    to_delete = []
    for link in list_of_links:
        # if link_refs.count((set(link.expandedRefs0) | set(link.expandedRefs1))) > 1:
        link_refs = (set(link.expandedRefs0) | set(link.expandedRefs1))
        if link_refs in link_refs_list:
            to_delete.append(link)
        else:
            link_refs_list.append(link_refs)


    # with open("links_to_delete.json", "w") as outfile:
    #
    #     dicts = [vars(link) for link in to_delete]
    #     for dict in dicts:
    #         dict['_id'] = str( dict['_id'])
    #     json.dump(dicts, outfile, indent=4)
    delete_links(to_delete)

    print("deleted " + str(len(to_delete)) + " links")






