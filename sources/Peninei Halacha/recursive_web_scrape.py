from bs4 import BeautifulSoup
import requests

seen = []

def crawler(url, depth):
    if depth == 0:
        return None

    try:
        html = requests.get(url).text                  # You were missing
    except:
        return None

    soup = BeautifulSoup(html, 'lxml')  # these lines.

    links = soup.findAll("a")

    links2 = []
    for link in links:
        if link.has_attr("href") and "https://ph.yhb.org.il/" in link["href"] and len(link["href"]) < 50 and \
                "plus" not in link["href"] and link["href"] not in seen and "fr" not in link["href"] and \
                "es" not in link["href"] and "ru" not in link["href"]:
            links2.append(link)
            seen.append(link["href"])

    print("Level ", depth, url)
    for link in links2:
        crawler(link['href'], depth - 1)


url = "https://ph.yhb.org.il/10-01-01"
crawler(url,10)
