#encoding=utf-8
import django
django.setup()
from sefaria.model import *
from linking_utilities.dibur_hamatchil_matcher import *
from sources.functions import *
import codecs
def do_match(line_n, results, current_perek, current_daf, last_daf, lines):
    base_text = TextChunk(current_daf.to(last_daf), lang='he')
    print base_text
    print len(current_perek)
    match_results = match_ref(base_text, current_perek, lambda x: x.split())["matches"]
    print match_results
    for i, result in enumerate(match_results):
        if result:
            result = result.normal()
        results[line_n-len(current_perek)+i] = result



if __name__ == "__main__":
    perek = -1
    results = {}
    index = library.get_index("Yevamot")
    alt_struct = index.alt_structs["Chapters"]["nodes"]
    skip_next = False
    current_perek = []
    last_daf = None #last daf of perek
    with open("text") as f:
        lines = list(f)
        for line_n, line in enumerate(lines):
            # if skip_next:
            #     skip_next = False
            line = line.decode('utf-8')
            if line.startswith(u"@פרק"):
                if current_perek:
                    do_match(line_n, results, current_perek, daf, last_daf, lines)
                    current_perek = []
                perek += 1
                wholeRef = Ref(alt_struct[perek]["wholeRef"])
                daf = wholeRef.starting_ref().section_ref()
                last_daf = wholeRef.ending_ref()
                results[line_n+1] = daf.normal()
                #skip_next = True
            else:
                relevant_words = u" ".join(line.split()[0:5])
                current_perek.append(relevant_words)

    results = [[lines[k].decode('utf-8'), results[k]] for k in sorted(results.keys())]
    print results
    with codecs.open("results.csv", 'w', encoding='utf-8') as f:
        for result in results:
            f.write(u"{},{}\n".format(result[1],result[0]))
