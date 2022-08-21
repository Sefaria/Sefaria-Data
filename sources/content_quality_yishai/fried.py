import requests
import json
import time

#   using guide
# sign in to friedberg and go to the first image that needed
# open dev tools, network tab and copy as cURL the request
# there the cookies details and ImageFileDetailsId can be found
# generally, the ImageFileDetailsId is running with the pages, so the range can be calculated
# but there are exceptional, so checking the last image seems to be a good practice


masechtot = {
    'shabbat': [5430, 5433],
    'chullin': [11722, 11723],
    'sukkah': [15445, 15445],
    'sukkah2': [15453, 15453]
}

for masechet in masechtot:
    current_id = masechtot[masechet][0]
    ending_id = masechtot[masechet][1]

    while current_id <= ending_id:
        print(f'Downloading {masechet}_{current_id:04}.jpg')

        # We need to spoof the cookies and the headers in order for the site to let us in. These are now obviously stale, so you'd
        # Need to login again w/ a legitimate login/pw and then copy one of the requests in the network panel of the dev tools and
        # extract the required variables

        cookies = {
            'ASP.NET_SessionId': 'uem2bzqvz12ghbstigktq2s4',
            'LPVID': 'I3YTAxM2EwOGFiZTMxNWM2',
            'LPSID-91630553': 'Nsug4YNnRlyIXqkuBW4qEQ',
            '.ASPXAUTH': '4265120AC275C0AB09ED85E2F44EFA42C782CF63CDEA456AEDACA0B52F909F79B566A70A08861949733126AC0F869EBDE775297DFAB318883FC0AFE52373AC6F5BA133AF2E74D7E8A642B3B27CA6607529A85D6668E0B1E152850026D5D72371',
            'selLang': 'heb',
        }

        # these probably don't need to change
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:84.0) Gecko/20100101 Firefox/84.0',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.5',
            'X-Requested-With': 'XMLHttpRequest',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Referer': 'https://bavli.genizah.org/ResultPages/Display',
            'Sec-GPC': '1',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
        }

        params = (
            ('ImageFileDetailsId', f'{current_id}'),
        )

        # Two API calls are required -- the first to get the file id -- and the second to download it...

        api_response = requests.get('https://bavli.genizah.org/api/FileByIDAPI/GetGuidByFile', headers=headers,
                                    params=params, cookies=cookies)
        guidNumber = (json.loads(api_response.text)["Data"][0])

        params = (
            ('guidNumber', guidNumber),
            ('TypeOfImage', 'RegularImage'),
            ('delayFinalProc', 'false'),
        )

        r = requests.get('https://bavli.genizah.org/api/FileByIDAPI/GetFilePathByGuid', headers=headers, params=params,
                         cookies=cookies)

        filename = (f'{masechet}_{current_id:04}.jpg')
        open(filename, 'wb').write(r.content)

        current_id = current_id + 1