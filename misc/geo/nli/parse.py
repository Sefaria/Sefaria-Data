#from pymarc import parse_xml_to_array
from pymarc import map_xml
import json
import re

places = {}

countries_to_check = [
    "(Israel)",
    "(ישראל)",
    "(יהודה ושומרון)",
    "(West Bank)",
    "(Jordan)",
    "(Syria)",
    "(Lebanon)",
    "(Iraq)",
    "(Egypt)",
    "(Iran)",
]


def get_places(record):
    # print(record.as_dict()["fields"])
    # print(record.as_dict()["fields"])
    place = {}
    for f in record.get_fields('034', "024"): #034 is geo data, 024 is another authorities link (i.e. wikidata)
        # geo_headings = [{f.subfields_as_dict()['9'][0]: f.subfields_as_dict()['a'][0]} for f in record.get_fields('151') if ("Israel" or "ישראל" or "יהודה ושומרון" or "West Bank") in f.subfields_as_dict()['a'][0]]
        geo_headings = [re.sub("\\(.+?\\)","", f.subfields_as_dict()['a'][0]).strip() for f in record.get_fields('151') if set(countries_to_check).intersection(f.subfields_as_dict()['a'][0].split()) and (f.subfields_as_dict()['9'][0] == "lat" or f.subfields_as_dict()['9'][0] == "heb")]
        alt_geo_headings = [re.sub("\\(.+?\\)","", f.subfields_as_dict()['a'][0]).strip() for f in record.get_fields('451') if f.subfields_as_dict()['9'][0] == "lat" or f.subfields_as_dict()['9'][0] == "heb"]

        if len(geo_headings) < 2:
            break

        place["name"] = geo_headings
        place["alt_names"] = alt_geo_headings

        if f.tag == '034':
            loc = {
                    'wlng': f.subfields_as_dict().get('d', [None])[0],
                    'elng': f.subfields_as_dict().get('e', [None])[0],
                    'nlat': f.subfields_as_dict().get('f', [None])[0],
                    'slat': f.subfields_as_dict().get('g', [None])[0],
            }

            place['location'] = place.get('location', {})
            place["location"][f.subfields_as_dict().get('2')[0]] = loc

            print(place['location'])


        if f.tag == '024':
            place['related'] = place.get('related', [])
            place['related'].append(f.subfields_as_dict().get('a')[0])
        # print(place)



    if place != {}:
        p = places.get(place["name"][1], {})

        primary_names = list(set(p.get("primary_names", []) + place["name"]))
        alt_names = list(set(p.get("alt_names", []) + place["alt_names"]))
        loc = {**p.get("location", {}), **place.get("location", {})}
        related = list(set(p.get("related", []) + place.get("related", [])))

        places[place["name"][1]] = {
            "primary_names": primary_names,
            "alt_names": alt_names,
            "related": related,
            "location": loc
        }




        # print(places[place["name"][1]])








map_xml(get_places, 'mazal4sinai.xml')


print(len(places))


with open('data.json', 'w') as jsonfile:
    json.dump(places, jsonfile)
