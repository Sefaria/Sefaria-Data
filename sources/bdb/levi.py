from bs4 import BeautifulSoup
import os
import re

path = '/home/yishai/sefaria/dict/BDB/data/eric_levy'
files = os.listdir(path)

entries = []
first_style = lambda x: int(x.span.attrs['id'].replace('textStyle', ''))
cross = lambda x: x.span.text == ''
twot = lambda x: ' TWOT' in x.text
gk = lambda x: ' GK' in x.text
only_heb = lambda x: all(ord(letter) in range(1425, 1525) or letter in ['\x98', ' '] for letter in x.text)
first_only_heb = lambda x: only_heb(x.span.text)

def heb_after_sign(e):
    sup = False
    if e.contents[0].name == 'sup' and e.sup == '':
        sup = True
    e = e.span
    signs = [r'I{1,3}V?\.', '', r'I{1,3}V?\. \[', 'I{1,3}V?', r'\.', r'\. \[', r'\[', '. &', '\.\[']
    if not sup and not any(re.search(f'^ *{s} *$', e.text) for s in signs):
        return
    while any(re.search(f'^ *{s} *$', e.text) for s in signs):
        e = e.find_next_sibling('span')
        if not e:
            return
    if only_heb(e):
        return True

start_styles = {1: [0, 2, 5]}
start_styles[2] = [0, 23]
start_styles[3] = [0, 5]

for i in range(1,4):
    print(i)
    file = [f for f in files if f.startswith(f'{i}_')][0]
    with open(f'{path}/{file}') as fp:
        soup = BeautifulSoup(fp.read(), 'html.parser')

    for child in soup.children:
        if child == '\n':
            continue
        if first_style(child) in start_styles[i] or heb_after_sign(child):
            entries.append(child)

print(entries[1847])
print(len(entries))
