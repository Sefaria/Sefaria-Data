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
            print "child " + child

    buf.close()
    return content_array[:-1];

def get_JSON_text(paragraph_array):
    return_text = "["
    for index in range(0,len(paragraph_array)-2):
        return_text+=" '"+paragraph_array[index]+"',"
    #so there's no "," after last element
    return_text+=" '"+paragraph_array[len(paragraph_array)-1]+"']"
    return return_text;
    
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
        print e.read();

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
    
#upload_text = "{["
#for index in range(0,len(final_list)-2):
#    upload_text+= get_JSON_text(final_list[index])+","
#upload_text+= get_JSON_text(final_list[len(final_list)-1])
#upload_text+= "]}"
upload_text = json.dumps(final_list)

print upload_text

text_version = {
    'versionTitle': "Likutei Moharan - rabenubook.com",
    'versionSource': "http://rabenubook.com/%D7%9C%D7%99%D7%A7%D7%95%D7%98%D7%99-%D7%9E%D7%95%D7%94%D7%A8%D7%B4%D7%9F-%D7%90/",
    'language': 'he',
    'text': upload_text
}

post_text("Likutei Moharan", upload_text)


chapter_buf.close()