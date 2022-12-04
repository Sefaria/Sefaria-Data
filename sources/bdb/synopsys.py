import os
import re
from bs4 import BeautifulSoup
import requests
import json
from hub_al3rdphase import get_al_text
import django
django.setup()
from kevin_al import get_bdbentry
from tqdm import tqdm
from time import sleep
import bleach

BASE = "synopsis-2-4-alt.loadbalancer.dicta.org.il"
SYNOPSIS_BASE_URL = f"https://{BASE}/synopsis"
SYNOPSIS_EXTENSION_URL = "/api/synopsis"

def synopsis_initial_call():
    response_data = requests.post(SYNOPSIS_BASE_URL + SYNOPSIS_EXTENSION_URL + "/uploadfile/0")
    return response_data.json()["id"]

def synopsis_upload_files(synopsis_id, json_obj):
    response_data = requests.post(SYNOPSIS_BASE_URL + SYNOPSIS_EXTENSION_URL + "/uploadfile/" + synopsis_id,
                                  files=json_obj, headers={})
    return response_data.json()

def synopsis_result(synopsis_id, groupwords=False):
    data = {"Grouping": "All"} if groupwords else {"Grouping": "None"}
    requests.post(SYNOPSIS_BASE_URL + SYNOPSIS_EXTENSION_URL + "/" + synopsis_id, data=data)
    url = SYNOPSIS_BASE_URL + "/ExcelOutput/" + synopsis_id + ".CollateX.json"
    response_obj = requests.get(url)
    # repetitions = 0
    tries = 0
    code = None
    for _ in tqdm(range(1500)):
        # repetitions += 1
        code = response_obj.status_code
        if code != 200:
            if code == 500 or code == 404:
                tries += 1
                if tries > 10:
                    return

            sleep(1)
            response_obj = requests.get(url)
        else:
            break
    return response_obj.content

def synopsis_all_calls(name, json_obj, groupwords=False):
    synopsis_id = synopsis_initial_call()
    with open('Collatex.temp.json', 'w') as fp:
        json.dump(json_obj, fp)
    with open('synopsis.settings.json', 'w') as fp:
        json.dump({"Grouping": "None", "AllowOutliers": "true"}, fp)
    with open('synopsis.settings.json', 'rb') as f0:
        with open('Collatex.temp.json', 'rb') as fp:
            upload_response = synopsis_upload_files(synopsis_id, {name: fp, 'synopsis.settings.json': f0})
    if len(upload_response['uploads_failed']) != 0:
        print(repr(upload_response))
    output = synopsis_result(synopsis_id, groupwords=groupwords)
    return output

def get_kev_text(key):
    soup = BeautifulSoup(get_bdbentry(key).as_strings()[0], 'html.parser')
    print(key)
    for ar in soup.select('arabic'):
        ar.string.replace_with('اَلْعَرَبِيَّةُ')
    for pe in soup.select('persian'):
        pe.string.replace_with('فارسی')
    for sy in soup.select('syriac'):
        sy.string.replace_with('ܠܫܢܐ')
    for et in soup.select('ethiopic'):
        et.string.replace_with('ግዕዝ')
    for sa in soup.select('samaritan'):
        sa.string.replace_with('INSERT-SAMARITAN')
    text = str(soup)
    text = bleach.clean(text, ['strong', 'em', 'sub', 'sup', 'a'], strip=True)
    text = ' '.join(text.split())
    text = re.sub('^([VI  †\[]*)<strong>([^<]*)</strong>', r'\1\2', text)
    text = re.sub('(<[^<>]*>)', r' \1 ', text)
    text = re.sub("THE FOLLOWING &ADI IS PART OF THE GREEK WORD (NO ENTITY IN GREEK)|ATNAH ON TOP OF TAU IN FOLLOWING - NO CHARACTER FOR THIS|THE FOLLOWING &ADI IS PART OF THE GREEK WORD - NO ENTITY IN GREEK|THE FOLLOWING C CEDILLA'S ARE CLOSE, BUT NOT THE EXACT CHARACTER, WHICH LOOKS MORE LIKE A RIGHT CURLY QUOTE UNDER THE C - SEE PAGE 109|THE FOLLOWING &AODA IS PART OF THE GREEK WORD - NO ENTITY IN GREEK|THE FOLLOWING &AMA IS PART OF THE GREEK WORD - NO ENTITY IN GREEK|THE FOLLOWING &AMW IS PART OF THE GREEK WORD - NO GREEK ENTITY|THE FOLLOWING &ADI IS PART OF THE GREEK WORD|NO ENTITY IN GREEK", '', text)
    text = re.sub('WAITING FOR PRADIS ENTITY TO REPLACE (UNDERCIRCLE)', '̥', text)
    text = re.sub('this is waiting for an upside down under breve entity', '̯', text)
    text = ' '.join(re.split('(—)', text))
    return text

def get_hub_text(key):
    with open(f'bh_divided/{key}.html') as fp:
        hub_soup = BeautifulSoup(fp.read(), 'html.parser')
    hub_text = str(hub_soup)
    hub_text = bleach.clean(hub_text, ['sup'], strip=True)
    hub_text = re.sub('(<[^<>]*>)', r' \1 ', hub_text)
    return hub_text

if __name__ == '__main__':
    with open('hub_dict_new.json') as fp:
        hub_dict = json.load(fp)

    files = os.listdir('synopsys')
    problems = []
    for hub in hub_dict:
        if f'{hub}.json' in files:
            continue
        print(hub)
        hub_text = get_hub_text(hub)
        if hub_dict[hub]['kevin']:
           kev_text = get_kev_text(hub_dict[hub]['kevin'])
        else:
            print('nokevin')
            continue
        # if not 'فارسی' in kev_text:
        #     continue
        texts = {'hub': hub_text, 'kev': kev_text}
        if hub_dict[hub]['al']:
            al_text = get_al_text(hub_dict[hub]['al'])
            texts['al'] = al_text
        texts = {'witnesses': [{
            'tokens': [{'t': x} for x in texts[text].split()],
            'id': text
        } for text in texts]}
        output = synopsis_all_calls(hub, texts)
        if output:
            with open(f'synopsys/{hub}.json', 'wb') as fp:
                fp.write(output)
        else:
            problems.append(hub)
    print(problems)
