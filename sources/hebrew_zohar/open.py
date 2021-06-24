for i in range(8):
    with open(f'000023_ZOHAR-VETARGUM-{i}.txt', encoding='Windows-1255') as fp:
        data=fp.read()
    with open(f'zoher{i}', 'w', encoding='utf-8') as fp:
        fp.write(data)