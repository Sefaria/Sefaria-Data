from concurrent.futures import ThreadPoolExecutor
import requests
import re
import json

pids = ["IE20517548", "IE20521161", "IE20521681", "IE20507286", "IE20507394", "IE20507968", "IE20508777", "IE20508906", "IE20509400", "IE20509504", "IE20509955", "IE20511623", "IE20512082", "IE20513522", "IE20519139", "IE20519253", "IE20519328", "IE20519807", "IE20520847", "IE20522498", "IE20523637", "IE20524718", "IE20526197", "IE21062998", "IE21063209", "IE21064386", "IE21068578", "IE21072539"]



masekhet_index = None
file_index = None

def get_file_ids_for_mesekhet(pid):
    r = requests.get('https://bookreader.nli.org.il/NliBookViewer/?ie_pid='+pid)

    s = 'var fileArray = (\[\"FL.+\])'
    result = re.search(s, r.text)

    return(json.loads(result[1]))

def download_manuscript_file(fileid):
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:82.0) Gecko/20100101 Firefox/82.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'DNT': '1',
        'Sec-GPC': '1',
        'Cache-Control': 'max-age=0',
        'TE': 'Trailers',
    }

    params = (
        ('dps_func', 'stream'),
        ('dps_pid', fileid),
    )

    r = requests.get('https://rosetta.nli.org.il/delivery/DeliveryManagerServlet', headers=headers, params=params)

    file_index = new_file_ids.index(fileid)
    filename = (f'masekhet_{masekhet_index:02}_{file_index:04}.jpg')
    print(f'{pid}-{fileid}: written to: {filename}')
    open(filename, 'wb').write(r.content)


for pid in pids:
    new_file_ids = get_file_ids_for_mesekhet(pid)
    masekhet_index = pids.index(pid)


    with ThreadPoolExecutor() as executor:
        executor.map(download_manuscript_file, new_file_ids)
