from sources.functions import *
import os
from bs4 import BeautifulSoup
import glob

class Siman:
    def __init__(self, siman, title, content, volume, file):
        self.siman = siman
        self.contents = [(title, content)]
        self.multiple_parts = False
        self.volume = volume
        self.files = [file]

    def addPart(self, title, content, f):
        if f in self.files:
            return
        else:
            self.files.append(f)
        self.contents.append((title, content))
        self.multiple_parts = True


    def __str__(self):
        return "{} parts in Siman {}".format(len(self.titles), self.siman)

if __name__ == "__main__":
    text = {}
    files = []
    for dir in os.listdir("."):
        if os.path.isdir(dir):
            files += [dir+"/"+f for f in list(os.walk(dir))[0][2]]
    for f in files:
        curr_dir = f.split("/")[0]
        if curr_dir not in text:
            text[curr_dir] = {}
        with open(f) as uziel_f:
            if f.endswith("txt") or "DS_S" in f:
                continue
            soup = BeautifulSoup(uziel_f.read(), parser='html')
            links = soup.find_all("a")
            title = soup.find("h1", {"class": "page-title"}).text
            assert title.startswith("סימן ")
            siman = getGematria(title.split()[1].split("-")[0])
            content = soup.find("div", {"class": "single-content"}).text
            content = [line for line in content.splitlines() if line]
            if siman in text[curr_dir]:
                existing_siman = text[curr_dir][siman]
                existing_siman.addPart(title, content, f)
            else:
                text[curr_dir][siman] = Siman(siman, title, content, curr_dir, f)

    multiple = []
    single = []
    for curr_dir in text:
        for siman in text[curr_dir]:
            siman_obj = text[curr_dir][siman]
            volume = siman_obj.volume
            new_dir = volume.split()[-1]
            if not os.path.exists(new_dir):
                os.mkdir(new_dir)
            siman_file = "{}/{}.txt".format(new_dir, siman)
            if not os.path.exists(siman_file):
                with open("{}/{}.txt".format(new_dir, siman), 'w') as f:
                    if siman_obj.multiple_parts:
                        print(siman_file)
                    if siman_obj.multiple_parts:
                        siman_obj.contents = sorted(siman_obj.contents, key=lambda x: getGematria(x[0].split()[2]))
                    for titles_and_contents in siman_obj.contents:
                        title, content = titles_and_contents
                        f.write("@"+title+"\n")
                        for line in content:
                            f.write(line+"\n")

