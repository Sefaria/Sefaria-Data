import os
import pandas as pd

ry, rsby, tk = 0, 0, 0
for fname in os.listdir('csvs'):
    df = pd.read_csv(f'csvs/{fname}')
    for index, row in df.iterrows():
        tana = row["ספ' תנאים"]
        if pd.isna(tana):
            continue
        if any(word in tana for word in ["ספ'", 'ספרא', 'ת"כ']):
            tk+=1
        if any(word in tana for word in ["מכילתא", 'מדר"י', 'מכדר"י']):
            ry+=1
        if any(word in tana for word in ['מדרשב"י', 'מכדרשב"י']):
            rsby+=1
print(tk, rsby, ry)
