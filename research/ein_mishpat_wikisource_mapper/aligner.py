import codecs, json, re, bisect, bleach, unicodecsv
from sefaria.model import *
from data_utilities import dibur_hamatchil_matcher

mesechtot = ["Sanhedrin"]

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

out_rows = []
for mes in mesechtot:
    mes_ind = library.get_index(mes)
    for daf_ref in mes_ind.all_section_refs():
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
        matched = dibur_hamatchil_matcher.match_ref(daf_ref.text("he"), comments_scraped, base_tokenizer,  with_abbrev_matches=True, with_num_abbrevs=False, place_consecutively=False)

        try:
            super_sefaria_list = [matched["matches"][sc].normal() for sc in super_comment_list]
        except AttributeError:
            print "OH NO!", daf_ref, matched["matches"]
            super_sefaria_list = [matched["matches"][sc].normal() if matched["matches"][sc] is not None else None for sc in super_comment_list]

        wiki_snippets = [u" <{}> ".format(bleach.clean(sim, strip=True, tags=[])).join([comments_scraped[sc-1],
                         comments_scraped[sc]]) if sc != 0 else u" <{}> {}".format(bleach.clean(sim, strip=True, tags=[]
                         ), comments_scraped[sc]) for sim, sc in zip(daf_scraped["super_simanim"], super_comment_list)]
        out_rows += [
            {"Index": ind,
             "Daf": daf_ref.normal(),
             "Siman": bleach.clean(sim, strip=True, tags=[]),
             "Siman Ref": Ref(sim_ref).starting_ref().normal() if sim_ref is not None else u"N/A",
             "Wiki Snippet": ws
             } for ind, sim, sim_ref, ws in zip(xrange(len(out_rows)+1, len(out_rows)+1+len(super_sefaria_list)),
                                            daf_scraped["super_simanim"], super_sefaria_list, wiki_snippets)
        ]

f = open("aligner.csv", "wb")
writer = unicodecsv.DictWriter(f, ["Index", "Daf", "Siman", "Siman Ref", "Wiki Snippet"])
writer.writeheader()
writer.writerows(out_rows)

