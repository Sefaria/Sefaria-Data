from sources.Kereti.i_tags import *

if __name__ == "__main__":
    title = "Chiddushei Hilkhot Niddah"
    default = "Ashlei Ravrevei: Shulchan Aruch Yoreh Deah, Lemberg, 1888"
    tiferet = get_kereti_dhs_in_mechaber(["Tiferet Yisrael/Base Text.txt"])

    all_dhs = get_kereti_tags(title, tiferet)
    #create_new_tags("", default, all_dhs, change_nothing=True)
    create_new_tags("CHIDDUSHEI", default, all_dhs, change_nothing=False)