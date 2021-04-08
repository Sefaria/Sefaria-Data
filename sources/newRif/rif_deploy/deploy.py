import django
django.setup()
from sefaria.model import *
from scripts.move_draft_text import ServerTextCopier
import argparse
import os
import json

#DEST = 'https://www.sefaria.org'
DEST = os.environ['DEST']
APIKEY = os.environ['APIKEY']
print(DEST, APIKEY)

def deploy_index(index):
    copier = ServerTextCopier(DEST, APIKEY, index, post_index=True)
    copier.do_copy()

def deploy_text(index):
    copier = ServerTextCopier(DEST, APIKEY, index, post_index=False, versions='all')
    copier.do_copy()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--i', help='deploy indexes', action="store_true")
    parser.add_argument('--t', help='deploy texts', action="store_true")
    parser.add_argument('-b', '--begin', default=0)
    parser.add_argument('-e', '--end', default=None)

    args = parser.parse_args()
    begin = int(args.begin)
    end = int(args.end) if args.end else None
    dirname = os.path.dirname((os.path.realpath(__file__)))
    outpath = os.path.join(dirname, 'finished_texts.json')
    if os.path.exists(outpath):
        with open(outpath) as fp:
            done = set(json.load(fp))
    else:
        done = set(library.get_indexes_in_category('Bavli'))

    if args.i:
        indexes = set(library.get_indexes_in_category('Rif', include_dependant=True)[begin:end])
        while indexes - done:
            for index in indexes - done:
                bases = getattr(library.get_index(index), 'base_text_titles', False)
                if not bases or all(i in done for i in bases):
                    print(index)
                    deploy_index(index)
                    done.add(index)
                    with open(outpath, 'w') as fp:
                        json.dump(list(done), fp)
                    print(len(indexes - done), 'remaining')

    if args.t:
        for text_num, index in enumerate(library.get_indexes_in_category('Rif', include_dependant=True)[begin:end], begin):
            if index.title in done:
                continue
            print(f'deploying text {text_num}')
            deploy_text(index)
            done.add(index.title)
            with open(outpath, 'w') as fp:
                json.dump(list(done), fp)
