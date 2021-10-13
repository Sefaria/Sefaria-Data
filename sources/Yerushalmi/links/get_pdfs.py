import requests
import re

toc = requests.request('get', 'https://web.archive.org/web/20170610134330/http://www.biu.ac.il/js/tl/yerushalmi/records.html')
if toc.status_code != 200:
    print('error getting toc')
else:
    toc = toc.content
    folder = b'https://web.archive.org/web/20170610134330/http://www.biu.ac.il/js/tl/yerushalmi/files/'
    for fname in re.findall(b'files/(.*?)"', toc):
        url = folder + fname
        pdf = requests.request('get', url)
        if pdf.status_code != 200:
            print('error getting', url)
        else:
            fname = fname.decode('UTF-8')
            with open(f'pdfs/{fname}', 'wb') as fp:
                fp.write(pdf.content)
