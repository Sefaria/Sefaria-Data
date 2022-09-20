import django, re, csv, json

import sefaria.system.exceptions

django.setup()
from sefaria.model import *

import traceback
import json
import re
import csv
import requests
from tqdm import tqdm
from urllib.parse import urlencode

from pyproj import Transformer
from sefaria.helper.normalization import NormalizerComposer
from research.knowledge_graph.named_entity_recognition.ner_tagger import NaiveNamedEntityRecognizer, CorpusSegment, NormalizerTools

normalizer = NormalizerComposer(step_keys=["br-tag", "itag", "unidecode", "cantillation", "maqaf", "double-space"])

# cities.json, regions.json, rivers.json
f = open('cities.json')
data = json.load(f)
geo_transformer = Transformer.from_crs("epsg:3857", "epsg:4326")

# non_conforming_refs = []

all_refs = []
bad_refs = []
refs_without_english_slugs = []

places = {}

def append_headword_and_ref_to_existing(ref, headword, loc_name):
    try:
        cur_place_refs = places[loc_name]["links"]
    except:
        cur_place_refs = []

    cur_place_refs.append([ref, headword, loc_name])
    return cur_place_refs



def add_data_if_is_ref(ref, headword, loc):
    loc_meta = loc["attributes"]
    loc_geo = loc["geometry"]

    if Ref.is_ref(ref):
        additional_meta = {}
        try:
            places[loc_meta["שם"]]

        except KeyError as e:
            # if loc_meta["wikidata_id"]: print(f'{loc_meta["wikidata_id"]}: {loc_meta["שם"]}')
            additional_meta = generate_additional_metadata(loc_meta["wikidata_id"], loc_meta["pleiades_id"], loc_meta["שם"], geo_transformer.transform(loc_geo['x'], loc_geo['y']))



        place = places.get(loc_meta["שם"], {
            "slug": additional_meta.get('en_title', loc_meta["שם"]).lower(),
            "titles": {
                "en": additional_meta.get('en_title', None),
                "he": loc_meta["שם"]
            },
            "subclass": "place",
            "description": {
                "en": "",
                "he": "",
            },
            "properties": {
                "wikidata_id": loc_meta["wikidata_id"],
                "pleiades_id": loc_meta["pleiades_id"],
                "geo": {
                    "geometryType": data["geometryType"],
                    "wkid": data["spatialReference"]["latestWkid"],
                    "geometry": loc_geo
                }
            },
            "links": [],
        })

        place_links = append_headword_and_ref_to_existing(ref, headword, loc_meta["שם"])
        place["links"] = place_links

        places[loc_meta["שם"]] = place

        all_refs.append(ref)
        return True
    else:
        return False

def generate_additional_metadata(wikidata_id, pleiades_id, he_place_name, lat_lng=None):
    additional_meta = {}
    if wikidata_id:

        base_url = f'https://www.wikidata.org/w/api.php?action=wbgetentities'

        r = requests.get(base_url, params={
            'format': 'json',
            'props': 'labels|descriptions',
            'ids': {wikidata_id},
            'languages': 'en|he'
        })

        data = r.json()

        additional_meta['en_title'] = data['entities'][wikidata_id]['labels'].get('en', {}).get("value", "")
        additional_meta['he_title'] = data['entities'][wikidata_id]['labels'].get('he', {}).get("value", "")
        additional_meta['en_desc'] = data['entities'][wikidata_id]['descriptions'].get('en', {}).get("value", "")
        additional_meta['he_desc'] = data['entities'][wikidata_id]['descriptions'].get('he', {}).get("value", "")

    elif pleiades_id:
        url = f'http://pleiades.stoa.org/places/{pleiades_id}/json'
        r = requests.get(url)
        if r.status_code == 404:
            pleiades_id = None
            return {}
        data = r.json()
        additional_meta['en_title'] = data['title'].split('/')[0]
        additional_meta['en_desc'] = data['description']
        # print(additional_meta)

    else:
        url = f"http://api.geonames.org/searchJSON?formatted=true&q={he_place_name}&maxRows=10&lang=en&username=rneiss&style=full&featureClass=P&country=IL&country=SY&country=JO&&country=EG&country=LB&country=PS"
        r = requests.get(url)
        data = r.json()
        if data["totalResultsCount"] > 0:
            top_result = data['geonames'][0]
            print('-------------------------------')
            print(f"found: {top_result['name']}: {top_result['lat']},{top_result['lng']}")
            refs_without_english_slugs.append([he_place_name, lat_lng, top_result['name'], f"{top_result['lat']},{top_result['lng']}"])
            # additional_meta['en_title'] = data['title'].split('/')[0]

        else:
            refs_without_english_slugs.append([he_place_name, lat_lng, "", ""])
        #     print(f"no match for {he_place_name}")

    return additional_meta


def generate_json():

    for loc in data['features']:
        refs = loc["attributes"]["אזכורים"].split("\n")
        for ref in refs:
            try:
                split_ref = re.split('\(|\.', ref)
                headword = split_ref[2].replace(")","").strip()
                alma_id = int(split_ref[0])
                cur_ref = split_ref[1].replace("בבלי ", "").strip()

                if not add_data_if_is_ref(cur_ref, headword, loc):
                    if cur_ref.startswith("ירושלמי"):
                        cur_ref = f"תלמוד {cur_ref}"
                    if add_data_if_is_ref(cur_ref, headword, loc):
                        break
                    bad_refs.append([loc["attributes"]["שם"], geo_transformer.transform(loc["geometry"]["x"], loc["geometry"]["y"]), ref])

            except IndexError as e:
                pass

            except Exception as e:
                # ref = re.sub(r'(\d+|\.)', '', ref).strip()
                # non_conforming_refs.append(ref)
                print(traceback.format_exc())
                pass
    return places

def write_csv(filename, arr):
    with open(filename, 'w') as file:
        write = csv.writer(file)
        write.writerows(arr)


def convert_places_to_csv(places):
    rows = []
    for v in places:
        place = places[v]
        lat, lng = geo_transformer.transform(place["properties"]["geo"]["geometry"]["x"], place["properties"]["geo"]["geometry"]["y"])
        place_row = [place["slug"], place["titles"]["en"], place["titles"]["he"], lat, lng, place["properties"]["wikidata_id"], place["properties"]["pleiades_id"]]
        rows.append(place_row)

    write_csv('places.csv', rows)

def convert_links_to_csv(places):
    rows = [ref for v in places for ref in places[v]["links"]]
    write_csv('place_topic_links.csv', rows)


def save_place_to_topic(existing_topic, en_title, he_title, geo, wikidata, pleiades):
    if existing_topic:
        t = existing_topic

    else:
        slug = Topic.normalize_slug(en_title)
        t = Topic.init(slug) or Topic({"slug": slug})

    if not t.has_title(en_title, "en"):
        try:
            t.add_title(en_title, "en", True, False)
        except Exception as e:
            print(e)
            t.add_title(en_title, "en")

    if not t.has_title(he_title, "he"):
        try:
            t.add_title(en_title, "he", True, False)
        except Exception as e:
            print(e)
            t.add_title(en_title, "he")

    t.set_property("geo", {'location': geo}, 'Alma')

    if wikidata != "":
        if getattr(t, 'alt_ids', None):
            t.alt_ids["wikidata"] = wikidata
        else:
            setattr(t, "alt_ids", {'wikidata': wikidata})

    if pleiades != "":
        if getattr(t, 'alt_ids', None):
            t.alt_ids["pleiades"] = pleiades
        else:
            setattr(t, "alt_ids", {'pleiades': pleiades})

    t.save()

    try:
        IntraTopicLink({
            "fromTopic": t.slug,
            "toTopic": "geography",
            "dataSource": "alma",
            "linkType": "is-a",
            "generatedBy": "geo-script-import"
        }).save()

    except Exception as e:
        print(e)

    return t.slug


def check_places():
    places_in_db = Topic().load({"slug": 'places'}).topics_by_link_type_recursively()

    TopicDataSource({
        'slug': 'alma',
        "displayName": {
            "en": "Alma",
            "he": "עלמא"
        }
    }).save()

    he2slug_map = {}
    place_names =[
        name["text"] for place in places_in_db for name in place.titles
    ]

    with open('places_full_eng.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')

        next(csv_reader, None) # skip header row

        for row in csv_reader:

            geo = {
                'type': 'Point',
                'coordinates': [
                    float(row[3]),
                    float(row[2])
                ],
            }

            # if hebrew name is already in place name
            if row[1] in place_names:
                ts = TopicSet.load_by_title(row[1])
                for t in ts:
                    if(t.has_types({'places'})):
                        slug = save_place_to_topic(t, row[0], row[1], geo, row[4], row[5])
                        he2slug_map[row[1]] = slug

            else:
                slug = save_place_to_topic(None, row[0], row[1], geo, row[4], row[5])
                he2slug_map[row[1]] = slug
    return he2slug_map


def find_potential_matches(raw_ref, headword, place):
    replacements = [("ירושלם", "ירושלים")]
    title_strs = [headword]
    for curr, new in replacements:
        alt_title = headword.replace(curr, new)
        if alt_title == headword: continue
        title_strs += [alt_title]
    named_entity = Topic({"slug": "blah", "titles": [{"lang": "he", "primary": True, "text": title} for title in title_strs]})
    ner = NaiveNamedEntityRecognizer([named_entity], normalizer, langSpecificParams={"he": {"prefixRegex": "(?:וכד|לכד|ובד|וד|בד|בכ|וב|וה|וכ|ול|ומ|וש|כב|ככ|כל|כמ|כש|מד|כד|דב|אד|לד|לכ|מב|מה|מכ|מל|מש|שב|שה|שכ|של|שמ|ב|כ|ל|מ|ש|ה|ו|ד|א(?!מר))??"}})
    ner.fit()
    potential_matches = []

    try:
        ref = Ref(raw_ref)
    except:
        return potential_matches

    if ref.is_book_level():
        return potential_matches

    expanded_refs = ref.all_segment_refs()

    for r in expanded_refs:
        text_chunk = r.text(lang='he')
        orig_text = text_chunk.text
        corpus_segment = CorpusSegment(False, orig_text, 'he', 'default', r)
        mentions = ner.predict_segment(corpus_segment)
        for mention in mentions:
            potential_matches.append([r.normal(), place, mention.start, mention.end, mention.mention])

    if len(potential_matches) == 0:
        trimmed_ref = " ".join(str(x) for x in raw_ref.split(' ')[:-1])
        potential_matches = find_potential_matches(trimmed_ref, headword, place)

    return potential_matches


def create_geo_ref_topic_links(he2slug_map):

    with open('place_topic_links (copy).csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')

        next(csv_reader, None) # skip header row

        no_match_refs = []
        potential_false_positives = []
        expected_good_matches = []

        for row in tqdm(list(csv_reader)):
            ref, headword, place = row
            potential_matches = find_potential_matches(ref, headword, place)

            if len(potential_matches) == 0:
                no_match_refs.append(row)

            elif len(potential_matches) > 1:
                potential_false_positives.append(row)

            else:
                expected_good_matches.append(potential_matches[0])
                # print(f'{potential_matches}: {headword}')

                slug = he2slug_map[place]
                mention_link = {
                    "toTopic": slug,
                    "linkType": "mention",
                    "dataSource": "alma",
                    "class": "refTopic",
                    "is_sheet": False,
                    "ref": potential_matches[0][0],
                    "expandedRefs": [potential_matches[0][0]],
                    "charLevelData": {
                        "startChar": potential_matches[0][2],
                        "endChar": potential_matches[0][3],
                        "versionTitle": Ref(potential_matches[0][0]).text(lang='he').version().versionTitle,
                        "language": 'he',
                        "text": potential_matches[0][4]
                    },
                    "generatedBy": "geo-script-import"
                }
                try:
                    RefTopicLink(mention_link).save()

                except sefaria.system.exceptions.DuplicateRecordError as e:
                    pass
                    # print(e)

    write_csv("no_match_refs.csv", no_match_refs)
    write_csv("expected_good_matches.csv", expected_good_matches)
    write_csv("potential_false_positives.csv", potential_false_positives)

    print(len(expected_good_matches))
    print(len(potential_false_positives))
    print(len(no_match_refs))


if __name__ == '__main__':
    he2slug_map = check_places()
    create_geo_ref_topic_links(he2slug_map)




# print(set(bad_refs))`
# print(len(set(bad_refs)))


# print(generate_json())

# generate_json()
# with open('places.json', 'w') as convert_file:
#     convert_file.write(json.dumps(places))

# write_csv("bad_refs.csv", bad_refs)
# write_csv("places_wo_eng.csv", refs_without_english_slugs)
# print(len(places))
# print(len(all_refs))
# f = open('places.json', )
# data = json.load(f)

# convert_places_to_csv(data)
# convert_links_to_csv(data)