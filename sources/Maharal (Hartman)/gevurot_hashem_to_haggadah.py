from sources.functions import *
import bleach
from data_utilities.dibur_hamatchil_matcher import *
def dher(str):
    # re.split("\.;:", str)
    bold_match = re.search('^<b>(.*?)</b>', str)
    str = bleach.clean(str, strip=True, tags=[])
    first_sentence = " ".join(str.split()[:6])
    quote_match = re.search('^\"(.*?)\"', str) or re.search('\"(.*?)\"', str)

    if quote_match:
        return quote_match.group(1).replace("וכו\'", "").replace("וגו\'", "").strip()
    elif bold_match:
        return bold_match.group(1)
    else:
        return first_sentence
    # elif bold_match:
    #     # print("BOLD")
    #     # print(bold_match.group(1))
    #     return bold_match.group(1)
    # else:
    #     return first_sentence

def create_report():
    ls = LinkSet({"$and": [{"refs": {"$regex": "^Gevurot Hashem"}}, {"refs": {"$regex": "^Pesach Haggadah"}}]})
    print(ls.count())
    with open("gevurot_hashem_report.csv", 'w') as f:
        writer = csv.writer(f)
        for l in ls:
            writer.writerow(['"{}"'.format(l.refs[0]), l.refs[1]])

def get_ref_in_map(pesach_map, pesach_refs, pos):
    middle = int(len(pesach_map)/2)
    if pos >= pesach_map[middle] and pos < pesach_map[middle+1]:
        return pesach_refs[middle]
    elif pos > pesach_map[middle]:
        return get_ref_in_map(pesach_map[middle:], pesach_refs[middle:], pos)
    elif pos < pesach_map[middle]:
        return get_ref_in_map(pesach_map[:middle+1], pesach_refs[:middle+1], pos)
    else:
        raise Exception("Shouldn't happen")
    # for i, loc_and_ref in enumerate(zip(pesach_map[0], pesach_map[1])):
    #     loc, ref = loc_and_ref
    #     next_loc = pesach_map[0][i+1]
    #     next_ref = pesach_map[1][i+1]
    #     if tuple[0] >= loc:
    #         while tuple[1] > next_loc:
    #             next_loc




links = []
results = {}

i = library.get_index("Pesach Haggadah")
tokenizer = lambda x: bleach.clean(x, strip=True, tags=[]).split()
pesach_map = i.text_index_map(tokenizer=tokenizer)


with open("results.csv", 'w') as f:
    writer = csv.writer(f)
# need to match Gevurot Hashem 50 to 62 to Magid
    magid = [ref.text('he').text for ref in library.get_index("Pesach Haggadah").all_segment_refs()]# if "Magid" in ref.normal()]
    magid = " ".join(magid)
    magid = tokenizer(magid)

    for chapter in library.get_index("Gevurot Hashem").all_section_refs():
        match = re.search("Gevurot Hashem (\d+)", chapter.normal())
        if match:
            if 50 <= int(match.group(1)) <= 62:
                comments = chapter.text('he').text
                results[match.group(1)] = []
                matches = match_text(magid, comments, dh_extract_method=dher)
                for i, tuple in enumerate(matches["matches"]):
                    if tuple != (-1, -1) and tuple[0] != tuple[1]:
                        gevurot_ref = match.group(0) + ":" + str(i+1)
                        pesach_start_ref = get_ref_in_map(pesach_map[0], pesach_map[1], tuple[0])
                        pesach_end_ref = get_ref_in_map(pesach_map[0], pesach_map[1], tuple[1])
                        try:
                            pesach_ref = pesach_start_ref.to(pesach_end_ref).normal()
                            links.append({"refs": [gevurot_ref,pesach_ref], "auto":  True,
                                     "type": "Commentary", "generated_by": "Haggadah_to_Gevurot"})
                        except Exception as e:
                            print(e)


print(len(links))
post_link(links)
