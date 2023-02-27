import django

django.setup()
from sefaria.model import *
from sefaria.system.exceptions import *
from parsing_utilities.XML_to_JaggedArray import *
import bleach

french_by_sec = {}
french_data = {}
words_per_chapter = {}
sentences_per_chapter = {}
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

def calc_overlap_score(en_sefaria_refs_in_curr_seg, fr_sefaria_refs_in_curr_seg):
    score = 0
    for en in en_sefaria_refs_in_curr_seg:
        for fr in fr_sefaria_refs_in_curr_seg:
            if en == fr:
                score += 2
            else:
                en_seg = Ref(en).section_ref().normal()
                fr_seg = Ref(fr).section_ref().normal()
                if fr_seg == en_seg:
                    score += 1
    return score


def partial_align():
    # new alignment, go through french_data seg refs and look for corresponding english links_and_pos_by_seg_ref
    # that has the most citations in common.  however, this must be done in order so once a match is made to
    # the 2nd segment of links_and_pos_by_seg_ref, the 1st segment cannot be considered in the next iteration
    aligned_text = {}
    for sec_ref in french_data:
        en_sefaria_refs = {}
        aligned_text[sec_ref] = {}
        moreh_sec_ref = sec_ref.replace("Part 1", "Part 1,").replace("Part 2", "Part 2,") \
            .replace("Part 3", "Part 3,").replace("Guide for the Perplexed", "Moreh Nevukhim")
        for en_seg_ref in links_and_pos_by_seg_ref[moreh_sec_ref]:
            our_citations = links_and_pos_by_seg_ref[moreh_sec_ref][en_seg_ref]
            en_sefaria_refs[en_seg_ref] = []
            for our_citation in our_citations:
                curr_sefaria_ref, en_num_words = our_citation
                en_sefaria_refs[en_seg_ref].append(curr_sefaria_ref)

        prev_seg_ref_found = 1
        for fr_seg_ref in french_data[sec_ref]:
            fr_text = ""
            fr_sefaria_refs_in_curr_seg = []
            for fr_citation_tuple in french_data[sec_ref][fr_seg_ref]:
                fr_sefaria_ref, fr_num_words, curr_text, fr_roman_ref = fr_citation_tuple
                fr_text += curr_text + " " + fr_roman_ref + " "
                if len(fr_sefaria_ref) > 0:
                    try:
                        fr_sefaria_refs_in_curr_seg.append(Ref(fr_sefaria_ref).normal())
                    except InputError as e:
                        print(e)

            # at this point we have all the refs for this fr_seg_ref
            starting = False
            best_match = None
            max = 0
            for i, en_seg_ref in enumerate(en_sefaria_refs):
                if i+1 == prev_seg_ref_found:
                    starting = True
                if starting:
                    en_sefaria_refs_in_curr_seg = [Ref(ref).normal() for ref in en_sefaria_refs[en_seg_ref]]
                    overlap = calc_overlap_score(en_sefaria_refs_in_curr_seg, fr_sefaria_refs_in_curr_seg)
                    if overlap > max:
                        max = overlap
                        best_match = i+1
            if best_match:
                if best_match not in aligned_text[sec_ref]:
                    aligned_text[sec_ref][best_match] = ""
                aligned_text[sec_ref][best_match] += fr_text + " "
                prev_seg_ref_found = best_match
            else:
                prev_seg_ref_found += 1
                if prev_seg_ref_found not in aligned_text[sec_ref]:
                    aligned_text[sec_ref][prev_seg_ref_found] = ""
                aligned_text[sec_ref][prev_seg_ref_found] += fr_text + " "

    return aligned_text

def align():
    for i, fr_sec_ref in enumerate(french_data):
        moreh_ref = fr_sec_ref.replace("Part 1", "Part 1,").replace("Part 2", "Part 2,") \
            .replace("Part 3", "Part 3,").replace("Guide for the Perplexed", "Moreh Nevukhim")
        our_guide_seg_ref = list(links_and_pos_by_seg_ref[moreh_ref].keys())[0]
        running_text = ""
        last_citation_found = None
        our_guide_links_and_word_counts = links_and_pos_by_seg_ref[moreh_ref]

        for fr_seg_ref in french_data[fr_sec_ref]:
            for citation in french_data[fr_sec_ref][fr_seg_ref]:
                french_ref, french_word_count, before_fr_text, fr_citation = citation
                try:
                    french_ref = Ref(french_ref.strip()).normal() if len(french_ref) > 0 else ""
                except InputError as e:
                    print(e)
                starting_to_look = False
                found = False
                matches_skipped = 0
                for temp_ref in our_guide_links_and_word_counts:
                    if not starting_to_look and temp_ref == our_guide_seg_ref:
                        starting_to_look = True
                    if starting_to_look:
                        for i, this_pair in enumerate(our_guide_links_and_word_counts[temp_ref]):
                            our_ref, our_word_count = this_pair
                            our_prev_ref = Ref(our_ref).prev_segment_ref()
                            our_next_ref = Ref(our_ref).next_segment_ref()
                            same_ref = french_ref == Ref(our_ref).normal()
                            if our_prev_ref:
                                same_ref = same_ref or our_prev_ref.normal() == french_ref
                            if our_next_ref:
                                same_ref = same_ref or our_next_ref.normal() == french_ref
                            if same_ref:
                                pos_ratio = float(french_word_count) / our_word_count
                                curr_text = running_text + " " + before_fr_text + " " + fr_citation
                                # num_english_words_in_match = get_num_english_words_from_X_to_Y(fr_sec_ref, last_citation_found, our_ref)
                                # match_ratio = float(curr_text.count(" "))/num_english_words_in_match
                                if 0.9 < pos_ratio < 1.5:  # and 0.9 < match_ratio < 6:
                                    found = True
                                    french_pos = fr_seg_ref.split(":")[-1]
                                    our_guide_seg_ref = temp_ref
                                    aligned[fr_sec_ref][our_guide_seg_ref] += curr_text
                                    running_text = ""
                                    last_citation_found = our_ref
                                    break
                            else:
                                matches_skipped += 1
                    if found:
                        break
                if not found:
                    running_text += before_fr_text + " " + fr_citation + " "

        if running_text:
            aligned[fr_sec_ref][our_guide_seg_ref] += running_text
            running_text = ""
    return aligned


def get_first_seg_ref():
    return ""


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
                links_and_pos[k].append((Ref(ref).normal(), loc + prev_loc))
            except:
                pass
            prev_loc += loc
    return links_and_pos


def get_guide_links_and_pos_by_seg_ref():
    links_and_pos = {}
    for i, k in enumerate(sentences_per_chapter.keys()):
        if k == "":
            continue
        sec_ref = Ref(k)
        sub_refs = sec_ref.all_subrefs()
        links_and_pos[k] = {}
        prev_loc = 0
        for sub_ref in sub_refs:
            prev_find = 0
            moreh_text = sub_ref.text('en').text
            citations = library.get_refs_in_string(moreh_text)
            links_and_pos[k][sub_ref.normal()] = []
            if not citations:
                prev_loc = len(moreh_text.split())
            else:
                for i, ref in enumerate(citations):
                    # curr_text = " ".join(moreh_text.split()[prev_loc:])
                    chr_pos = moreh_text.find(ref)
                    loc = len(moreh_text[prev_find:chr_pos].split())
                    try:
                        Ref(ref)
                        links_and_pos[k][sub_ref.normal()].append((ref, loc + prev_loc))
                    except Exception as e:
                        print(e)
                    prev_loc += loc
                    prev_find = chr_pos
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
        curr_val = words_per_chapter[k] / our_guide_words[k]
        if curr_val < min:
            min = curr_val
        if curr_val > max:
            max = curr_val
        avg += curr_val
        total += 1
    print("Average: {}".format(float(avg) / total))
    print("Range: {} to {}".format(min, max))
    return our_guide_sentences, our_guide_words


def add_citations(orig_row, row, num_words_citation, before_text, french_citation_text, sefaria_ref):
    match = re.search(".*?\d+\.\d+\.\d+", orig_row[0])
    if not match:
        return row
    if "Part" not in row[0]:
        row[0] = row[0].replace(".", ", ", 1)
        row[0] = re.sub("(\d+), ", "Part \g<1>, ", row[0])
    section_ref = Ref(row[0]).section_ref().normal()
    if section_ref not in french_by_sec:
        french_by_sec[section_ref] = []
        french_data[section_ref] = {}
    french_by_sec[section_ref].append(sefaria_ref)
    if Ref(row[0]).normal() not in french_data[section_ref]:
        french_data[section_ref][Ref(row[0]).normal()] = []
    french_data[section_ref][Ref(row[0]).normal()].append(
        (sefaria_ref, num_words_citation, before_text, french_citation_text))
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
        overlap = set(poss_links).issubset(
            set(our_guide_links[ref]))  # set(poss_links).intersection(our_guide_links[ref]) > 0
        if overlap:

            corresponding[ref] = ref


        else:
            prev_5 = None
            next_5 = None
            others_to_check = []
            corresponding[ref] = []
            for i in range(1, 6):
                if r + i < len(links):
                    others_to_check.append(list(links.keys())[r + i])
                if r - i >= 0:
                    others_to_check.append(list(links.keys())[r - i])
            for l in others_to_check:
                overlap = set(poss_links).intersection(l)
                if len(overlap) > 0:
                    print("Found match")
                    corresponding[ref] += l
    return corresponding

def prep_and_post(aligned_text):
    for sec_ref in aligned_text:
        aligned_text[sec_ref] = convertDictToArray(aligned_text[sec_ref], empty="")
        send_text = {
            "versionTitle": "partially aligned [fr]",
            "versionSource": "https://www.sefaria.org",
            "text": aligned_text[sec_ref],
            "language": "en"
        }
        post_text(sec_ref, send_text)

def repair_segments(aligned):
    for sec_ref in aligned:
        prev_seg_ref = None
        for seg_ref, line in aligned[sec_ref].items():
            #first_letter_upper_case = re.match("\. [A-ZÀ-Ÿ]{1}", bleach.clean(line, tags="", strip=True).strip())
            first_letter_upper_case = re.search("\. ([A-ZÀ-Ÿ]{1})", line)
            if seg_ref.endswith(":1") is False and first_letter_upper_case:
                #split on first capital letter
                first_letter_upper_case = first_letter_upper_case.group(1)
                first_letter_upper_case_pos = len(re.split("\. [A-ZÀ-Ÿ]{1}", line)[0]) + 2
                aligned[sec_ref][prev_seg_ref] += line[:first_letter_upper_case_pos]
                aligned[sec_ref][seg_ref] = line[first_letter_upper_case_pos:]
            prev_seg_ref = seg_ref
    return aligned

def get_num_english_words_from_X_to_Y(sec_ref, last_citation_found, our_ref):
    moreh_text = " ".join(Ref(sec_ref).text('en').text)
    last_citation_found_pos = moreh_text.find(last_citation_found, 1) if last_citation_found else 0
    our_ref_pos = moreh_text.find(our_ref)
    assert our_ref_pos > last_citation_found_pos >= 0
    return moreh_text[last_citation_found_pos:our_ref_pos].count(" ") + 1

    # try instead of resetting each time we find, because this relies on assumptions,
    # just start at each position and go up and down 5 - 10 spots looking for all matches and record all


def get_ref(l):
    guide_pos = 0 if l.refs[0].startswith("Guide for the Perplexed,") else 1
    guide_ref = l.refs[guide_pos]
    other_ref = l.refs[1 - guide_pos]
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
                # if you move Guide back, you're saying that French version is split into two,
                if curr_siman > 1:
                    curr_siman -= 1
                    ref = "{} {}".format(guide, curr_siman)
                    found = test(poss_links, ref, corresponding)
                    if not found:
                        # if you move Guide forward, you're saying Guide is split
                        curr_siman += 2
                        ref = "{} {}".format(guide, curr_siman)
                        found = test(poss_links, ref, corresponding)
                        if not found:
                            corresponding[ref] = "Not found"
                            curr_siman -= 1
    return corresponding


def get_proper_ref(fr_seg_ref, aligned):
    sec_ref = seg_ref.split(":")[0]
    en_seg_refs = aligned[sec_ref]
    if fr_seg_ref in en_seg_refs:
        return fr_seg_ref
    else:
        last_one = list(en_seg_refs.keys())[-1]
        return last_one

def print_to_file(aligned, file):
    with open(file, 'w') as new_f:
        writer = csv.writer(new_f)
        for sec_ref in aligned:
            for seg_ref in aligned[sec_ref]:
                writer.writerow([seg_ref, aligned[sec_ref][seg_ref]])

def convert_french_ref_to_sefaria_ref(french_ref, row):
    french_ref = french_ref[1:-1]  # remove parenthesis
    title = french_ref.replace(french_ref.split()[-2] + " " + french_ref.split()[-1], "").strip()
    french_ref = french_ref.split()
    french_ref[-2] = str(roman_to_int(french_ref[-2].replace(",", "")))
    try:
        title = title.replace(",", "")
        loc = fr_books.index(title)
        actual_book = en_tanakh[loc]
        title = actual_book
    except ValueError as e:
        title = title.replace("Micha", "Micah").replace("Isaïe.", "Isaiah") \
            .replace("Ézéch.", "Ezekiel").replace("Ps.", "Psalms").replace("Cf. Job", "Job").replace("I Rois",
                                                                                                     "I Kings") \
            .replace("Exod.", "Exodus").replace("Nom.", "Numbers").replace("Jérém.", "Jeremiah") \
            .replace("Ecclesiaste", "Ecclesiastes") \
            .replace("Deutéron.", "Deuteronomy").replace("I Chron.", "I Chronicles").replace("Habac.",
                                                                                             "Habakkuk") \
            .replace("Lévit.", "Leviticus").replace("Prov.", "Proverbs").replace("Lament.", "Lamentations") \
            .replace("I Sam.", "I Samuel").replace("II Sam.", "II Samuel").replace("II Chron.", "II Chronicles") \
            .replace("Malach.", "Malachi").replace("Deutér.", "Deuteronomy").replace("Nomb.", "Numbers") \
            .replace("Nombr.", "Numbers").replace("Lév.", "Leviticus").replace("Jér.", "Jeremiah").replace(
            'Ecclés.', "Ecclesiastes").replace("Jésaïe", "Isaiah") \
            .replace("Deutér", "Deuteronomy").replace("Malach.", "Malachi").replace("Ezéch", "Ezekiel").replace(
            "Deulér", "Deuteronomy").replace("Gen.", "Genesis") \
            .replace("Jos.", "Joshua").replace("Dan.", "Daniel").replace("Deuter.", "Deuteronomy").replace(
            "Hos.", "Hoshea") \
            .replace("Cantique des cant.", "Cantique des Cant.").replace("Cantique des Cant.", "Song of Songs") \
            .replace("Roi", "Rois").replace("Deut.", "Deuteronomy").replace("'Jérém.'", "Jeremiah") \
            .replace("Sam.", "Samuel").replace("Hag.", "Haggai").replace("Hosée", "Hosea")
        actual_book = title
    chapter_and_segment = ":".join(french_ref[-2:])
    sefaria_ref = "{} {}".format(actual_book, chapter_and_segment)
    return sefaria_ref


def check_simanim(aligned):
    siman_probs = {}
    for siman in aligned:
        for ref in aligned[siman]:
            if len(aligned[siman][ref]) == 0:
                if siman not in siman_probs:
                    siman_probs[siman] = 0
                siman_probs[siman] += 1
    print('done')


def extract_french_data():
    with open("new_full_text.csv", 'w') as new_f:
        writer = csv.writer(new_f)
        prev_row = ""
        with open("Moreh Wout Footnotes.csv", 'r') as f:
            rows = list(csv.reader(f))
            for r, row in enumerate(rows):
                orig_row = list(row)
                if "Part" not in row[0]:
                    ch = row[0].replace(".", ", ", 1)
                    ch = re.sub("(\d+), ", "Part \g<1>, ", ch)
                ch = ":".join(ch.split(".")[:-1])
                if ch not in words_per_chapter:
                    num_words = 0
                    words_per_chapter[ch] = 0
                    sentences_per_chapter[ch] = 0
                words_per_chapter[ch] += len(row[1].split())
                sentences_per_chapter[ch] += len(re.findall("\. [A-ZÀ-Ÿ]{1}", row[1])) + 1 + len(
                    re.findall('\.\"', row[1]))
                split_up_by_citations = re.split("(\([A-ZÀ-ÿa-z., ]{2,15} [ILVXC,]+ \d+\))", row[1])
                # split_up_by_citations is an array of comments followed by their citations if they have them such as:
                # ["Hello", "(Genesis 1:2)", "Goodbye"]
                i = 0
                while True:
                    comment = split_up_by_citations[i * 2]
                    next_one = (i * 2) + 1
                    num_words += len(comment.split())
                    if (i * 2) < len(split_up_by_citations) - 1:
                        citation = split_up_by_citations[next_one]
                        i += 1
                        sefaria_ref = convert_french_ref_to_sefaria_ref(citation, row)
                        assert citation in row[1]
                        row[1] = row[1].replace(citation, sefaria_ref, 1)
                        row = add_citations(orig_row, row, num_words, comment, citation, sefaria_ref)
                    else:
                        row = add_citations(orig_row, row, num_words, comment, "", "")
                        break

                prev_row = row

                writer.writerow(row)


extract_french_data()
our_guide_links = {}
our_guide_seg_links = {}
segs = Ref("Guide for the Perplexed, Part 1").all_segment_refs() + Ref(
    "Guide for the Perplexed, Part 2").all_segment_refs() + Ref("Guide for the Perplexed, Part 3").all_segment_refs()
secs = Ref("Guide for the Perplexed, Part 1").all_subrefs() + Ref(
    "Guide for the Perplexed, Part 2").all_subrefs() + Ref("Guide for the Perplexed, Part 3").all_subrefs()

our_guide_words, our_guide_sentences = get_guide_words_and_sentences()
aligned = {}
for ref in secs:
    sec_ref_segs = ref.all_subrefs()
    aligned[ref.normal()] = {}
    for r in sec_ref_segs:
        aligned[ref.normal()][r.normal()] = ""

for ref in segs:
    our_guide_seg_links[ref.normal()] = [get_ref(l) for l in LinkSet(ref)]

# links_and_pos = get_guide_links_and_pos()
# with open('our_guide_links_and_pos.json', 'r') as f:
#     links_and_pos = json.load(f)
# links_and_pos_by_seg_ref = get_guide_links_and_pos_by_seg_ref()
# with open("our_guide_links_and_pos_by_seg_ref.json", 'w') as f:
#     json.dump(links_and_pos_by_seg_ref, f)
with open("our_guide_links_and_pos_by_seg_ref.json", 'r') as f:
    links_and_pos_by_seg_ref = json.load(f)

# #steps: 1) start with first citation, set our_guide_seg_ref to first seg ref in our guide,
# #       2) look for first citation in our_guide_ref's citations and check word_count ratio
# #       3) if found and ratio good, add text to aligned[our_guide_seg_ref]
# #       4) if not found, look in next our_guide_seg_ref if there is a next ref until we
# #       exhaust all seg_refs in our_guide_sec_ref
# #       5) if found and ratio good in one of the next our_guide_seg_refs, we add text to
# #       aligned[our_guide_seg_ref] and continue looking for next citation from this our_guide_seg_ref onward
# #       6) if not found anywhere or ratio not good, simply add text to running_text
# #       7) if at end there is running_text, add running_text to aligned[our_guide_seg_ref]
# #       8) in case of chapter 5, where ratio doesn't help remove false positive, compare directly number of french
# #       words being added to aligned to number of english words from last citation found
# #
# #
# aligned = align()
# aligned = repair_segments(aligned)
# print_to_file(aligned, "aligned Moreh -- first pass.csv")
#check_simanim(aligned)
text = partial_align()
prep_and_post(text)