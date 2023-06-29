from sources.functions import *
chrome = "/Users/stevenkaplan/Documents/chromedriver"
def get_lines(perek):
    lines = perek.split("<br>")
    if lines[0].startswith("פרק "):
        lines = lines[1:]
    mishnah = ""
    lines = [x.strip() for x in lines if len(x.strip()) > 0]
    for l, line in enumerate(lines):
        if line.startswith('משנה ') and line.count(" ") == 1:
            mishnah = line.split()[1]
            lines[l] = mishnah
        elif line.count(" ") == 0:
            if getGematria(line) - getGematria(mishnah) == 1:
                mishnah = line
            elif getGematria(line) - getGematria(mishnah) == 0:
                lines[l] = ""
    return [x.strip() for x in lines if len(x.strip()) > 0]

def bleach_it(element, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS):
    return bleach.clean(str(element), tags=tags, attributes=attributes, strip=True).replace("  ", " ").strip()

#
# url = 'https://he.wikisource.org/wiki/%D7%9E%D7%A9%D7%A0%D7%94_%D7%9E%D7%A0%D7%95%D7%A7%D7%93%D7%AA_%D7%95%D7%9E%D7%A2%D7%95%D7%A6%D7%91%D7%AA'
# def wiki(vsource, founders=True):
#     soup = BeautifulSoup(selenium_get_url(chrome, vsource))
#     if founders:
#         [x.decompose() for x in soup.find_all("a")]
#         contents = soup.find("div", {"id": "pageContainer"}).contents
#     else:
#         contents = soup.find_all('p')
#     return [bleach_it(x) for x in contents if bleach_it(x).strip() != ""]
#
# soup = BeautifulSoup(selenium_get_url(chrome, url))
# el = soup.find('div', {'class': 'mw-parser-output'})
# results = [bleach_it(x) for x in el.contents if bleach_it(x).strip() != ""]
# links = [x.find_all('a') for x in soup.find_all('tr')]
# for k in links:
#     for l in [a for a in k if a and a.attrs['href'].startswith("/wiki")]:
#         href = l['href'].replace("/wiki/", "")
#         soup = BeautifulSoup(selenium_get_url(chrome, 'https://he.wikisource.org/'+l['href'], name=href))
files = os.listdir(".")
for f in files:
    if f.endswith(".html"):
        print(f)
        with open(f) as file:
            soup = BeautifulSoup(file)
            y = soup.find("div", {"class": "mw-parser-output"})
            results = ([bleach_it(x) for x in y.find_all('p') if bleach_it(x).strip() != ""])
            try:
                temp = BeautifulSoup(results[0]).find('a').text[5:-1].replace('בכורים', 'ביכורים')
                masechet = Ref(temp).index
            except:
                continue
            if "Talmud" in masechet.categories:
                masechet = "Mishnah "+masechet.title
            else:
                masechet = masechet.title
            should_have_chapters = library.get_index(masechet).all_section_refs()
            actual_chapters = results[3:]
            text = {}
            if len(should_have_chapters) == len(actual_chapters):
                for p, perek in enumerate(actual_chapters):
                    text[p] = []
                    lines = get_lines(perek)
                    mishnah = 0
                    for l, line in enumerate(lines):
                        line = line.strip().replace('&gt;', '>').replace('&lt;', '<')
                        if len(line) == 0:
                            pass
                        elif getGematria(line) - mishnah in list(range(0, 20)):
                            mishnah += 1
                            if len(text[p]) > 0 and text[p][-1] == "":
                                pass
                            else:
                                text[p].append("")
                        else:
                            text[p][-1] += line + " "
                        text[p][-1] = text[p][-1].replace("  ", " ")
                    diff = len(text[p]) - len(Ref(f"{masechet} {p+1}").all_segment_refs())
                    if diff != 0:
                        print(f"Be'eri {masechet} {p+1} is longer by {diff}")
            else:
                assert 3 == 4
                print(f"Problem with {masechet}")