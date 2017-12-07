from sources.Shulchan_Arukh.ShulchanArukh import *

def generic_cleaner(ja, clean):
    for i, siman in enumerate(ja):
        for j, seif in enumerate(siman):
            ja[i][j] = clean(seif)
    return ja

def taz_clean(ja):
    def clean(str):
        replacements = [u"\(#\)", u"#\)", u"\[#\]", u"#\]"] #References to Levushei HaSrad
        for r in replacements:
            str = re.sub(r, u"", str)
        return str.replace(u"?", u"").replace(u"%%%", u"%")
    return generic_cleaner(ja, clean)

def eshel_clean(ja):
    def clean(str):
        return str.replace(u"?", u"")
    return generic_cleaner(ja, clean)

def chok_clean(ja):
    def clean(str):
        return str.replace(u"?", u"")
    return generic_cleaner(ja, clean)

def ateret_clean(ja):
    def clean(str):
        str = str.replace(u"?", u"")
        return str
    return generic_cleaner(ja, clean)

def check_marks(comm, clean):
    all_finds = {}
    commentary_text = comm.render()
    for volume in comm:
        volume_text = volume.render()
        volume_text = clean(volume_text)
        finds = []
        for siman_text in volume_text:
            for seif_text in siman_text:
                finds += re.findall(u"[^\s\u05d0-\u05ea\'\"\.\:,;\)\(\]\[]{1,7}", seif_text)
        if len(finds) > 0:
            for el in finds:
                if el not in all_finds.keys():
                    all_finds[el] = 0
                all_finds[el] += 1
    for key, value in all_finds.items():
        print u"{} -> {} occurrences".format(key, value)
    return volume_text


if __name__ == "__main__":
    root = Root('../../Orach_Chaim.xml')
    commentaries = root.get_commentaries()
    post_parse = {
                 u"Taz on Shulchan Arukh, Orach Chaim": taz_clean,
                 u"Eshel Avraham on Shulchan Arukh, Orach Chaim": eshel_clean,
                 u"Ateret Zekenim on Shulchan Arukh, Orach Chaim": ateret_clean,
                 u"Chok Yaakov on Shulchan Arukh, Orach Chaim": chok_clean
    }
    for title, clean_func in post_parse.items():
        print
        print title
        comm = commentaries.get_commentary_by_title(title.split(" on")[0])
        comm = check_marks(comm, clean_func)
        pass



