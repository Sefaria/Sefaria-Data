from docx2python import docx2python
from sources.functions import *
ALLOWED_TAGS = list(ALLOWED_TAGS)
ALLOWED_TAGS.remove("span")

def get_ftnotes(html):
    def add_to_dict(content):
        content = bleach.clean(content, strip=True, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS)
        content = content.replace("&lt;", "").replace("&gt;", "").strip()
        content = re.sub("^<b>%(.*?)</b>$", "", content)
        if len(content) > 0:
            ftnotes_dict[num].append(content)

    ftnotes_dict = defaultdict(list)
    for x in html.footnotes_runs[0][0]:
        strings = flatten_list(x)
        if len(strings) > 1:
            m = re.search("^footnote\-?(\d+)\)(.*?)$", strings[0])
            if m:
                content = m.group(2).strip()
                num = int(m.group(1))
                assert num not in ftnotes_dict
                add_to_dict(content)
                for content in strings[1:]:
                    add_to_dict(content)
    for x, y in ftnotes_dict.items():
        ftnotes_dict[x] = "\n".join(y)
    return ftnotes_dict

def get_body(html):
    body = []
    for x in html.body_runs[0][0][0]:
        for p in x:
            p = bleach.clean(p, strip=True, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS)
            if len(p) > 0:
                body.append(p)
    return body


def divide_by_daf(body):
    dafs = {}
    curr = None
    for x in body:
        if re.search("^<b>%(.*?)</b>", x):
            curr = re.search("^<b>%(.*?)</b>", x).group(1)
            dafs[curr] = []
        else:
            assert curr is not None
            dafs[curr].append(x)
    return dafs


def divide_by_comment(daf):
    comments = {}
    curr = 0
    for c in daf:
        c = c.strip()
        if c == "#":
            if curr in comments:
                comments[curr] = "".join(comments[curr])
            curr += 1
            comments[curr] = []
        elif len(c) > 0:
            comments[curr].append(c)
    if curr in comments:
        comments[curr] = "".join(comments[curr])
    return comments

files = [f for f in os.listdir(".") if f.endswith("docx")]
actual_dafs = {}
for f in files:
    html = docx2python(f, html=True)
    ftnotes = get_ftnotes(html)
    body = get_body(html)
    dafs = divide_by_daf(body)
    for daf in dafs:
        comments = divide_by_comment(dafs[daf])
        for c, comm in comments.items():
            comment_ftnotes = re.findall('(----footnote(\d+)----)', comments[c])
            for comment_ftnote in comment_ftnotes:
                actual_ftnote = ftnotes[int(comment_ftnote[1])]
                actual_ftnote = f"<sup class='footnote-marker'>{int(comment_ftnote[1])}</sup><i class='footnote'>{actual_ftnote}</i>"
                comments[c] = comments[c].replace(comment_ftnote[0], actual_ftnote)
        dafs[daf] = comments
    for k in dafs:
        actual_dafs[getGematria(k)] = convertDictToArray(dafs[k])

root = JaggedArrayNode()
root.add_primary_titles("Derush Al HaTorah", "דרוש על התורה")
root.key = "Derush Al HaTorah"
indx = {'title': root.key, 'categories': []}
versionTitle = 'Derush al HaTorah, with footnotes and annotations by Rabbi Yehoshua D. Hartman, Machon Yerushalyim, 2023'
versionSource = "https://www.nli.org.il/he/books/NNL_ALEPH003874699/NLI"
