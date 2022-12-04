import re
import json

def vide_split(text):
    entries = []
    if len(re.findall('(?:^| )v\.(?: |$)', text)) > 1 and len(text.split()) < 23:
        if any(w in text for w in ['סִרָה', 'רָפָה', 'בְּרִית']):
            return
        try:
            text = text.strip()
            if not text.endswith('.'):
                text += '.'
            while text:
                ent = re.findall('((?:.(?! v\. ))*. v\.(?:.(?! v\. ))*[\.,;])(?:.*? v\.|.*$)', text)[0].strip()
                if ent[-1] in [',;']:
                    ent = ent[:-1] + '.'
                if ent[-2] in [',;']:
                    ent = ent[:-2] + '.'
                entries.append(ent)
                text2 = re.sub(f'^{re.escape(ent)}', '', text).strip()
                if text2 == text:
                    return
                text = text2
        except:
            return entries
        return entries

if __name__ == '__main__':
    with open('hub_dict_final.json') as fp:
        hubd = json.load(fp)
    report = []
    for h in hubd:
        if 'text' in hubd[h]:
            entries = vide_split(hubd[h]['text'])
            if entries != None:
                report.append(hubd[h]['text'])
                report += entries
                report.append('')
    with open('vide split report.txt', 'w', encoding='utf-8') as fp:
        fp.write('\n'.join(report))
