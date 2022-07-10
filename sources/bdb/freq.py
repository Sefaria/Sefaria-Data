import json
import re
from bs4 import BeautifulSoup

freq = {}
for i in range(1, 8675):
    try:
        with open(f'biblehub/{i}.html') as fp:
            hub = BeautifulSoup(fp.read(), 'html.parser')
    except FileNotFoundError:
        continue
    for word in hub.text.split():
        word = re.sub(r'[^A-Za-zא-ת]', '', word)
        if len(word) < 2:
            continue
        try:
            freq[word] += 1
        except KeyError:
            freq[word] = 1

print(sorted(freq, key=lambda x: freq[x])[:50])

with open('freq.json', 'w', encoding='utf-8') as fp:
    json.dump(freq, fp, ensure_ascii=False)
