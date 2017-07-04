import codecs, json, re, bisect, bleach
from sefaria.model import *
from data_utilities import dibur_hamatchil_matcher

mesechtot = ["Sanhedrin", "Gittin"]

def base_tokenizer(base_str):
    base_str = bleach.clean(base_str, tags=[], strip=True)
    for match in re.finditer(ur'\(.*?\)', base_str):
        if library.get_titles_in_string(match.group()) and len(match.group().split()) <= 5:
            base_str = base_str.replace(match.group(), u"")
            # base_str = re.sub(ur"(?:\(.*?\)|<.*?>)", u"", base_str)
    word_list = re.split(ur"\s+", base_str)
    word_list = [w for w in word_list if w]  # remove empty strings
    return word_list

def validate_matches(matches):
    report = u""
    for i, m in matches:
        pass

with codecs.open("scraper.out", "rb", encoding='utf8') as f:
    wiki_scraped = json.load(f, encoding='utf8')

out_obj = {}
for mes in mesechtot:
    mes_ind = library.get_index(mes)
    for daf_ref in [Ref("Sanhedrin 67a")]:  # mes_ind.all_section_refs():
        print daf_ref
        daf_scraped = wiki_scraped[daf_ref.book][daf_ref.normal()]
        words_scraped = daf_scraped["text"].split()
        word_start_list = []
        matched_iter = re.finditer(ur"\s+([^ ])", daf_scraped["text"])
        for m in matched_iter:
            word_start_list += [m.start()]

        super_word_list = [bisect.bisect_right(word_start_list, si) for si in daf_scraped["super_indices"]]
        super_comment_list = []
        comments_scraped = []
        chunk_size = 20
        super_chunk_size = 5
        curr_word = 0
        curr_super_word = 0
        while curr_word < len(words_scraped):
            possible_range = range(curr_word, curr_word+chunk_size)
            if curr_super_word < len(super_word_list) and super_word_list[curr_super_word] - 1 in possible_range:
                comments_scraped += [u" ".join(words_scraped[curr_word:super_word_list[curr_super_word]])]
                curr_word = super_word_list[curr_super_word]
            elif curr_super_word < len(super_word_list) and super_word_list[curr_super_word] in possible_range:
                temp_chunk = min(super_word_list[curr_super_word+1] - curr_word, super_chunk_size) if curr_super_word + 1 < len(super_word_list) else super_chunk_size
                comments_scraped += [u" ".join(words_scraped[curr_word:curr_word + temp_chunk])]
                super_comment_list += [len(comments_scraped)-1]
                curr_word += temp_chunk
                curr_super_word += 1
            else:
                comments_scraped += [u" ".join(words_scraped[curr_word:curr_word + chunk_size])]
                curr_word += chunk_size
        matched = dibur_hamatchil_matcher.match_ref(daf_ref.text("he"), comments_scraped, base_tokenizer,  with_abbrev_matches=True, with_num_abbrevs=False)

        try:
            super_sefaria_list = [matched["matches"][sc].normal() for sc in super_comment_list]
        except AttributeError:
            print "OH NO!", daf_ref, matched["matches"]
            super_sefaria_list = [matched["matches"][sc].normal() if matched["matches"][sc] is not None else None for sc in super_comment_list]
        daf_obj = {
            "super_indices": daf_scraped["super_indices"],
            "super_simanim": daf_scraped["super_simanim"],
            "super_refs": super_sefaria_list
        }
        try:
            out_obj[daf_ref.book][daf_ref.normal()] = daf_obj
        except KeyError:
            out_obj[daf_ref.book] = {}
            out_obj[daf_ref.book][daf_ref.normal()] = daf_obj


        # if None in matched["matches"]:
        #     for i, (m, c) in enumerate(zip(matched["matches"], matched["match_text"])):
        #         if m is None:
        #             print daf_ref, m, c[1]

f = codecs.open("aligner.out", "wb", encoding='utf8')
json.dump(out_obj, f, ensure_ascii=False, indent=4)
f.close()
