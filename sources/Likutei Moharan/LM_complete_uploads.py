import pycurl
import cStringIO
import re
import sys
import json
import urllib
import urllib2
from urllib2 import URLError, HTTPError
from bs4 import BeautifulSoup

reload(sys)
sys.setdefaultencoding("utf-8")

def get_content_array(chapter_url):
    buf = cStringIO.StringIO()
    c = pycurl.Curl()
    c.setopt(c.URL, chapter_url)
    c.setopt(c.WRITEFUNCTION, buf.write)
    c.perform()
    content_array = []

    soup = BeautifulSoup(buf.getvalue(), 'html.parser', from_encoding="iso-8859-8")

    for child in soup.find("div", class_ = "entry-content" ).descendants:
        if unicode(child)[0] !="<" and unicode(child)[0] !="i" and len(unicode(child)) !=1:
            content_array.append(child)
            print "building..." + child[0:5]

    buf.close()
    return content_array[:-1];

    
def post_text(ref, text):
    textJSON = json.dumps(text)
    ref = ref.replace(" ", "_")
    url = 'http://localhost:8000/api/texts/%s' % ref
    values = {'json': textJSON, 'apikey': 'zR30KoOjZYcecN1CvrzjROLR85pWAhYXDZaAiBkOT5w'}
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    try:
        response = urllib2.urlopen(req)
        print response.read()
    except HTTPError, e:
        print 'Error code: ', e.code
        with open('error.html', "w") as error_file:
           error_file.write(e.read());

chapter_buf = cStringIO.StringIO()
c = pycurl.Curl()
c.setopt(c.URL, 'http://rabenubook.com/%D7%9C%D7%99%D7%A7%D7%95%D7%98%D7%99-%D7%9E%D7%95%D7%94%D7%A8%D7%B4%D7%9F-%D7%AA%D7%95%D7%9B%D7%9F-%D7%A2%D7%A0%D7%99%D7%99%D7%A0%D7%99%D7%9D/')

c.setopt(c.WRITEFUNCTION, chapter_buf.write)
c.perform()
soup = BeautifulSoup(chapter_buf.getvalue(), 'html.parser', from_encoding="iso-8859-8")

chapters =  soup.find(id="lcp_instance_0").find_all("a")

final_list = []
for index in range(len(chapters)):
    final_list.append(get_content_array(chapters[index]['href']))
    
upload_text = final_list

print "uploading..."

text_version = {
    'versionTitle': "Likutei Moharan - rabenubook.com",
    'versionSource': "http://rabenubook.com/%D7%9C%D7%99%D7%A7%D7%95%D7%98%D7%99-%D7%9E%D7%95%D7%94%D7%A8%D7%B4%D7%9F-%D7%90/",
    'language': 'he',
    'text': upload_text
}

post_text("Likutei Moharan", text_version)


chapter_buf.close()