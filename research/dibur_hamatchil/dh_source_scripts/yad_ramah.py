# -*- coding: utf-8 -*-
from sefaria.model import *
from data_utilities import dibur_hamatchil_matcher as dhm
import unicodecsv, codecs, json
import regex as re



def dh_extraction_method(string):
    stop_words = [u'פירוש',u'פי׳',u'פירשו',u'ופירש',u'פרש״י',u'פירש״י',u'כלומר',u'וכו׳',u'וא״ת',u'ק״ל']
    return string

def rashi_filter(string):
    return True

def match():
    mes = "Sanhedrin"
    yr  = library.get_index("Yad Ramah on {}".format(mes))
    gem = library.get_index("{}".format(mes))

    yrRefList  = yr.all_section_refs()[:5]
    gemRefList = gem.all_section_refs()
    gemInd = 0

    num_matched = 0
    num_searched = 0

    link_list = []
    log = open("yad_ramah.log","w")
    rt_log = open("yad_ramah_rashei_tevot.csv","w")
    rt_log_csv = unicodecsv.DictWriter(rt_log, fieldnames=["abbrev","expanded","context_before","context_after"])
    rt_log_csv.writeheader()
    for yrRef in yrRefList:
        while gemRefList[gemInd].sections[0] != yrRef.sections[0]:
            gemInd += 1
        gemRef = gemRefList[gemInd]
        print "----- {} -----".format(gemRef)
        log.write("----- {} -----\n".format(gemRef))

        yrtc = TextChunk(yrRef,'he')

        # let's extend the range of gemara_tc to account for weird rashba stuff
        num_refs_to_expand = 2

        gemara_ref_before = gemRef.prev_section_ref()
        gemara_ref_after = gemRef.next_section_ref()
        if gemara_ref_before and len(gemara_ref_before.all_subrefs()) >= num_refs_to_expand:
            gemRef = gemara_ref_before.all_subrefs()[-num_refs_to_expand].to(gemRef)
        if gemara_ref_after and len(gemara_ref_after.all_subrefs()) >= num_refs_to_expand:
            gemRef = gemRef.to(gemara_ref_after.all_subrefs()[num_refs_to_expand - 1])

        gemtc = TextChunk(gemRef,'he')

        def base_tokenizer(string):
            return dhm.get_maximum_dh(gemtc,string,max_dh_len=6)


        matched = dhm.match_ref(gemtc, yrtc, base_tokenizer=base_tokenizer,
                                                    dh_extract_method=dh_extraction_method, verbose=True,
                                                    with_abbrev_matches=True, rashi_filter=rashi_filter)

        ref_map = [(base, comment) for base, comment in zip(matched['matches'], matched['comment_refs'])]
        abbrevs = [am for seg in matched['abbrevs'] for am in seg]
        for am in abbrevs:
            rt_log_csv.writerow(
                {'abbrev': dhm.cleanAbbrev(am.abbrev), 'expanded': u' '.join(am.expanded),
                 'context_before': u' '.join(am.contextBefore), 'context_after': u' '.join(am.contextAfter)})

        temp_link_list = [l for l in ref_map if not l[0] is None and not l[1] is None]
        link_list += temp_link_list
        unlink_list = [ul[1] for ul in ref_map if ul[0] is None or ul[1] is None]
        for r in ref_map:
            if not r[0] is None: num_matched += 1

        num_searched += len(ref_map)

        print "MATCHES - {}".format(ref_map)
        print "ACCURACY - {}%".format(round(1.0 * num_matched / num_searched, 5) * 100)
        log.write("MATCHES - {}\n".format(temp_link_list))
        log.write("NOT FOUND - {}\n".format(unlink_list))
        log.write("ACCURACY - {}%\n".format(round(1.0 * num_matched / num_searched, 5) * 100))
    doc = {"link_list": [[link[0].normal(), link[1].normal()] for link in link_list]}
    fp = codecs.open("yad_ramah_links.json", "w", encoding='utf-8')
    json.dump(doc, fp, indent=4, encoding='utf-8', ensure_ascii=False)
    fp.close()
    log.close()
    rt_log.close()

match()