import django
django.setup()
from sefaria.model import *
from sefaria.system.database import *
import regex as re


#after changing many titles in the library using index_all_3.py this script came to return the old spellings as alt_titles on the indexes for the sake of 301 redirex

# ind = library.get_index(new_title)
# added = ind.nodes.title_group.add_title(old_title, 'en')
# if added:
#     print(f"added {old_title} to index {ind.title}")
# ind.save()
# ind.versionState().refresh()
# q = {"base_text_titles": {"$regex": f".*{new_title}.*"}}

def add_old_alt_title(old_title, new_title):
    cnt = 0
    q = {"title": {"$regex": f".*{new_title}.*"}}
    cursor = db.index.find(q)
    for comm in cursor:
        comm_ind = library.get_index(comm['title'])
        comm_titles = comm_ind.nodes.title_group.titles
        for t in comm_titles:
            if t['lang']=='en' and re.search(new_title, t['text']):
                old_comm_title = t["text"].replace(new_title, old_title)
                added = comm_ind.nodes.title_group.add_title(old_comm_title, 'en')
                if added:
                    print(f"added {old_comm_title} to index {comm_ind.title}")
                    cnt+=1
        comm_ind.save()
        comm_ind.versionState().refresh()
    print(cnt)
    return cnt

if __name__ == '__main__':
    paired_names = [('Halacha and Aggadah', 'Halakhah and Aggadah'),
 ('Derech Chaim', 'Derekh Chayim'),
 ('Maaneh Lashon Chabad', "Ma'aneh Lashon Chabad"),
 ('Minhat Kenaot', 'Minchat Kenaot'),
 ('Derech Hashem', 'Derekh HaShem'),
 ('Shmonah Kvatzim', 'Shemonah Kevatzim'),
 ('Pri Haaretz', 'Pri HaAretz'),
 ('Sefer HaMidot', 'Sefer HaMiddot'),
 ("Shaar HaEmunah Ve'Yesod HaChassidut", "Sha'ar HaEmunah VeYesod HaChasidut"),
 ('Mahberet Menachem', 'Machberet Menachem'),
 ('Sefer haBachur', 'Sefer HaBachur'),
 ('Meshech Chochma', 'Meshekh Chokhmah'),
 ('Tur HaAroch', 'Tur HaArokh'),
 ('Likutei Halachot', 'Likutei Halakhot'),
 ('Darchei HaTalmud', 'Darkhei HaTalmud'),
('Pithei Teshuva', 'Pitchei Teshuva'),
('Kitzur Baal Haturim', 'Kitzur Baal HaTurim'),
('Melechet Shlomo', 'Melekhet Shelomoh'),
('Maharam Shif', 'Maharam Schiff')]
    cnt = 0
    for pair in paired_names:
        cnt += add_old_alt_title(pair[0], pair[1])
    print(f'# of all titles added to the library: {cnt}')
