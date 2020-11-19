from sources.functions import *
from seleniumrequests import Firefox
from bs4 import BeautifulSoup
from random import shuffle, randint
import requests
import time
import os

links = ["http://haravuziel.org.il/category/%d7%a1%d7%a4%d7%a8%d7%99%d7%9d/%d7%a9%d7%95%d7%aa-%d7%9e%d7%a9%d7%a4%d7%98%d7%99-%d7%a2%d7%95%d7%96%d7%99%d7%90%d7%9c-%d7%97%d7%9c%d7%a7-%d7%94/",
         "http://haravuziel.org.il/category/%d7%a1%d7%a4%d7%a8%d7%99%d7%9d/%d7%a9%d7%95%d7%aa-%d7%9e%d7%a9%d7%a4%d7%98%d7%99-%d7%a2%d7%95%d7%96%d7%99%d7%90%d7%9c-%d7%97%d7%9c%d7%a7-%d7%98/%d7%99%d7%95%d7%a8%d7%94-%d7%93%d7%a2%d7%94-%d7%a9%d7%95%d7%aa-%d7%9e%d7%a9%d7%a4%d7%98%d7%99-%d7%a2%d7%95%d7%96%d7%99%d7%90%d7%9c-%d7%97%d7%9c%d7%a7-%d7%98/",
         "http://haravuziel.org.il/category/%d7%a1%d7%a4%d7%a8%d7%99%d7%9d/%d7%a9%d7%95%d7%aa-%d7%9e%d7%a9%d7%a4%d7%98%d7%99-%d7%a2%d7%95%d7%96%d7%99%d7%90%d7%9c-%d7%97%d7%9c%d7%a7-%d7%97/",
         "http://haravuziel.org.il/category/%d7%a1%d7%a4%d7%a8%d7%99%d7%9d/%d7%a9%d7%95%d7%aa-%d7%9e%d7%a9%d7%a4%d7%98%d7%99-%d7%a2%d7%95%d7%96%d7%99%d7%90%d7%9c-%d7%97%d7%9c%d7%a7-%d7%96/"]
for link in links:
    print(link)
    for each_link in [link + "/page/2", link]:
        response = requests.get(each_link, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content)
            dir = soup.find("h2", {"class": "booksTitle"}).text
            if not os.path.exists(dir):
                os.mkdir(dir)
            simanim = [a.attrs["href"] for a in soup.find_all("a") if a.text.startswith("סימן")]
            shuffle(simanim)
            for siman in simanim:
                siman_file_name = siman.split("/")[-2]
                if not os.path.exists(dir+"/"+siman_file_name):
                    time.sleep(randint(1, 3))
                    response = requests.get(siman, headers=headers)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content)
                        with open(dir+"/"+siman_file_name, 'w') as f:
                            f.write(str(soup))
                            print("SUCCESS")
                    else:
                        print(siman)
                        print(response)

        else:
            print(link)
            print(response)