import requests

chumashim = ['01727', '01671', '01672', '01673', '01674']
for c, chumash in enumerate(chumashim):
    for i in range(2, 14):
        url = f'http://www.toratemetfreeware.com/online/f_{chumash}_part_{i}.html'
        req = requests.request('get', url)
        if req.status_code == 200:
            open(f'newdata/{c}-{i}.html', 'wb').write(req.content)
