__author__ = 'stevenkaplan'
from sources.functions import *
import json
import csv
from data_utilities.dibur_hamatchil_matcher import *

class Resegment:
    def __init__(self, errors):
        self.resegment_errors = open(errors, 'w')
        self.curr_num_parshiot = 0
        self.curr_text_dict = {}
        self.new_text_dict = {}
        self.results = {}

    def parse_current(self, text_dict):
        for key in text_dict:
            for i, comments in enumerate(text_dict[key]):
                dhs = []
                for j, each_comm in enumerate(comments):
                    DH = " ".join(each_comm.split(" ")[0:10])
                    dhs.append(DH)
                text_dict[key][i] = dhs
        self.curr_text_dict = text_dict
        self.curr_num_parshiot = len(text_dict.keys())

    def get_parshiot(self):
        he_parshiot = {}
        with open("../../../Sefaria-Project/data/tmp/parsha.csv") as parsha_file:
            parshiot = csv.reader(parsha_file)
            parshiot.next()
            order = 1
            for row in parshiot:
                (en, he, ref) = row
                if en == "Lech-Lecha":
                    en = "Lech Lecha"
                he = he.decode('utf-8')
                he_parshiot[he] = en

        return he_parshiot

    def parse_new(self, new_file):
        he_parshiot = self.get_parshiot()
        text_dict = {}
        with open(new_file) as new_file:
            prev_num = 0
            num = 0
            for line in new_file:
                line = line.replace("\n", "").replace("\r", "").decode('utf-8')
                if len(line) == 0:
                    continue
                if line.startswith("#") and len(line.split(" ")) < 5:
                    line = " ".join(line.split(" ")[2:])
                    curr_parsha = he_parshiot[line]
                    text_dict[curr_parsha] = []
                    prev_num = 0
                elif line.startswith("!") and len(line.split(" ")) < 4:
                    line = " ".join(line.split(" ")[1:])
                    num = getGematria(line)
                    assert num - 1 == prev_num
                    prev_num = num
                elif prev_num == num:
                    text_dict[curr_parsha].append(line)

        self.check_dicts(text_dict)
        self.new_text_dict = text_dict

    def check_dicts(self, new_text_dict):
        #assert len(new_text_dict.keys()) == self.curr_num_parshiot
        for new_parsha in new_text_dict:
            len_new_parsha = len(new_text_dict[new_parsha])
            len_curr_parsha = len(self.curr_text_dict[new_parsha])
            assert len_new_parsha == len_curr_parsha

    def match(self):
        for key in self.new_text_dict:
            self.results[key] = []
            count = 0
            for i, base_text in enumerate(self.new_text_dict[key]):
                base_text = strip_nekud(base_text).split(" ")
                if base_text[-1] == "":
                    base_text = base_text[0:-1]
                commentary = self.curr_text_dict[key][i]
                self.results[key].append(match_text(base_text, commentary))
                for result in self.results[key][i]['matches']:
                    if result[0] == -1:
                        count += 1

            #print "There were {} not matched in {}".format(count, key)

    def segment(self):
        for parsha in self.results:
            sec_text_array = []
            for sec_count, matches_dict in enumerate(self.results[parsha]):
                new_text_array = self.new_text_dict[parsha][sec_count].split(" ")
                seg_text_array = []
                matches_tuples = matches_dict['matches']
                start = 0
                for seg_count, match_tuple in enumerate(matches_tuples):
                    if match_tuple == (-1, -1):
                        unsegmented_ref = "{} {}:{}".format(parsha, sec_count+1, max(seg_count, 1))
                        self.resegment_errors.write("Midrash Tanchuma, {} must be segmented.\n".format(unsegmented_ref))
                    elif seg_count > 0:
                        end = match_tuple[0]
                        seg_text_array.append(" ".join(new_text_array[start:end]))
                        start = end

                end = len(new_text_array)
                seg_text_array.append(" ".join(new_text_array[start:end]))

                self.check_two_versions(len(seg_text_array), len(self.curr_text_dict[parsha][sec_count]), parsha, sec_count+1)
                sec_text_array.append(seg_text_array)

            send_text = {
                "text": sec_text_array,
                "language": "he",
                "versionTitle": "new",
                "versionSource": "http://www.versionsource.com"
                }
            post_ref = "Midrash Tanchuma, {}".format(parsha)
            print post_ref
            post_text(post_ref, send_text, server="http://ste.sefaria.org")



    def check_two_versions(self, with_nekud, wout_nekud, parsha, sections):
        if with_nekud != wout_nekud:
            chapter_ref = "{} {}".format(parsha, sections)
            self.resegment_errors.write("""Midrash Tanchuma, {} is wrong.  Version w nekud
            has {} comments and version without nekud has {} comments\n\n""".format(chapter_ref, with_nekud, wout_nekud))

        '''
        Iterate through each 'matches' for each section of each parsha
        Ignore the first one since don't need to break it.
        Starting at the second set of indices, break there and continue for all comments of that section
        When finding a (-1, -1), record to a file the Ref that was skipped


        then we have two dictionaries, each with keys of parshiot, but the one with current_version has a two-d array
    where first index corresponds to the only index in the new_version dictionary, and the second index has the DH

    the new_version dict key indexes simply hold the block of text


    base_text is what??  base_text is new_version and commentary is current_version DHs
        '''




if __name__ == "__main__":
    resegment = Resegment("resegment_errors.txt")
    resegment.parse_current(json.load(open("current_version.json"))['text'])
    resegment.parse_new("new_version.txt")
    resegment.match()
    resegment.segment()
    '''
    current_version = parse_current(json.load("current_version.json")['text'])
    new_version = parse_new("new_version.txt")

    for parse_new function, it goes through new_version file, and builds a dictionary where keys are all of the English parshiot names
    and the value is the array of text, and modifies the text by stripping the nekudot (but how will we get back the nekudot later???)
    First: Create the dictionary and its arrays and then iterate and assert that the length of each array is the number of sections in the
    current version AND that the number of keys is identical to the number of parshiot in current

    for parse_current, it simply modifies the dictionary representing the current version by replacing each string by the first 12 words of
    that string, to make it like a DH

    '''
