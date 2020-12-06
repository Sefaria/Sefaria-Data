import django
django.setup()
from sefaria.model import *
from data_utilities.XML_to_JaggedArray import *
problems = set()
def get_guide_links_and_pos():
    links_and_pos = {}
    for k in sentences_per_chapter.keys():
        if k == "":
            continue
        print(k)
        links_and_pos[k] = []
        moreh_text = " ".join(Ref(k).text('en').text)
        citations = library.get_refs_in_string(moreh_text)
        prev_loc = 0
        for i, ref in enumerate(citations):
            curr_text = " ".join(moreh_text.split()[prev_loc:])
            chr_pos = curr_text.find(ref)
            loc = len(curr_text[:chr_pos].split())
            try:
                links_and_pos[k].append((Ref(ref).normal(), loc+prev_loc))
            except:
                pass
            prev_loc += loc
    return links_and_pos

def get_guide_words_and_sentences():
    our_guide_words = {}
    our_guide_sentences = {}
    avg = 0
    total = 0
    min = 100
    max = 0
    for k in sentences_per_chapter.keys():
        if k == "":
            continue
        moreh_text = " ".join(Ref(k).text('en').text)

        our_guide_sentences[k] = len(re.findall("\. [A-Z]{1}", moreh_text)) + 1 + len(re.findall('\.\"', moreh_text))
        our_guide_words[k] = len(moreh_text.split())
        curr_val = words_per_chapter[k]/our_guide_words[k]
        if curr_val < min:
            min = curr_val
        if curr_val > max:
            max = curr_val
        avg += curr_val
        total += 1
    print("Average: {}".format(float(avg)/total))
    print("Range: {} to {}".format(min, max))
    return our_guide_sentences, our_guide_words

def add_citations(orig_row, row, num_words_citation):
    match = re.search(".*?\d+\.\d+\.\d+", orig_row[0])
    if not match:
        return row
    if "Part" not in row[0]:
        row[0] = row[0].replace(".", ", ", 1)
        row[0] = re.sub("(\d+), ", "Part \g<1>, ", row[0])
    section_ref = Ref(row[0]).section_ref().normal()
    if section_ref not in found_by_sec:
        found_by_sec[section_ref] = []
        found_by_seg[section_ref] = {}
    found_by_sec[section_ref].append(new_citation)
    if Ref(row[0]).normal() not in found_by_seg[section_ref]:
        found_by_seg[section_ref][Ref(row[0]).normal()] = []
    found_by_seg[section_ref][Ref(row[0]).normal()].append((new_citation, num_words_citation, row[1]))
    return row

def test(poss_links, ref, corresponding):
    found = False
    real_links = [get_ref(l) for l in LinkSet(Ref(ref))]
    for l in poss_links:
        if l in real_links:
            found = True
            corresponding[ref] = ref
            break
    return found

def get_corr_siman_try_2(our_guide_links, our_guide_links_by_seg, links, links_by_seg):
    corresponding = {}
    found = False
    guide = "Guide for the Perplexed, Part 1"
    curr_siman = 1

    for r, ref in enumerate(links):
        poss_links = links[ref]
        overlap = set(poss_links).issubset(set(our_guide_links[ref])) #set(poss_links).intersection(our_guide_links[ref]) > 0
        if overlap:

            corresponding[ref] = ref


        else:
            prev_5 = None
            next_5 = None
            others_to_check = []
            corresponding[ref] = []
            for i in range(1, 6):
                if r+i < len(links):
                    others_to_check.append(list(links.keys())[r+i])
                if r-i >= 0:
                    others_to_check.append(list(links.keys())[r-i])
            for l in others_to_check:
                overlap = set(poss_links).intersection(l)
                if len(overlap) > 0:
                    print("Found match")
                    corresponding[ref] += l
    return corresponding

    # try instead of resetting each time we find, because this relies on assumptions,
    # just start at each position and go up and down 5 - 10 spots looking for all matches and record all

def get_ref(l):
    guide_pos = 0 if l.refs[0].startswith("Guide for the Perplexed,") else 1
    guide_ref = l.refs[guide_pos]
    other_ref = l.refs[1-guide_pos]
    other_index = Ref(other_ref).index
    not_comm = "Commentary" not in other_index.categories
    tanakh = "Tanakh" in other_index.categories
    if tanakh and not_comm:
        return other_ref
    else:
        return ""

def get_corresponding_simanim(links):
# if you can find tne of the links move on to next siman, if you find none in corresponding siman, check before and after
# save the spot where you found it last
    corresponding = {}
    found = False
    guide = "Guide for the Perplexed, Part 1"
    curr_siman = 1
    for ref in links:
        if ref.startswith(guide):
            poss_links = links[ref]
            found = test(poss_links, ref, corresponding)
            print(found)
            if found:
                curr_siman += 1
            elif not found:
                #if you move Guide back, you're saying that French version is split into two,
                if curr_siman > 1:
                    curr_siman -= 1
                    ref = "{} {}".format(guide, curr_siman)
                    found = test(poss_links, ref, corresponding)
                    if not found:
                        #if you move Guide forward, you're saying Guide is split
                        curr_siman += 2
                        ref = "{} {}".format(guide, curr_siman)
                        found = test(poss_links, ref, corresponding)
                        if not found:
                            corresponding[ref] = "Not found"
                            curr_siman -= 1
    return corresponding

fr_books = """Genèse
Exode
Lévitique
Nombres
Deutéronome
Josué
Juges
I Samuel
II Samuel
I Rois
II Rois
Isaïe
Jérémie
Ézéchiel
Osée
Joël
Amos
Abdias
Jonas
Michée
Nahum
Habacuc
Zéphanie
Aggée
Zacharie
Malachie
Psaumes
Proverbes
Job
Cantique des Cantiques
Ruth
Lamentations
Ecclésiaste
Esther
Daniel
Esdras
Néhémie
I Chroniques
II Chroniques""".splitlines()

en_tanakh = library.get_indexes_in_category("Tanakh")
books = "|".join(fr_books)
found_by_seg = {}
found_by_sec = {}
from sources.functions import *
words_per_chapter = {}
sentences_per_chapter = {}
num_words_citation = 0
with open("new_full_text.csv", 'w') as new_f:
    writer = csv.writer(new_f)
    with open("Moreh Nevukhim.csv", 'r') as f:
        rows = list(csv.reader(f))
        for r, row in enumerate(rows):
            orig_row = list(row)
            finds = re.findall("([A-ZÀ-ÿa-z. ]{2,15}), ([ILVXC]+), (\d+)", row[1])
            if "Part" not in row[0]:
                ch = row[0].replace(".", ", ", 1)
                ch = re.sub("(\d+), ", "Part \g<1>, ", ch)
            ch = ":".join(ch.split(".")[:-1])
            if ch not in words_per_chapter:
                num_words = 0
                words_per_chapter[ch] = 0
                sentences_per_chapter[ch] = 0
            words_per_chapter[ch] += len(row[1].split())
            sentences_per_chapter[ch] += len(re.findall("\. [A-ZÀ-Ÿ]{1}", row[1])) + 1 + len(re.findall('\.\"', row[1]))
            if finds:
                for find in finds:
                    find = list(find)
                    temp_ref = "{}, {}, {}".format(find[0], find[1], find[2])
                    num_words_citation = len(row[1].split(temp_ref)[0].split()) + temp_ref.count(" ") + 1
                    old_citation = "{}, {}".format(*find[1:])
                    if len(find) != 3:
                        print("ERROR")
                    else:
                        find[1] = roman_to_int(find[1])
                        try:
                            loc = fr_books.index(find[0])
                            actual_book = en_tanakh[loc]
                            find[0] = actual_book
                        except ValueError as e:
                            find[0] = find[0].replace("Micha", "Micah").replace("Ézéch.", "Ezekiel").replace("Ps.", "Psalms").replace("Exod.", "Exodus") \
                                .replace("Deutéron.", "Deuteronomy").replace("I Chron.", "I Chronicles").replace("Habac.", "Habakkuk") \
                                .replace("Lévit.", "Leviticus").replace("Prov.", "Proverbs").replace("Lament.", "Lamentations") \
                                .replace("I Sam.", "I Samuel").replace("II Sam.", "II Samuel").replace("II Chron.", "II Chronicles") \
                                .replace("Malach.", "Malachi").replace("Deutér.", "Deuteronomy").replace("Nomb.", "Numbers") \
                                .replace("Nombr.", "Numbers").replace("Lév.", "Leviticus").replace("Jér.", "Jeremiah").replace('Ecclés.', "Ecclesiastes") \
                                .replace("Deutér", "Deuteronomy").replace("Malach.", "Malachi").replace("Ezéch", "Ezekiel").replace("Deulér", "Deuteronomy").replace("Gen.", "Genesis") \
                                .replace("Jos.", "Joshua").replace("Dan.", "Daniel").replace("Deuter.", "Deuteronomy").replace("Hos.", "Hoshea") \
                                .replace("Cantique des cant.", "Cantique des Cant.").replace("Cantique des Cant.", "Song of Songs") \
                                .replace("Ecclesiaste", "Ecclesiastes").replace("Roi", "Rois").replace("Deut.", "Deuteronomy").replace("'Jérém.'", "Jeremiah").replace("Sam.", "Samuel").replace("Hag.", "Haggai").replace("Hosée","Hosea")
                            actual_book = find[0]
                        new_citation = "{}:{}".format(*find[1:])
                        assert old_citation in row[1]
                        row[1] = row[1].replace(old_citation, new_citation, 1)
                        new_citation = "{} {}".format(actual_book, new_citation)
                        row = add_citations(orig_row, row, num_words+num_words_citation)
            else:
                if "Part" not in row[0]:
                    row[0] = row[0].replace(".", ", ", 1)
                    row[0] = re.sub("(\d+), ", "Part \g<1>, ", row[0])
                try:
                    section_ref = Ref(row[0]).section_ref().normal()
                    if section_ref not in found_by_sec:
                        found_by_seg[section_ref] = {}
                    if Ref(row[0]).normal() not in found_by_seg[section_ref]:
                        found_by_seg[section_ref][Ref(row[0]).normal()] = []
                    found_by_seg[section_ref][Ref(row[0]).normal()].append((new_citation, num_words_citation, row[1]))
                except Exception as e:
                    pass
            num_words += len(row[1].split())

            writer.writerow(row)
our_guide_links = {}
our_guide_seg_links = {}
segs = Ref("Guide for the Perplexed, Part 1").all_segment_refs() + Ref(
    "Guide for the Perplexed, Part 2").all_segment_refs() + Ref("Guide for the Perplexed, Part 3").all_segment_refs()
secs = Ref("Guide for the Perplexed, Part 1").all_subrefs() + Ref(
    "Guide for the Perplexed, Part 2").all_subrefs() + Ref("Guide for the Perplexed, Part 3").all_subrefs()

our_guide_words, our_guide_sentences = get_guide_words_and_sentences()
for ref in segs:
    our_guide_seg_links[ref.normal()] = [get_ref(l) for l in LinkSet(ref)]

# links_and_pos = get_guide_links_and_pos()
with open('our_guide_links_and_pos.json', 'r') as f:
    links_and_pos = json.load(f)
for ref in secs:
    our_guide_links[ref.normal()] = [get_ref(l) for l in LinkSet(ref)]

#results = get_corr_siman_try_2(our_guide_links, our_guide_seg_links, found_by_sec, found_by_seg)


#test that ratio falls inside range 1.13 to 4.36 before accepting match, otherwise flag siman
#need to test that match ends with a period...
prev_pos = 0
total_simanim = 0
running_text = ""
new_found_by_seg = dict(our_guide_seg_links)
for i, sec_ref in enumerate(found_by_seg):
    total_simanim += 1
    prev_len_text = 0 #running count throughout sec_ref
    full_text = ""
    for seg_ref in found_by_seg[sec_ref]:
        new_found_by_seg[seg_ref] = ""
        for citation in found_by_seg[sec_ref][seg_ref]:
            french_ref, french_word_count, french_text = citation
            full_text += french_text + " "

    for seg_ref in found_by_seg[sec_ref]:
        for citation in found_by_seg[sec_ref][seg_ref]:
            french_ref, french_word_count, french_text = citation
            moreh_ref = sec_ref.replace("Part 1", "Part 1,").replace("Part 2", "Part 2,").replace("Part 3", "Part 3,").replace("Guide for the Perplexed", "Moreh Nevukhim")
            our_guide_links_and_word_counts = links_and_pos[moreh_ref]
            found = False
            for our_ref, our_word_count in our_guide_links_and_word_counts:
                if french_ref == our_ref:
                    if french_ref == 'Ezekiel 1:26':
                        print()
                    ratio = float(french_word_count)/our_word_count
                    if 1 < ratio < 5:
                        found = True
                        curr_text = " ".join(full_text.split()[prev_pos:french_word_count])
                        new_found_by_seg[seg_ref] += curr_text
                        running_text = ""
                        # check french text to see that it ends with a period...
                        if not french_text.endswith("."):
                            print("Warning: No period in {}".format(french_ref))

                        prev_pos = french_word_count
                    else:
                        print("Warning: Ratio off in {}".format(sec_ref))
            # running_text += " ".join(french_text.split()[prev_pos:]) + " " #whatever couldn't be matched should be saved
            # prev_pos = len(running_text.split())
        # if not found:
        prev_len_text += len(french_text.split())
    if prev_pos < len(full_text.split()):
        curr_text = " ".join(full_text.split()[prev_pos:french_word_count + 1])
        new_found_by_seg[seg_ref] += curr_text

print(total_simanim)

