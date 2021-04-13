import django
django.setup()
import requests
from sefaria.model import *
from scripts.move_draft_text import ServerTextCopier
import argparse
import os
import time
import json
from concurrent.futures import ThreadPoolExecutor

#DEST = 'https://www.sefaria.org'
DEST = os.environ['DEST']
APIKEY = os.environ['APIKEY']
print(DEST, APIKEY)


def check_uploaded(title):
    url = f'{DEST}/api/v2/raw/index/{title.replace(" ", "_")}'
    response = requests.get(url)
    try:
        json_response = response.json()
    except json.JSONDecodeError:
        return False
    if 'error' in json_response:
        return False
    return True

def deploy_index(index):
    copier = ServerTextCopier(DEST, APIKEY, index, post_index=True)
    copier.do_copy()

def deploy_text(index):
    copier = ServerTextCopier(DEST, APIKEY, index, post_index=False, versions='all')
    copier.do_copy()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--indices', help='deploy indexes', action="store_true")
    parser.add_argument('-t', '--texts', help='deploy texts', action="store_true")
    parser.add_argument('-b', '--begin', default=0)
    parser.add_argument('-n', '--number', default=None, help='number of texts to deploy in this run')

    args = parser.parse_args()
    begin = int(args.begin)
    end = int(args.number) + begin if args.number else None
    # dirname = os.path.dirname((os.path.realpath(__file__)))
    # outpath = os.path.join(dirname, 'finished_texts.json')
    # if os.path.exists(outpath):
    #     with open(outpath) as fp:
    #         done = set(json.load(fp))
    # else:
    done = set(library.get_indexes_in_category('Bavli'))
    indexes = library.get_indexes_in_category('Rif', include_dependant=True)

    if args.indices:
        with ThreadPoolExecutor() as executor:
            uploaded = executor.map(check_uploaded, indexes)
        for ind, upload in zip(indexes, uploaded):
            if upload:
                done.add(ind)

        indexes = set(indexes[begin:end])
        while indexes - done:
            for index in indexes - done:
                bases = getattr(library.get_index(index), 'base_text_titles', False)
                if not bases or all(i in done for i in bases):
                    print(index)
                    deploy_index(index)
                    done.add(index)
                    # with open(outpath, 'w') as fp:
                    #     json.dump(list(done), fp)
                    print(len(indexes - done), 'remaining')

    if args.texts:
        text_list = library.get_indexes_in_category('Rif', include_dependant=True)
        for text_num, index in enumerate(text_list[begin:end], begin):
            print(f'deploying text {text_num}/{len(text_list)};', f'{end-text_num} remaining for this run')
            start = time.time()
            deploy_text(index)
            completed = time.time()
            print('text uploaded. time elapsed:', completed-start)
