import csv
import requests
import urllib
import json
import time

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from stem import Signal
from stem.control import Controller


# spoof a real browser as jstor et al don't take kindly to bots
headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Upgrade-Insecure-Requests': '1',
    'Alt-Used': 'dx.doi.org',
    'Connection': 'keep-alive',
    'DNT': '1',
    'Sec-GPC': '1',
}

mms_id_to_url = {}



def get_url(target_url):
    session = requests.session()

    # TO Request URL with SOCKS over TOR
    session.proxies = {}
    session.proxies['http']='socks5h://localhost:9050'
    session.proxies['https']='socks5h://localhost:9050'

    try:
        r = session.get(target_url, headers=headers, timeout=10.0)
        if len(mms_id_to_url) % 20 == 0:
            print("switching ips...")
            switch_ip()

        print(f'{len(mms_id_to_url)}: {r.status_code}: {r.url} -- {r.headers.get("content-type")}')
        mms_id_to_url.setdefault(current_id,[]).append({
            'given_url': target_url,
            'final_url': r.url,
            'type': r.headers.get("content-type"),
            'base_url': urllib.parse.urlsplit(r.url).netloc,
            'status_code': r.status_code
        })

        with open('result.json', 'w') as outfile:
            json.dump(mms_id_to_url, outfile, indent=2)



    except Exception as e:
        print(str(e))

def switch_ip():
    with Controller.from_port(port = 9051) as controller:
        controller.authenticate(password = 'PASSWORD_GOES_HERE')
        controller.signal(Signal.NEWNYM)
        time.sleep(controller.get_newnym_wait())

with open('rambi.csv', newline='') as csvfile:
     rambi_data = csv.reader(csvfile)
     current_id = None
     for row in rambi_data:
         id = current_id if row[0] == "" else row[0]
         current_id = id
         if row[1] != "":
             get_url(row[1])
