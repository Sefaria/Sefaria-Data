# encoding=utf-8

"""
Deploy script for the peregrine batch. Copy this file, along with `All_Peregrine_Titles.json` over to the \app directory
in the appropriate sandbox.

This can be accomplished with `kubectl cp`:
`kubectl cp deploy_peregrine.py <pod>:/app/deploy_peregrine.py -c <container>
hint: for the peregrine sandbox, the container name is web-peregrine

The APIKEY is obtained as an environment variable. Also, a SLACK_URL can be supplied, which will notify on slack when
deploy is completed
"""
import os
import sys
import json
import time
import requests
import argparse


assert os.getcwd() == '/app'
sys.path.append('./scripts')
from move_draft_text import ServerTextCopier

argument_parser = argparse.ArgumentParser()
argument_parser.add_argument("-d", "--destination", default="https://www.sefaria.org", help="server to deploy to")
argument_parser.add_argument("-t", "--title_list", default="All_Peregrine_Titles.json", help="JSON file with list of titles to deploy")
arguments = argument_parser.parse_args()

assert os.path.exists(arguments.title_list)
with open(arguments.title_list, 'r') as fp:
    title_list = json.load(fp)

destination = arguments.destination
print "Deploying to {}".format(destination)
apikey = os.getenv('APIKEY')
assert apikey is not None

for i, title in enumerate(title_list):
    print u'{} / {}'.format(i+1, len(title_list))
    copier = ServerTextCopier(destination, apikey, title, post_index=True, versions='all', post_links=2)
    copier.do_copy()

    # give the destination some time to recover
    time.sleep(1.5)

slack = os.getenv('SLACK_URL')
if slack:
    requests.post(slack, json={'text': 'Upload Complete'})
