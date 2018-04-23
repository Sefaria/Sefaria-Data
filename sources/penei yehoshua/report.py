#encoding=utf-8
from sefaria.model import *
from sefaria import system
from sources.functions import *
import csv
import os

class MaharshaLite:
    def __init__(self, book):
        self.book = book
        self.len_masechet = len(book.all_section_refs()) #how many sections in book
        self.current_daf = 3
        self.category = "gemara"
        self.rashi ='רש"י'
        self.rashbam = 'פרשב"ם'
        self.ran = 'ר"ן'
        self.rosh = 'רא"ש'
        self.tosafot = "תוס"
        self.dibbur_hamatchil = ['בד"ה', 'ד"ה', 'בא"ד', """ד'"ה"""]
        self.gemara = "גמ"
        self.shom = "שם"
        self.amud_bet = 'ע"ב'
        self.mishnah = ['במשנה', 'מתני']
        self.categories = ['rashi', 'tosafot', 'gemara', 'ran', 'rosh', 'rashbam']
        self.dh_by_cat = {cat: {self.current_daf: []} for cat in self.categories}
        self.comm_dict = {self.current_daf: []}
        self.list_of_dafs = []

    def determineCategory(self, comment):
        word = comment.split(" ")[0] if comment.split(" ")[0] != " " else comment.split(" ")[1]
        if self.rashi in word:
            self.category = 'rashi'
        elif self.tosafot in word:
            self.category = 'tosafot'
        elif self.gemara in word or word in self.mishnah:
            self.category = 'gemara'
        elif self.ran in word:
            self.category = 'ran'
        elif self.rosh in word:
            self.category = 'rosh'
        elif self.rashbam in word:
            self.category = "rashbam"
        elif word == 'בא"ד' or word == 'עוד בדבור זה':
            return "same_dh"
        return None

    # def get_alephs_bets(file):
    #     lines = " ".join(list(file))
    #     dappim = []
    #     aleph = "@11דף@22"
    #     bet = '@11ע"ב'
    #     how_many_alephs = len(lines.split(aleph)) - 1
    #     how_many_bets = len(lines.split(bet)) - 1
    #     return how_many_alephs, how_many_bets


    def get_dh(line):
        first_12_words = " ".join(line.split(" ")[0:12])
        chulay = u"כו'"
        if chulay in first_12_words:
            dh, comment = line.split(chulay, 1)
            dh += u" "+chulay

    def parseDH(self, comment, category, same_dh):
        orig_comment = comment
        if same_dh is None:
            first_15_words = " ".join(comment.split(" ")[0:15])
            chulay = first_15_words.find("כו'")
            first_period = first_15_words.find(".")
            if chulay > 0:
                dh, comment = comment[0:chulay+5], comment[chulay+6:]
            elif first_period:
                dh, comment = comment[0:first_period+1], comment[first_period+1:]
                comment = comment[1:] if comment[0] == " " else comment
            else:
                print "Segment has no DH"
            self.prev_dh = dh
            self.addDHComment(dh, comment, category, same_dh)
        else:
            self.addDHComment(self.prev_dh, comment, category, same_dh)

    def getDaf(self, line, len_masechet):
        prev_num = self.current_daf
        orig_line = line
        line = line.replace("@11 ", "@11")
        if line.split(" ")[0].find('דף')>=0:
            daf_value = getGematria(line.split(" ")[1].replace('"', '').replace("'", ''))
            if line.split(" ")[2].find(self.amud_bet)>=0:
                self.current_daf = 2*daf_value
            else:
                self.current_daf = 2*daf_value - 1
            actual_text = ""
            start_at = 3
            if line.split(" ")[2] not in ['ע"ב', 'ע"א']:
                start_at = 2
            for count, word in enumerate(line.split(" ")):
                if count >= start_at:
                    actual_text += word + " "
        else:
            self.current_daf += 1
            actual_text = line[3:]

        if self.current_daf <= prev_num:
            he_current = AddressTalmud.toStr("he", self.current_daf)
            he_prev = AddressTalmud.toStr("he", prev_num)
            #prev_line = " ".join(prev_line.split(" ")[0:5])
            #orig_line = " ".join(orig_line.split(" ")[0:5])
            print u"{} before {}\n".format(he_prev, he_current)
            self.dont_post = True
            #print u"The line starting: {} is {}\n".format(prev_line, he_prev)
            #print u"It came before the line starting {}, which is {}\n\n".format(orig_line, he_current)


        self.actual_text = actual_text
        if self.current_daf > len_masechet:
            print "DAF EXTRA {} > {} in {} {}".format(self.current_daf, len_masechet, self.title, self.masechet)
            pass
        self.list_of_dafs.append(self.current_daf)

        if not self.current_daf in self.comm_dict:
            self.comm_dict[self.current_daf] = []
            self.dh_by_cat[self.category][self.current_daf] = []

        return self.current_daf

    def addDHComment(self, dh, comment, category, same_dh):
        dh = removeAllTags(dh)
        comment = removeAllTags(comment)
        dh = dh.decode('utf-8')
        comment = comment.decode('utf-8')
        #self.dh1_dict[self.current_daf].append((category, dh))
        if same_dh:
            post_comment = comment
        else:
            post_comment = dh + comment

        post_comment = post_comment.strip()
        first_word = post_comment.split(" ")[0]
        post_comment = u"<b>{}</b> {}".format(first_word, " ".join(post_comment.split(" ")[1:]))
        self.comm_dict[self.current_daf].append(post_comment)
        self.dh_by_cat[category][self.current_daf].append(dh)


    def parse(self, lines):
        for line in lines:
            if line.startswith("@11") and " " in line: #second check to make sure this isn't a perek header
                self.getDaf(line, self.len_masechet)
                aleph = "@11דף@22"
                bet = '@11ע"ב'

                same_dh = self.determineCategory(line)
                self.parseDH(line, self.category, same_dh)




if __name__ == "__main__":
    files = [f for f in os.listdir(".") if f.endswith(".txt")]
    for file in files:
        title = file[0:-4]
        try: #the try except clause allows us to test that book exists and isn't one of the commentaries that we don't want in director
            book = library.get_index(title)
            parser = MaharshaLite(book)
            with open(file) as f:
                parser.parse(list(f))
        except system.exceptions.BookNameError as e:
            print e


#Upshot is first word never part of DH, second word could be if it is B'Gemara, B'Mishneh, B'Rashi
    # with open("report.csv", 'w') as report:
    #     report = csv.writer(report)
    #     report.writerow(["Masechet", "Comm Alephs", "Comm Bets", "Comm Total", "Base Dappim"])
    #     for file in files:
    #         title = file[0:-4]
    #         with open(file) as f:
    #             try:
    #                 base = len(library.get_index(title).all_section_refs())
    #                 alephs, bets = get_alephs_bets(f)
    #                 report.writerow([title, alephs, bets, alephs+bets, base])
    #             except system.exceptions.BookNameError as e:
    #                 print e
