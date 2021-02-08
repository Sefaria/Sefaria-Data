from sources.functions import *
import csv
links = []
with open("AZ_Index_link_mapping_-_corrected_.csv", 'r') as f:
    for row in csv.reader(f):
        i, azharot, zohars = row
        if len(zohars) > 0:
            for zohar in eval(zohars):
                links.append({"refs": [zohar, azharot], "generated_by": "zohar_to_azharot", "type": "Commentary", "auto": True})
    post_link(links)