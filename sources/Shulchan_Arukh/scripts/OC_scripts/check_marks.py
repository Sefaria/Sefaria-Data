from sources.Shulchan_Arukh.ShulchanArukh import *
def check_marks(comm):
    all_finds = {}
    for volume in comm:
        for siman in volume:
            for seif in siman:
                seif_text = seif.render()
                replacements = [u"\(#\)", u"#\)", u"\[#\]", u"#\]"]
                for r in replacements:
                    seif_text = re.sub(r, u"", seif_text)
                finds = re.findall(u"[^\s\u05d0-\u05ea\'\"\.\*\:,;\)\(\]\[]{1,7}", seif_text)
                if len(finds) > 0:
                    for el in finds:
                        if el not in all_finds.keys():
                            all_finds[el] = 0
                        all_finds[el] += 1
        print "\nVolume {}".format(volume.num)
        for key, value in all_finds.items():
            print u"{} -> {} occurrences".format(key, value)

if __name__ == "__main__":
    root = Root('../../Orach_Chaim.xml')
    commentaries = root.get_commentaries()
    titles_of_comms = ["Taz", "Eshel Avraham", "Ateret Zekenim", "Chok Yaakov"]
    for title in titles_of_comms:
        print title
        comm = commentaries.get_commentary_by_title(title)
        check_marks(comm)


