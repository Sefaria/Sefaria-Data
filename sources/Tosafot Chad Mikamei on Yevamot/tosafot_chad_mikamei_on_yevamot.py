#encoding=utf-8
import django
django.setup()
from sefaria.model import *
from data_utilities.dibur_hamatchil_matcher import *

def do_match(current_perek, current_daf, last_daf):
    base_text = TextChunk(current_daf.to(last_daf), lang='he')
    match_results = match_ref(base_text, current_perek, lambda x: x.split())
    pass

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
            print line
            if skip_next:
                skip_next = False
            elif line.startswith("@פרק"):
                if current_perek:
                    do_match(current_perek, daf, last_daf)
                    current_perek = []
                perek += 1
                wholeRef = Ref(alt_struct[perek]["wholeRef"])
                daf = wholeRef.starting_ref().section_ref()
                last_daf = wholeRef.ending_ref()
                results[line_n+1] = daf
                skip_next = True
            else:
                relevant_words = line.split(".")[0] if "." in line else " ".join(line.split()[0:10])
                current_perek.append(relevant_words.decode('utf-8'))
    print results