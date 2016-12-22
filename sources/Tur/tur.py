# -*- coding: utf-8 -*-
import urllib
import urllib2
from urllib2 import URLError, HTTPError
import json 
import pdb
import os
import sys
import re
p = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, p)

os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from local_settings import *
from functions import *

sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *
from sefaria.model.schema import AddressTalmud


def flipTags(line, first_word_66, first_word_77, first_word_88):
    line = line.decode('utf-8')
    if line[0] == ' ':
        line = line[1:]
    orig_arr = re.findall(u"(?:@\d\d)*\([\u05D0-\u05EA]{1,4}\)", line)
    for count, each_one in enumerate(orig_arr):
        copy = each_one
        start = copy.find('(')
        tags = copy[0:start]
        copy = copy.replace(tags, "")
        copy = copy + tags
        if count == 0:
            if first_word_66 >= 0:
                copy = copy+"@66"
            if first_word_77 >= 0:
                copy = copy + "@77"
            if first_word_88 >= 0:
                copy = copy+ "@88"
        line = line.replace(each_one, copy)
    return line.encode('utf-8')


def replaceWithOrder(line, at):
    count = 1
    before_marker = at[0:2]
    after_marker = at[2:]
    while line.find(at)>=0:
        pos = line.find(at)
        line_before = line[0:pos]
        line_after = line[pos+4:]
        replace_with = before_marker+numToHeb(count).encode('utf-8')+after_marker
        try:
            line = line_before+replace_with+line_after
        except:
            pdb.set_trace()
        count+=1
    return line



def gatherData(data, line, helek, siman_num, matches_array, commentaries):
    #for this siman, this commentary, there are these tags
    data[helek][siman_num] = {}
    for commentary_count, matches in enumerate(matches_array):
        hash = {}
        this_commentary = commentaries[commentary_count]
        if this_commentary == "Replace":
            continue
        data[helek][siman_num][this_commentary] = {}
        for order_count, match in enumerate(matches):
            this_match = getGematria(match.encode('utf-8'))
            if this_match in hash:
                hash[this_match] += 1
            else:
                hash[this_match] = 1
        data[helek][siman_num][this_commentary] = hash
    return data


def skippedAny(array):
    length = len(array)
    prev = 0
    report = ""
    for each_one in array:
        if each_one != prev + 1:
            report += "Skipped " + numToHeb(prev+1).encode('utf-8') + "\n"
        prev = each_one

    return report


def genDict(matches_array, commentaries, which_one):
    hash = {}
    for commentary_count, matches in enumerate(matches_array):
        if commentaries[commentary_count] == which_one:
            for order_count, match in enumerate(matches):
                this_gematria = getGematria(match)
                if this_gematria in hash:
                    hash[this_gematria] += 1
                else:
                    hash[this_gematria] = 1

    return hash


def check(which_one, siman_num, helek, matches_array, commentaries, line):
    if helek == 'Choshen Mishpat':
        return

    duplicate_report = open("report_"+which_one+"_duplicates.txt", "a")
    skipped_report = open("skipped_"+which_one+".txt", "a")
    which_one = which_one.replace(" ", "")
    siman_report = open("siman_off_report.txt", 'a')
    name_of_file_lengths = "{}_{}_length_siman.txt".format(which_one, helek.replace(" ", ""))
    print helek
    print which_one
    hash = genDict(matches_array, commentaries, which_one)
    lengths_of_simans = json.loads(open(name_of_file_lengths).read())
    if which_one == "DarcheiMoshe":
        darchei_file = open("{} darchei moshe.txt".format(helek))
        update_dict_BY_data(hash, darchei_file, siman_num, duplicate_report)
        darchei_file.close()
    if len(hash) == 0 and str(siman_num) in lengths_of_simans:
        siman_report.write("{} {}".format(siman_num, helek))
        siman_report.write("\nThere are 0 {} tags in Tur but there is a comment in {} files".format(which_one, which_one))
        siman_report.write("\n\n")
        siman_report.close()
        return
    elif len(hash) > 0 and str(siman_num) not in lengths_of_simans:
        siman_report.write("{} {}".format(siman_num, helek))
        siman_report.write("\nThere are {} tags in Tur but there are 0 comments in {} files.".format(which_one, which_one))
        siman_report.write("\n\n")
        siman_report.close()
        return
    if len(hash) > 0:
        helek = helek.replace(" ", "")
        length_of_siman = lengths_of_simans[str(siman_num)]
        remove_keys_beyond_length(hash, length_of_siman)
        write_duplicate(hash, duplicate_report, siman_num, helek)
        keys = sorted(hash.keys())
        skipped_any = skippedAny(keys)
        if len(skipped_any) > 0:
            skipped_report.write("{} Siman #: {}\n".format(helek, siman_num))
        skipped_report.write(skipped_any)
        duplicate_report.close()
        skipped_report.close()


def update_dict_BY_data(hash, other_file, siman_num, duplicate_report):
    data = json.loads(other_file.read())
    if str(siman_num) not in data:
        duplicate_report.write("In Beit Yosef, not finding Siman #"+str(siman_num)+"\n")
        return
    else:
        array = data[str(siman_num)]
    for each in array:
        if each in hash:
            hash[each] += 1
        else:
            hash[each] = 1


def remove_keys_beyond_length(hash, length_of_siman):
    ones_beyond_range = []
    for key in hash:
        if key > length_of_siman:
            ones_beyond_range.append(key)
    for el in ones_beyond_range:
        hash.pop(el)




def write_duplicate(hash, duplicate_report, siman_num, helek):
    for number in hash:
        if hash[number] > 1:
            print "Siman "+str(siman_num)+", "+helek+": "+numToHeb(number).encode('utf8')+" has "+str(hash[number])+"\n"
            duplicate_report.write("Siman "+str(siman_num)+", "+helek+": "+numToHeb(number).encode('utf8')+" has "+str(hash[number])+"\n")


def replaceWithHTMLTags(line, helek, siman_num, data):
    global prisha_file
    line = line.decode('utf-8')
    line = line.replace('%(', '(%')
    line = line.replace('(#', '(%')
    line = line.replace("&%", "(%")
    line = line.replace('(*', '(%')
    if helek == "Choshen Mishpat":
       commentaries = ["DarcheiMoshe", "Hagahot", "Beit_Yosef", "Bach", "Replace", "Mystery"]
       matches_array = [re.findall(u"\(%[\u05D0-\u05EA]{1,4}\)", line), re.findall(u"\s#[\u05D0-\u05EA]{1,4}", line),
                        re.findall(u"\{[\u05D0-\u05EA]{1,4}\}",line), re.findall(u"\|[\u05D0-\u05EA]{1,4}\|", line),
                        re.findall(u"\([\u05D0-\u05EA]{1,4}\)", line), re.findall(u"<[\u05D0-\u05EA]{1,4}>",line)]
    else:
       commentaries = ["Drisha", "Prisha", "DarcheiMoshe", "Hagahot", "Beit_Yosef", "Bach", "Mystery"]
       matches_array = [re.findall(u"\[[\u05D0-\u05EA]{1,4}\]", line), re.findall(u"\([\u05D0-\u05EA]{1,4}\)", line),
                        re.findall(u"\(%[\u05D0-\u05EA]{1,4}\)", line) or re.findall(u"\[%[\u05D0-\u05EA]{1,4}\]", line),
                        re.findall(u"\s#[\u05D0-\u05EA]{1,4}", line),
                        re.findall(u"\{[\u05D0-\u05EA]{1,4}\}",line), re.findall(u"\|[\u05D0-\u05EA]{1,4}\|", line),
                        re.findall(u"<[\u05D0-\u05EA]{1,4}>",line)]
                        
    data = gatherData(data, line, helek, siman_num, matches_array, commentaries)
    
    check("Drisha", siman_num, helek, matches_array, commentaries, line)
    check("Prisha", siman_num, helek, matches_array, commentaries, line)
    check("Darchei Moshe", siman_num, helek, matches_array, commentaries, line)

    for commentary_count, matches in enumerate(matches_array):
        hash = {}
        how_many_shams = 0
        for order_count, match in enumerate(matches):
            if helek == "Choshen Mishpat" and commentaries[commentary_count] == "Replace":
                line = line.replace(match, "#$!^")
            else:
                this_gematria = getGematria(match.encode('utf-8'))
                if this_gematria in hash:
                    hash[this_gematria] += 1
                    prisha_file += 1
                else:
                    hash[this_gematria] = 1
                HTML_tag =  '<i data-commentator="'+commentaries[commentary_count]+'" data-order="'+str(this_gematria)+"."+str(hash[this_gematria])+'"></i>'
                line = line.replace(match, HTML_tag, 1)
    return line, data


def create_indexes(eng_helekim, heb_helekim):
  tur = SchemaNode()
  tur.add_title("Tur", 'en', primary=True)
  tur.add_title("Arbah Turim", 'en', primary=False)
  tur.add_title("Arbaah Turim", 'en', primary=False)
  tur.add_title("Arba Turim", 'en', primary=False)
  tur.add_title(u"טור", 'he', primary=True)
  tur.add_title(u"ארבעה טורים", 'he', primary=False)
  tur.key = 'tur'
  for count, helek in enumerate(eng_helekim):
      if helek == "Choshen Mishpat":
          choshen = JaggedArrayNode()
          choshen.add_title("Choshen Mishpat", "en", primary=True)
          choshen.add_title(heb_helekim[count], "he", primary=True)
          choshen.key = helek
          choshen.depth = 2
          choshen.addressTypes = ["Integer", "Integer"]
          choshen.sectionNames = ["Siman", "Seif"]
          tur.append(choshen)
      else:
          helek_node = JaggedArrayNode()
          helek_node.add_title(helek, 'en', primary=True)
          helek_node.add_title(heb_helekim[count], 'he', primary=True)
          helek_node.key = helek
          helek_node.depth = 2
          helek_node.addressTypes = ["Integer", "Integer"]
          helek_node.sectionNames = ["Siman", "Seif"]
          tur.append(helek_node)
  tur.validate()
  index = {
    "title": "Tur",
    "titleVariants": ["Arba Turim", "Arbaah Turim", "Arbah Turim"],
    "categories": ["Halakhah", "Tur and Commentaries"],
    "schema": tur.serialize()
    }
  post_index(index)

def parse_text(at_66, at_77, at_88, helekim, files_helekim):
  data = {}  
  for count, helek in enumerate(helekim):
    f = open(files_helekim[count])
    current_siman = 0
    append_to_next_line= False
    prev_hilchot_topic = ""
    just_saw_00 = False
    will_see_00 = False
    text[helek] = {}
    data[helek] = {}
    header = ""
    old_header = ""
    for line in f:
        actual_line = line
        line = line.replace('\n','').replace('\r','')
        if len(line) < 1:
            continue
        if (len(line)<=20 and line.find("@22")>=0):
            append_to_next_line = True
            appending = line
            continue
        if append_to_next_line:
            #print appending+line
            append_to_next_line = False
            line = appending + line
        first_word_66 = -1
        first_word_77 = -1
        first_word_88 = -1
        siman_header = False


        if line.find("@00") >= 0:
          header_pos = line.find("@00")
          len_line = len(line)
          if header_pos > 10 and header_pos < len_line-100:
            start = line.find("@00")
            there_yet = 0
            end = -1
            for index, char in enumerate(line):
                if index > start:
                    if char == ' ':
                        there_yet += 1
                if there_yet == 2:
                    end = index
                    print line[start:end]
                    break
            line = line.replace(line[start:end], "<br><b>"+line[start:end]+"<br>")



        if line.find("@00") >= 0 and len(line.split(" ")) >= 2:
            start = line.find("@00")
            end = len(line)
            if len(header) > 0:
                old_header = header
            header = line[start:end]
            line = line.replace(header, "")
            header = removeAllStrings(header)
            line_wout_tags = removeAllStrings(line)
            if len(line_wout_tags) > 1:
                will_see_00 = True
            else:
                just_saw_00 = True
                continue

        if line.find("@22")>=0 or (line.find("@00")>=0 and len(line)>200):
            siman_header = True
            if line[0] == ' ':
                line = line[1:]
            first_space = line.find(' ')
            first_word = line[0:first_space]
            first_word_66 = first_word.find("@66")
            first_word_77 = first_word.find("@77")
            first_word_88 = first_word.find("@88")
            first_word = first_word.replace("@22","").replace("@77","").replace("@66","").replace("@11","").replace("@88","").replace("@00","")
            this_siman = getGematria(first_word)
            if this_siman != current_siman + 1 and this_siman != current_siman+2 and this_siman != 37:
                print 'siman off'
                pdb.set_trace()
                print this_siman
                print current_siman
                print helek
                print line
            line_wout_first_word = line[first_space+1:]
            second_word = line_wout_first_word[0:line_wout_first_word.find(' ')]
            second_word = removeAllStrings(second_word)
            second_gematria = getGematria(second_word)
            current_siman = this_siman
            line = line[first_space+1:]
            line = removeExtraSpaces(line)
            if line[0] == ' ':
                line = line[1:]
            if helek == "Choshen Mishpat":
                line = flipTags(line, first_word_66, first_word_77, first_word_88)
            else:
                if first_word_66 >= 0:
                    line = "@66"+line
                if first_word_77 >= 0:
                    line = "@77"+line
                if first_word_88 >= 0:
                    line = "@88"+line
        line = line.replace("@66", at_66)
        line = line.replace("@77", at_77)
        line = line.replace("@88", at_88)
        line = replaceWithOrder(line, at_66)
        line = replaceWithOrder(line, at_77)
        line = replaceWithOrder(line, at_88)
        line = removeAllStrings(line)
        
        
        if just_saw_00 == True:
            just_saw_00 = False
            if helek == "Choshen Mishpat":
              if len(old_header) > 0:
                headers[current_siman] = old_header
                old_header = ""
              else:
                headers[current_siman] = header
                header = ""
            else:
                if len(old_header) > 0:
                    line = "<b>"+old_header+"</b><br>"+line
                    old_header = ""
                else:
                    line = "<b>"+header+"</b><br>"+line
                    header = ""
        elif will_see_00 == False:
            if len(header) > 0:
                pdb.set_trace()

        if will_see_00 == True:
            just_saw_00 = True
            will_see_00 = False

        line, data = replaceWithHTMLTags(line, helek, current_siman, data)
        if current_siman not in text[helek]:
            text[helek][current_siman] = [line]
        else:
            text[helek][current_siman][0] = text[helek][current_siman][0]+"<br>"+line
        if second_gematria - this_siman == 1:
            text[helek][second_gematria] = [u"ראו סימן "+str(current_siman)]
            current_siman = second_gematria
        prev_line = actual_line
  return data

if __name__ == "__main__":
    import csv
    global tag_csv_files
    tag_csv_files = {}
    tag_csv_files["Choshen Mishpat"] = 'CM_tags.csv'
    tag_csv_files["Yoreh Deah"] = 'YD_tags.csv'
    tag_csv_files["Even HaEzer"] = 'EH_tags.csv'
    tag_csv_files["Orach Chaim"] = 'OC_tags.csv'

    global text
    global prisha_file
    prisha_file = 0
    global headers
    headers = {}
    text = {}
    global hilchot_topic
    hilchot_topic = {}
    eng_helekim = ["Orach Chaim", "Yoreh Deah", "Even HaEzer", "Choshen Mishpat"]
    heb_helekim = [u"אורח חיים", u"יורה דעה", u"אבן העזר", u"חושן משפט"]
    at_66 = " {} "
    at_77 = " || "
    at_88 = " <> "
    files_helekim = ["Orach_Chaim/turorachchaim.txt", "Yoreh Deah/tur yoreh deah.txt", "Even HaEzer/tur even haezer.txt", "Choshen Mishpat/tur choshen mishpat.txt"]
    #create_indexes(eng_helekim, heb_helekim)
    data = parse_text(at_66, at_77, at_88, eng_helekim, files_helekim)
    for helek in data:
        f = open(tag_csv_files[helek], 'w')
        f.write(json.dumps(data[helek]))
        f.close()
    print 'done parsing'
    for siman_num in text["Choshen Mishpat"]:
        if siman_num in headers:
            header = "<b>"+headers[siman_num]+"</b><br>"
        else:
            header = ""
        current = text["Choshen Mishpat"][siman_num][0].replace(u'\xa0',u'')
        new_arr = current.split("#$!^")
        if new_arr[0].replace(" ","") == '':
            new_arr.pop(0)
        new_arr[0] = header.decode('utf-8') + new_arr[0]
        text["Choshen Mishpat"][siman_num] = []
        for each_one in new_arr:
           text["Choshen Mishpat"][siman_num].append(each_one)
    for helek in eng_helekim:
        print helek
        send_text = {
            "text": convertDictToArray(text[helek]),
            "language": "he",
            "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001935970",
            "versionTitle": helek + ", Vilna, 1923"
        }
        #post_text("Tur,_"+helek, send_text)
    