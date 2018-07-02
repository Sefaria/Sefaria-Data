# -*- coding: utf-8 -*-

import argparse
import sys
import helperFunctions as Helper
#from helperFunctions import run_once
import json
import re
import csv
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import difflib


strip_cantillation_vowel_regex = re.compile(ur"[^\u05d0-\u05f4\s]", re.UNICODE)
    #re.compile(ur"[\u0591-\u05c7\s]", re.UNICODE)
    #
fuzzy_min_ratio = 98
exact_match_min_words = 2


def create_parsing_map():
    parsing_map = {
        '@00' : 'parsha',
        '@11' : 'dh',
        '@22' : 'verse'
    }
    return parsing_map


def book_record():
    return {
        "title": 'Meshech Hochma',
        "titleVariants": ["Meshech Hochma", "Meir Simcha HaCohen"],
        "heTitle": 'משך חכמה',
        "heTitleVariants" :['משך חכמה', 'מאיר שמחה הכהן'],
        "sectionNames": ["Parsha", "Comment"],
        "categories": ['Parshanut'],
    }

def make_biblical_portions_dict():
    portions_obj = {}
    with open("parsha.csv", 'rb') as csvfile:
        words = csv.reader(csvfile, delimiter=',')
        for row in words:
            obj = {}
            key = unicode(row[1].strip(), 'utf-8')
            obj['ref'] = row[2]
            obj['title'] = row[0]
            portions_obj[key] = obj
            #print "%s %s" % (key.encode('utf-8'), obj["title"])
    return portions_obj


def get_biblical_text(ref):
    api_res = Helper.api_get_text(ref)
    portion = {}
    portion['book'] = api_res['book']
    portion['text'] = api_res['he']
    portion['sections'] = api_res['sections']
    portion['searchBeginSections'] = api_res['sections']
    portion['toSections'] = api_res['toSections']
    if portion['sections'][0] == portion['toSections'][0]: #the api returns a list of strings, and not a 2d array if only one chapter
        #adjust to unify structure
        portion['text'] = [portion['text']]
    for i,chapter in enumerate(portion['text']): #if a chapter only has one verse, it is not an array
        if not isinstance(chapter, list):
            portion['text'][i] = [chapter]

    print "Ref: %s sections: %s to sections: %s" % (ref, portion['sections'], portion['toSections'])
    return portion

"""
def find_first_anchor_text(comment_arr, text_obj):
    #this joins the comment into one string, since initially the bold text is separated
    comment_text = " ".join(comment_arr)
    #go over each biblical verse and try and find a match. Begin from where we last found a match
    #first calculate the actual array cells the start from (in the verses)
    phys_cells = [y-x for x,y in zip(text_obj['sections'],text_obj['searchBeginSections'])]
    #make sure to denote the proper chapter and verse numbers while iterating

    for ch_num, chapter in enumerate(text_obj['text'][phys_cells[0]:], text_obj['searchBeginSections'][0]):
        #for a verse, we need the initial verse number only if we are still in the first chapter we are searching,
        # otherwise we start from the beginning
        first_verse = text_obj['searchBeginSections'][1] if ch_num == text_obj['searchBeginSections'][0] else 1
        first_cell = phys_cells[1] if ch_num == text_obj['searchBeginSections'][0] else 0
        for v_num, verse in enumerate(chapter[first_cell:], first_verse):
            match_res = find_match_in_verse(comment_text, verse)
            if match_res:
                #for now treat the first match as if it's the correct match
                #reset the boundaries to look at in the text
                text_obj['searchBeginSections'] = [ch_num, v_num]
                #return the chapter and verse number
                print "Match found in %s chapter %s, verse %s" % (text_obj['book'],ch_num, v_num)
                return match_res.update({'location': [ch_num, v_num]})
    print "No match found"
    return None
"""

def find_best_anchor_text(comment_str, source_dict):
    match = find_max_anchor_text(comment_str, source_dict, method="exact")
    if match is None:
        #print "didn't find exact"
        return find_max_anchor_text(comment_str, source_dict, method="fuzzy")
    elif match['match_count'] < exact_match_min_words:
        #print "found exact too small"
        fuzzy_match = find_max_anchor_text(comment_str, source_dict, method="fuzzy")
        if fuzzy_match and fuzzy_match['match_count'] > match['match_count']:
            return fuzzy_match
    return match



def find_max_anchor_text(comment_str, source_dict, method="exact"):
    result_options = []
    fuzzy_result_options = []
    #this joins the comment into one string, since initially the bold text is separated
    comment = prep_comment(comment_str)
    #go over each biblical verse and try and find a match. Begin from where we last found a match
    #first calculate the actual array cells the start from (in the verses)

    #make sure to denote the proper chapter and verse numbers while iterating
    for ch_num, chapter in enumerate(source_dict['text'], source_dict['searchBeginSections'][0]):
        #for a verse, we need the initial verse number only if we are still in the first chapter we are searching,
        # otherwise we start from the beginning
        first_verse = source_dict['searchBeginSections'][1] if ch_num == source_dict['searchBeginSections'][0] else 1
        for v_num, verse in enumerate(chapter, first_verse):
            verse = prep_source_verse(verse)
            match_res = re_find_match_in_verse(comment, verse) if method == 'exact' else fuzzy_find_match_in_verse(comment, verse)
            if match_res:
                match_res.update({'location': [ch_num, v_num], 'verse': verse})
                result_options.append(match_res)

    return sorted_result(result_options, method)

def sorted_result(results, method):
    if method == 'exact':
        sorting_func = lambda k: k['match_count']
    else:
        sorting_func = lambda k: k['match_ratio']
    sorted_results = sorted(results, key=sorting_func, reverse=True)
    if method is 'fuzzy':
        for s in sorted_results:
            print "{} for {} ({}) with match ratio {} and count {}".format(s['location'], s['anchor_text'].encode('utf-8'), s['type'], s['match_ratio'], s['match_count'])
    result = None
    if len(sorted_results):
        result = sorted_results[0]
        """if sorter(sorted_results[-1]) == sorted_results[0][pref_attr]:
            result = sorted_results[0]"""
    #print "Match found in %s chapter %s, verse %s" % (text_obj['book'],result[0], result[1])
    return result
    #print "No match found"

def prep_source_verse(verse):
    verse = re.sub(ur"\u05be", " ", verse) # removes upper maqafs, some words are connected with a dash
    verse = strip_cantillation_vowel_regex.sub('', verse)

    return verse

def prep_comment(comment):
    comment_start = comment.split(".")[0] # we definitely do not need past the first period
    comment_start = re.sub(ur"ד'", u"יהוה", comment_start) # replace Tetragrammaton shorthands with the real one
    return comment_start


def prep_comment_re(words):
    re_str = ur"(^|\s)" + re.escape(" ".join(words)) + ur"($|:|\s|\.)"
    if u"כו'" in re_str:
        re_str = re.sub(ur"[\u05d5]?כו'", ur".*" ,re_str)
    return re_str



#TODO: allow for spanning verses,
def re_find_match_in_verse(comment, verse):
    comment_words = comment.split()
    word_pos = 1
    while True:
        # we really dont need to look at the entire commentary section, just  the first few words.
        if word_pos > 10:
            break
        comment_re = prep_comment_re(comment_words[:word_pos])
        if re.search(comment_re, verse, re.UNICODE) is None: #comment_sub1str not in verse:
            word_pos -= 1
            break
        else:
            word_pos +=1
    if word_pos >=1:
        anchor_text = " ".join(comment_words[:word_pos])
        #print "Found match for the words %s" % anchor_text.encode('utf-8')
        return {'match_count' :word_pos, 'anchor_text' : anchor_text, 'type': 'exact_regex'}
    return None
    #get the verse

def fuzzy_find_match_in_verse(comment, verse):
    comment_words = comment.split()
    choices = []
    word_pos = 8
    match_ratio = 0
    while word_pos > 1:
        search_str = " ".join(comment_words[:word_pos])
        match_ratio = fuzz.partial_ratio(search_str,verse)
        #print "%s %d" % (search_str.encode('utf-8'), match_ratio)
        if match_ratio > 75: #fuzzy_min_ratio - ((2*word_pos)/100*fuzzy_min_ratio):
            choices.append((word_pos, match_ratio))
        word_pos-=1
    if len(choices):
        sort_choices = sorted(choices,key=lambda x: x[1], reverse=True)
        best_result = sort_choices[0]
        if best_result[0] >= exact_match_min_words:
            anchor_text = " ".join(comment_words[:best_result[0]])
            #print "Found match for the words %s" % anchor_text.encode('utf-8')
            return {'match_count' :best_result[0], 'match_ratio': best_result[1], 'anchor_text' : anchor_text, 'type': 'fuzzy'}
    return None
    #get the verse


def run_parser():
    print "running parser"
    running_verses = 0
    text_struct = []
    biblical_portions_dict = make_biblical_portions_dict()
    links = []
    #regex = re.compile(ur'@11(.*)@22',re.UNICODE)
    with open("source/Meshech Hochma.txt", 'r') as filep:
        file_text = filep.read()
        ucd_text = unicode(file_text, 'utf-8')
    #regex = re.compile(ur'@00([^@]*)',re.UNICODE)
    result_file = open("results.csv", 'wb+')
    result_csv = csv.writer(result_file, delimiter=',')
    regex = re.compile(ur'@00', re.UNICODE)
    p_arr = regex.split(ucd_text)
    p_arr.pop(0)
    i = 1
    for p in p_arr:
        verses = p.split('@11')
        if len(verses) <= 1:
            continue
            #if for some reason there is only a title
            # #there is one place where there is an extra title for "haftarot" that has no content

        parsha_name = parsha_key = verses.pop(0).strip() #split and isolate the parsha name
        segment_title = '<b>' + parsha_key + '</b>' #for inserting into the parsed text

        parsha = []

        print "title: ", segment_title.encode('utf-8')
        parsha.append(segment_title)
        linkify = parsha_key in biblical_portions_dict
        if linkify:
            #not all parsed segments are parashot.
            biblical_portions_dict[parsha_key].update(get_biblical_text(biblical_portions_dict[parsha_key]['ref']))
            print len(biblical_portions_dict[parsha_key]['text'])
        for j,v in enumerate(verses,2):
            running_verses +=1
            v_arr = v.split('@22')
            #this is the part where we need to make some links to the biblical text.
            comment_verse_formatted = '<b>%s</b>%s' % (v_arr[0], v_arr[1])
            comment_verse_text = '%s %s' % (v_arr[0], v_arr[1])
            if linkify:
                print "Links for Meshech Hochma %d %d"  % (i, j)
                link_res = find_best_anchor_text(comment_verse_text, biblical_portions_dict[parsha_key])
                if link_res:
                    link_obj = {
                        "type": "commentary",
                        "refs": ["Meshech Hochma %d:%d" % (i,j), "%s %d:%d" % (biblical_portions_dict[parsha_key]['book'], link_res['location'][0], link_res['location'][1])],
                        "anchorText": link_res['anchor_text'],
                    }
                    output_data = [link_obj['refs'][0], link_obj['anchorText'].encode('utf-8'), link_obj['refs'][1], link_res['verse'].encode('utf-8'), link_res['type']]
                    print "{} [{}] \n {} [{}] ({})".format(*output_data)
                    links.append(link_obj)
                    result_csv.writerow(output_data)
                else:
                    output_data = ["Meshech Hochma %d %d"  % (i, j), v_arr[0].encode('utf-8')]
                    result_csv.writerow(output_data)
            #print j, ") ",comment_verse.encode('utf-8')
            print "========================================================================================================"
            parsha.append(comment_verse_formatted)
        text_struct.append(parsha)
        i+=1
    save_parsed_text(text_struct)
    save_parsed_links(links)
    print "%d / %d" % (len(links), running_verses)
    result_file.close()


""" Saves a text to JSON """
def save_parsed_text(text):
    #print ref
    #JSON obj matching the API requirements
    text_whole = {
        "title": 'Meshech Hochma',
        "versionTitle": "Srikot",
        "versionSource": "",
        "language": "he",
        "text": text,
    }
    #save
    Helper.mkdir_p("preprocess_json/")
    with open("preprocess_json/Meshech Hochma.json", 'w') as out:
        json.dump(text_whole, out)

def save_parsed_links(links):
    Helper.mkdir_p("preprocess_json/links/")
    with open("preprocess_json/links/Meshech_Hochma_links.json", 'w') as out:
        json.dump(links, out)

def run_post_to_api():
    Helper.createBookRecord(book_record())
    with open("preprocess_json/Meshech Hochma.json", 'r') as filep:
        file_text = filep.read()
    Helper.postText("Meshech Hochma", file_text, False)

def run_post_links():
    #we saved an array of links, still need to build them each into the correct obj
    with open("preprocess_json/links/Meshech_Hochma_links.json", 'r') as filep:
        links_arr = json.load(filep)
    print len(links_arr), " ", isinstance(links_arr, list)

    Helper.postLink(links_arr)




""" The main function, runs when called from the CLI"""
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--preprocess", help="Perform the preprocess and parse the files but do not post them to the db", action="store_true")
    parser.add_argument("-a", "--postapi", help="post data to API",
                    action="store_true")
    parser.add_argument("-l", "--postlinks", help="post links to API",
                    action="store_true")
    args = parser.parse_args()
    #Map command line arguments to function arguments.
    if args.preprocess:
        run_parser()
    if args.postapi:
        print "posting to api"
        run_post_to_api()
    if args.postlinks:
        print "posting links to api"
        run_post_links()