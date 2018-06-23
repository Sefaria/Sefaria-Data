import json, codecs
from sefaria.model import *

test_refs = ["Mishnah Berakhot 3:1", "Mishnah Shabbat 8:4", "Mishnah Negaim 7:4",
             "Mekhilta d'Rabbi Yishmael 12:30:1", "Sifra, Vayikra Dibbura d'Nedavah, Chapter 13:1", "Sifrei Bamidbar 137:2",
             "Bereishit Rabbah 23:1", "Derech Eretz Zuta 2:1", "Otzar Midrashim, Avraham our Father, The_Legend of Avraham 3",
             "Sefer Mitzvot Gadol, Volume Two 76:1",
             "Rashi on Genesis 1:1:1", "Rashi on Leviticus 11:2:3", "Rashi on Numbers 13:2:2",
             "Ramban on Numbers 13:4:1", "Ramban on Exodus 30:23:2", "Ramban on Genesis 6:6:1",
             "Mishneh Torah, Transmission of the Oral Law 7", "Mishneh Torah, Human Dispositions 4:2", "Mishneh Torah, Marriage 1:1",
             "Beit Yosef, Orach Chaim 37:3:1",
             "Yachin on Mishnah Berakhot 1:1:1", "Yachin on Mishnah Eruvin 5:8:1", "Yachin on Mishnah Zavim 1:4:1",
             "Bartenura on Mishnah Kilayim 1:1:2", "Bartenura on Mishnah Menachot 1:2:9", "Bartenura on Mishnah Makhshirin 1:1:3"]


out = []
for rt in test_refs:
    ro = Ref(rt)
    text = TextChunk(ro,lang="he").text
    assert isinstance(text, unicode)
    out += [{
        "ref": rt,
        "text": text
    }]

json.dump(out, codecs.open('test_dictionary_text.json','wb', encoding='utf8'), indent=4, ensure_ascii=False)
#objStr = json.dumps(out, indent=4, ensure_ascii=False)
#with open('test_dictionary_text.json', "wb") as f:
#    f.write(objStr.encode('utf-8'))
