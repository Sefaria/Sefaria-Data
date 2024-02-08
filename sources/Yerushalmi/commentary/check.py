import os
import csv

def check(root, fname):
    n, y = 0, 0
    with open(f'{root}/{fname}', encoding='utf-8', newline='') as fp:
        for row in csv.DictReader(fp):
            if row['base text ref']:
                y += 1
            else:
                n += 1
    return y / (y+n)

if __name__ == '__main__':
    '''root = 'csvs/Amudei Yerushalayim'
    for fname in os.listdir(root):
        print(fname)
        print(check(root, fname))'''
    for fol in os.listdir('csvs'):
        print(fol)
        x=0
        for fname in os.listdir(f'csvs/{fol}'):
           x+= check(f'csvs/{fol}', fname)
        print(x/len(os.listdir(f'csvs/{fol}')))
