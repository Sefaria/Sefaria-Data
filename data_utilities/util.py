__author__ = 'stevenkaplan'

class Util:
    def __init__(self, output_file, fail):
        self.output_file = output_file
        self.fail = fail

    def in_order_multiple_segments(self, line, curr_num, increment_by):
         if len(line) > 0 and line[0] == ' ':
             line = line[1:]
         if len(line) > 0 and line[len(line)-1] == ' ':
             line = line[:-1]
         if len(line.split(" "))>1:
             all = line.split(" ")
             num_list = []
             for i in range(len(all)):
                 num_list.append(getGematria(all[i]))
             num_list = sorted(num_list)
             for poss_num in num_list:
                 poss_num = fixChetHay(poss_num, curr_num)
                 if poss_num < curr_num:
                     return -1
                 else:
                     curr_num = poss_num
         return curr_num

    def fixChetHay(self, poss_num, curr_num):
        if poss_num == 8 and curr_num == 4:
            return 5
        elif poss_num == 5 and curr_num == 7:
            return 8
        else:
            return poss_num

    def in_order_caller(self, reg_exp_tag, file, reg_exp_reset):
        ##open file, create an array based on reg_exp,
        ##when hit reset_tag, call in_order
        in_order_array = []
        for line in open(file):
            reset = re.findall(reg_exp_reset, line)
            if len(reset) > 0:
                in_order(in_order_array, reg_exp_tag)
                in_order_array = []
            find_all = re.findall(reg_exp_tag, line)
            for each_one in find_all:
                in_order_array.append(each_one)




    def in_order(list, multiple_segments=False, dont_count=[], increment_by=1):
         poss_num = 0
         curr_num = 0
         perfect = True
         for line in list:
             for word in dont_count:
                line = line.replace(word, "")
             if multiple_segments == True:
                 curr_num = in_order_multiple_segments(line, curr_num, increment_by)
             else:
                 poss_num = getGematria(line)
                 poss_num = fixChetHay(poss_num, curr_num)
                 if increment_by > 0:
                     if poss_num - curr_num != increment_by:
                         perfect = False
                 if poss_num < curr_num:
                     perfect = False
                 curr_num = poss_num
                 if perfect == False:
                     self.fail()
                 prev_line = line

    def getHebrewTitle(sefer):
        sefer_url = SEFARIA_SERVER+'api/index/'+sefer.replace(" ","_")
        req = urllib2.Request(sefer_url)
        res = urllib2.urlopen(req)
        data = json.load(res)
        return data['heTitle']

   def convertDictToArray(dict, empty=[]):
        array = []
        count = 1
        text_array = []
        sorted_keys = sorted(dict.keys())
        for key in sorted_keys:
            if count == key:
                array.append(dict[key])
                count+=1
            else:
                diff = key - count
                while(diff>0):
                    array.append(empty)
                    diff-=1
                array.append(dict[key])
                count = key+1
        return array




    def wordHasNekudot(word):
        data = word.decode('utf-8')
        data = data.replace(u"\u05B0", "")
        data = data.replace(u"\u05B1", "")
        data = data.replace(u"\u05B2", "")
        data = data.replace(u"\u05B3", "")
        data = data.replace(u"\u05B4", "")
        data = data.replace(u"\u05B5", "")
        data = data.replace(u"\u05B6", "")
        data = data.replace(u"\u05B7", "")
        data = data.replace(u"\u05B8", "")
        data = data.replace(u"\u05B9", "")
        data = data.replace(u"\u05BB", "")
        data = data.replace(u"\u05BC", "")
        data = data.replace(u"\u05BD", "")
        data = data.replace(u"\u05BF", "")
        data = data.replace(u"\u05C1", "")
        data = data.replace(u"\u05C2", "")
        data = data.replace(u"\u05C3", "")
        data = data.replace(u"\u05C4", "")
        return data != word.decode('utf-8')


    def isGematria(txt):
        txt = txt.replace('.','')
        if txt.find("ך")>=0:
            txt = txt.replace("ך", "כ")
        if txt.find("ם")>=0:
            txt = txt.replace("ם", "מ")
        if txt.find("ף")>=0:
            txt = txt.replace("ף", "פ")
        if txt.find("ץ")>=0:
            txt = txt.replace("ץ", "צ")
        if txt.find("טו")>=0:
            txt = txt.replace("טו", "יה")
        if txt.find("טז")>=0:
            txt = txt.replace("טז", "יו")
        if len(txt) == 2:
            letter_count = 0
            for i in range(9):
                if inv_gematria[i+1]==txt[letter_count:2+letter_count]:
                    return True
                if inv_gematria[(i+1)*10]==txt[letter_count:2+letter_count]:
                    return True
            for i in range(4):
                if inv_gematria[(i+1)*100]==txt[letter_count:2+letter_count]:
                    return True
        elif len(txt) == 4:
          first_letter_is = ""
          for letter_count in range(2):
            letter_count *= 2
            for i in range(9):
                if inv_gematria[i+1]==txt[letter_count:2+letter_count]:
                    if letter_count == 0:
                        #print "single false"
                        return False
                    else:
                        first_letter_is = "singles"
                if inv_gematria[(i+1)*10]==txt[letter_count:2+letter_count]:
                    if letter_count == 0:
                        first_letter_is = "tens"
                    elif letter_count == 2:
                        if first_letter_is != "hundred":
                            #print "tens false"
                            return False
            for i in range(4):
                if inv_gematria[(i+1)*100]==txt[letter_count:2+letter_count]:
                    if letter_count == 0:
                        first_letter_is = "hundred"
                    elif letter_count == 2:
                        if txt[0:2] != 'ת':
                            #print "hundreds false, no taf"
                            return False
        elif len(txt) == 6:
            #rules: first and second letter can't be singles
            #first letter must be hundreds
            #second letter can be hundreds or tens
            #third letter must be singles
            for letter_count in range(3):
                letter_count *= 2
                for i in range(9):
                    if inv_gematria[i+1]==txt[letter_count:2+letter_count]:
                        if letter_count != 4:
                        #	print "3 length singles false"
                            return False
                        if letter_count == 0:
                            first_letter_is = "singles"
                    if inv_gematria[(i+1)*10]==txt[letter_count:2+letter_count]:
                        if letter_count == 0:
                            #print "3 length tens false, can't be first"
                            return False
                        elif letter_count == 2:
                            if first_letter_is != "hundred":
                            #	print "3 length tens false because first letter not 100s"
                                return False
                        elif letter_count == 4:
                            #print "3 length tens false, can't be last"
                            return False
                for i in range(4):
                    if inv_gematria[(i+1)*100]==txt[letter_count:2+letter_count]:
                        if letter_count == 0:
                            first_letter_is = "hundred"
                        elif letter_count == 2:
                            if txt[0:2] != 'ת':
                                #print "3 length hundreds false, no taf"
                                return False
        else:
            print "length of gematria is off"
            print txt
            return False
        return True

    def getGematria(txt):
        if not isinstance(txt, unicode):
            txt = txt.decode('utf-8')
        index=0
        sum=0
        while index <= len(txt)-1:
            if txt[index:index+1] in gematria:
                sum += gematria[txt[index:index+1]]

            index+=1
        return sum



    def numToHeb(engnum=""):
        engnum = str(engnum)
        numdig = len(engnum)
        hebnum = ""
        letters = [["" for i in range(3)] for j in range(10)]
        letters[0]=["", "א", "ב", "ג", "ד", "ה", "ו", "ז", "ח", "ט"]
        letters[1]=["", "י", "כ", "ל", "מ", "נ", "ס", "ע", "פ", "צ"]
        letters[2]=["", "ק", "ר", "ש", "ת", "תק", "תר", "תש", "תת", "תתק"]
        if (numdig > 3):
            print "We currently can't handle numbers larger than 999"
            exit()
        for count in range(numdig):
            hebnum += letters[numdig-count-1][int(engnum[count])]
        hebnum = re.sub('יה', 'טו', hebnum)
        hebnum = re.sub('יו', 'טז', hebnum)
        hebnum = hebnum.decode('utf-8')
        return hebnum


    def multiple_replace(old_string, replacement_dictionary):
        """
        Use a dictionary to make multiple replacements to a single string

        :param old_string: String to which replacements will be made
        :param replacement_dictionary: a dictionary with keys being the substrings
        to be replaced, values what they should be replaced with.
        :return: String with replacements made.
        """

        for keys, value in replacement_dictionary.iteritems():
            old_string = old_string.replace(keys, value)

        return old_string


    def find_discrepancies(book_list, version_title, file_buffer, language, middle=False):
        """
        Prints all cases in which the number of verses in a text version doesn't match the
        number in the canonical version.

        *** Only works for Tanach, can be modified to work for any level 2 text***

        :param book_list: list of books
        :param version_title: Version title to be examined
        :param file_buffer: Buffer for file to print results
        :param language: 'en' or 'he' accordingly
        :param middle: set to True to manually start scanning a book from the middle.
        If middle is set to True, user will be prompted for the beginning chapter.
        """

        # loop through each book
        for book in book_list:

            # print book to give user update on progress
            print book
            book = book.replace(' ', '_')
            book = book.replace('\n', '')

            if middle:

                print "Start {0} at chapter: ".format(book)
                start_chapter = input()
                url = SEFARIA_SERVER + '/api/texts/' + book + '.' + \
                    str(start_chapter) + '/' + language + '/' + version_title

            else:
                url = SEFARIA_SERVER + '/api/texts/' + book + '.1/' + language + '/' + version_title


            try:
                # get first chapter in book
                response = urllib2.urlopen(url)
                version_text = json.load(response)

                # loop through chapters
                chapters = Ref(book).all_subrefs()

                # check for correct number of chapters
                if len(chapters) != version_text['lengths'][0]:
                    file_buffer.write('Chapter Problem in'+book+'\n')

                for index, chapter in enumerate(chapters):

                    # if starting in the middle skip to appropriate chapter
                    if middle:
                        if index+1 != start_chapter:
                            continue

                        else:
                            # set middle back to false
                            middle = False

                    print index+1,

                    # get canonical number of verses
                    canon = len(TextChunk(chapter, vtitle=u'Tanach with Text Only', lang='he').text)

                    # get number of verses in version
                    verses = len(version_text['text'])
                    if verses != canon:
                        file_buffer.write(chapter.normal() + '\n')

                    # get next chapter
                    next_chapter = reg_replace(' \d', version_text['next'], ' ', '.')
                    next_chapter = next_chapter.replace(' ', '_')
                    url = SEFARIA_SERVER+'/api/texts/'+next_chapter+'/'+language+'/'+version_title

                    response = urllib2.urlopen(url)
                    version_text = json.load(response)

            except (URLError, HTTPError, KeyboardInterrupt, KeyError, ValueError) as e:
                print e
                print url
                file_buffer.close()
                sys.exit(1)

