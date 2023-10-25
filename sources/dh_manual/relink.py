import pandas as pd
import django
django.setup()
from sefaria.model import *

X = Y = 0
C, D = {}, {}

def relink(book, df):
    global X, Y, C, D
    links = Ref(book).linkset()
    X += len(links)
    print(f'deleting {len(links)} of {book}')
    for l in links:
        if l.type == 'commentary':
            C[[r for r in l.refs if 'Ritva' in r][0]] = [r for r in l.refs if 'Ritva' not in r][0]
            l.delete()
    library.get_index(book).versionState().refresh()
    df = df.reset_index()
    df = df.where(pd.notnull(df), None)
    old = ''
    links = []
    for index, row in df.iterrows():
        ref, bref = row['ref'], row['base ref']
        if not bref:
            daf = ref.split('on ')[1].split(':')[0]
            if daf in old:
                bref = old
            else:
                bref = ''
        old = bref
        links.append(Link({'refs': [ref, bref],
                     'auto': True,
                     'type': 'commentary',
                     'generated_by': 'new ritva linker'}))

    Y += len(links)
    while links:
        link = links.pop()
        if not link.refs[1]:
            if old.endswith(':1'):
                link.refs[1] = old
            else:
                link.refs[1] = ':1-'.join(old.split(':'))
        else:
            old = link.refs[1]

        D[link.refs[0]] = link.refs[1]

        link.save()

if __name__ == '__main__':
    books = library.get_indices_by_collective_title('Ritva')
    for book in books:
        try:
            df = pd.read_excel(f'data/{book}.xlsx')
            relink(book, df)
        except FileNotFoundError:
            print(book)
            pass
    print(X, 'old links')
    print(Y, 'new links')

    a = 0
    for k in C:
        if k not in D or C[k] != D[k]:
            a+=1
    print(a, 'wrong old links')
