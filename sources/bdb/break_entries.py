import srsly

all = set()
data = srsly.read_jsonl('doc_evaluation.jsonl')
for doc in data:
    text = doc['text']
    breaks = [text[a:b] for a, b, _ in doc['fp']]
    all |= set(breaks)

print('\n'.join(all))
