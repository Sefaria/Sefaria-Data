import requests

cookies = {
    'local-cookie': '/0C4zUVv2wvjKpnu1h/OD04y0Ex+3VfvdsBYKmJn8hjU3wZUsoMHfv4TmSmOwC8/DiXFX57u4FMAQosTGbOtm/7HJAfLNESn8HOGJeI8hXkvDqMJ7QWbrPRCvCYTRq40OZrMs1rxHAgb0Z3KDmR7MRTGuxTidT3fNoo8QzdsSCyKNXnvSSX2K+yodIAHHtMyT3okp21N9VF2EP4lxDEnG2kcqkKssudctOQFIWasmMsqnWBl22ZjCEk5uha7jk/m',
    '_culture': '',
    'ASP.NET_SessionId': 'imr3fry0vapfhttggsrwtaxz',
    'ExternalReferrer': 'https://biblia.com/books/bdb/article/LBDB.5.11?contentType=xhtml',
    'Session': '07/25/2022 11:59:35',
}

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    # 'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    # Requests sorts cookies= alphabetically
    # 'Cookie': 'local-cookie=/0C4zUVv2wvjKpnu1h/OD04y0Ex+3VfvdsBYKmJn8hjU3wZUsoMHfv4TmSmOwC8/DiXFX57u4FMAQosTGbOtm/7HJAfLNESn8HOGJeI8hXkvDqMJ7QWbrPRCvCYTRq40OZrMs1rxHAgb0Z3KDmR7MRTGuxTidT3fNoo8QzdsSCyKNXnvSSX2K+yodIAHHtMyT3okp21N9VF2EP4lxDEnG2kcqkKssudctOQFIWasmMsqnWBl22ZjCEk5uha7jk/m; _culture=; ASP.NET_SessionId=imr3fry0vapfhttggsrwtaxz; ExternalReferrer=https://biblia.com/books/bdb/article/LBDB.5.11?contentType=xhtml; Session=07/25/2022 11:59:35',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'cross-site',
    'Sec-GPC': '1',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
}

params = {
    'contentType': 'xhtml',
}

for i in range(1, 2542):
    for j in range(1000):
        response = requests.get(f'https://biblia.com/books/bdb/article/LBDB.{i}.{j}', params=params, cookies=cookies, headers=headers)
        if response.status_code == 404:
            break
        print(i,j)
        if response.status_code != 200:
            print(response.status_code)
        with open(f'biblia/{i}:{j}.html', 'w', encoding='utf-8') as fp:
            fp.write(response.text)
