from sources.functions import *

def find_occurrences(X, Z, Y):
    # Define the regular expression pattern
    # It looks for the presence of 'Z' in the last 1-6 words before 'X' and then matches 'X' followed immediately by parentheses
    pattern = rf'\b(?:\w+\W+)?(?:\w+\W+)?(?:\w+\W+)?(?:\w+\W+)?(?:\w+\W+)?(?:\w+\W+)?\b{Z}\b.*?\b{X}\s*\([^)]+\)'

    # Use finditer to find all non-overlapping matches in the string Y
    matches = re.finditer(pattern, Y, re.IGNORECASE | re.DOTALL)

    # Extract all occurrences
    occurrences = [(match.group(), match.start(), match.end()) for match in matches]

    return occurrences

def build_zohar_parasha_regex():
    i = library.get_index("Zohar")
    return "|".join([x.get_titles('he')[0] for x in i.nodes.children])


def extract_with_six_words(X, Y):
    # Initialize an empty list to collect the phrases
    phrases = []
    words = Y.split()  # Split the string into a list of words
    length = len(words)

    # Loop through each word in the list
    for i in range(length):
        word = words[i]
        if X in word and i + 8 < length:
            phrase = ' '.join(words[i:i + 9])
            phrases.append(phrase)

    return phrases

def find_ref_daf(needle, start, refs, title):
    start_loc = AddressTalmud(0).toNumber('en', start)
    for i, ref in enumerate(refs):
        loc = start_loc + i
        loc_daf = AddressTalmud.toStr('en', loc)
        if needle == loc_daf and title in refs[i]:
            return refs[i]
    return None

probs = set()

finds = defaultdict(list)
def find_zohar(segment_str, tref, he_tref, version):
    global finds
    global probs
    #match_ref_interface()(base_ref, comm_ref, comments, base_tokenizer, dh_extract_method, vtitle="", generated_by="", padding=False):
    if ("""זוה"ק""" or """זה"ק""" in segment_str) and ("(" in segment_str or "[" in segment_str):
        segment_str = bleach.clean(segment_str, strip=True)
        phrases = extract_with_six_words("""זה"ק""", segment_str)
        phrases += extract_with_six_words("""זוה"ק""", segment_str)
        for phrase in phrases:
            matches = re.findall(regex, phrase)
            for m in matches:
                for x in re.findall(re.escape(m)+"\s\S*?\)", segment_str):
                    daf = x.split()[-1].replace(')', '').replace("(", "")
                    term_name = None
                    try:
                        term_name = " ".join(x.split()[:-1]).replace('בחקותי', "בחוקתי")
                        term_name = Term().load_by_title(term_name).name
                    except Exception as e:
                        probs.add(term_name)
                        continue
                    try:
                        daf = AddressTalmud(0).toStr('en', AddressTalmud(0).toNumber('he', daf))
                    except Exception as e:
                        probs.add(daf)
                        continue
                    dh_pos = segment_str.find(x)+len(x)
                    if dh_pos + 6 >= len(segment_str):
                        continue
                    else:
                        #dh = re.search("\S{2,}\s\S{2,}\s\S{2,}", segment_str[dh_pos:]).group(0)
                        segment_str_with_dh = bleach.clean(segment_str[dh_pos:], strip=True, tags=[])
                        segment_str_with_dh = re.sub(r'\(.*?\)', "", segment_str_with_dh)
                        dh = re.search(r'(\b\w+)(?:\W+\b\w+){0,5}', segment_str_with_dh).group(0).split("וכו'")[0].split(".")[0].split(",")[0]
                        if len(dh) < 2:
                            continue
                        #print(dh)
                    finds[tref].append((term_name, daf, dh))

regex = build_zohar_parasha_regex()
for b in library.get_indexes_in_category("Izhbitz"):
    for v in library.get_index(b).versionSet():
        print(v)
        v.walk_thru_contents(find_zohar)
i = library.get_index("Zohar")
print(probs)
new_finds = defaultdict(set)
for ref in finds:
    match = None
    for ref_title, ref_daf, dh in finds[ref]:
        failure = True
        for vol in i.alt_structs["Daf"]["nodes"]:
            if match:
                break
            for parasha in vol["nodes"]:
                if match:
                    break
                if "startingAddress" in parasha:
                    title = [x['text'] for x in parasha['titles'] if x['lang'] == 'he'][0]
                    m = find_ref_daf(ref_daf, parasha["startingAddress"], parasha["refs"], ref_title)
                    if m:
                        match = m
                        break
                else:
                    for parasha2 in parasha["nodes"]:
                        try:
                            title = [x['text'] for x in parasha2['titles'] if x['lang'] == 'en'][0]
                        except:
                            title = parasha2["wholeRef"].replace("Zohar, ", "").split()[0]
                        m = find_ref_daf(ref_daf, parasha2["startingAddress"], parasha2["refs"], ref_title)
                        if m:
                            match = m
                            break
        new_finds[ref].add((match, dh))
        match = None
links = []
total = 0
successes = 0
for hasidic_ref in new_finds:
    for zohar_ref, dh in new_finds[hasidic_ref]:
        if zohar_ref is not None:
            results = match_ref(Ref(zohar_ref).text('he'), [dh], lambda x: x.split())
            if results['matches'][0] is not None:
                links.append({"generated_by": "izbhiz_to_zohar", "auto": True, "type": "commentary", "refs": [results["matches"][0].normal(), hasidic_ref]})
print(successes, total)
for l in links:
    try:
        Link(l).save()
    except Exception as e:
        print(e)

