# encoding=utf-8



import re
import codecs
import urllib
import json
from sefaria.model import *
from sefaria.model.schema import *
from sefaria.system.exceptions import BookNameError

def str2addressType(atype, num):
    try:
        klass = globals()["Address" + atype]
    except KeyError:
        raise IndexSchemaError("No matching class for addressType {}".format(atype))
    return klass(0).toStr(u"en", num)


def tokenizer(s, as_str=False, tref=None, vtitle=None):
    s = re.sub(ur'־', u' ', s)
    s = re.sub(ur'\([^)]+\)', u'', s)
    s = re.sub(ur'\[[^\]]+\]', u'', s)
    s = re.sub(ur'[^ א-ת]', u'', s)
    # remove are parenthetical text
    if as_str:
        return [(s.split(), tref, vtitle)]
    return s.split()


def walk_thru_contents(item, all_words=None, doc2vec=False, tref=u'', vtitle=None, schema=None, addressTypes=None):
    if all_words is None:
        all_words = []
    if addressTypes is None and schema is not None:
        addressTypes = schema[u"addressTypes"] if u"addressTypes" in schema else None
    assert(isinstance(all_words, list))
    if type(item) is dict:
        for n in schema[u"nodes"]:
            node_title = u"" if n.get(u"default", False) or not n.get(u"titles", None) else filter(lambda x: x.get(u"primary", False) and x.get(u"lang", u"") == u"en", n[u"titles"])[0][u"text"]
            walk_thru_contents(item[n[u"key"]], all_words, doc2vec, tref + u", {}".format(node_title), vtitle, n, addressTypes)
    elif type(item) is list:
        for ii, i in enumerate(item):
            try:
                walk_thru_contents(i, all_words, doc2vec, tref + u"{}{}".format(u" " if schema else u":", str2addressType(addressTypes[0], ii+1)), vtitle, addressTypes=addressTypes[1:])
            except IndexError:
                print u"index error for addressTypes {} ref {}".format(addressTypes, tref, vtitle)
    elif isinstance(item, basestring):
        all_words += tokenizer(item, doc2vec, tref, vtitle)

    return all_words


def export_library_as_file(filename):
    vs = VersionSet({"language": "he"})
    all_words = []
    count = vs.count()
    for i, v in enumerate(vs):
        print "{}/{}".format(i+1, count)
        try:
            version_words = walk_thru_contents(v.chapter, tref=v.title, vtitle=v.versionTitle, schema=v.get_index().schema)
            all_words += version_words
        except BookNameError:
            print u"No such book for version {}".format(v)

    with codecs.open(filename, 'wb', encoding='utf8') as fout:
        fout.write(u" ".join(all_words))


def pad_hex(i, n):
    h = hex(i)
    l = len(h)
    if l < n:
        h = "0x" + ("0"*(n-l)) + h[2:]
    return h


def ascii_encode(s):
    return "".join(map(lambda x: pad_hex(ord(x), 5), s))


def unicode_encode(s):
    u"".join([unichr(int(s[i:i + 5], 16)) for i, x in enumerate(s) if i % 5 == 0])


def export_library_as_docs(filename):
    vs = VersionSet({"language": "he"})
    all_docs = []
    count = vs.count()
    for i, v in enumerate(vs):
        if i % 100 == 0:
            print "{}/{}".format(i+1, count)
        try:
            version_words = walk_thru_contents(v.chapter, doc2vec=True, tref=v.title, vtitle=v.versionTitle, schema=v.get_index().schema)
        except BookNameError:
            print u"Skipping {}, {}".format(v.title, v.versionTitle)
            continue
        except Exception as e:
            print e, v.title, v.versionTitle
            continue
        all_docs += version_words

    doc_id_map = {}
    with codecs.open(filename, 'wb', encoding='utf8') as fout:
        for idoc, doc in enumerate(all_docs):
            if idoc % 10000 == 0:
                print "writing {}/{}".format(idoc+1, len(all_docs))

            doc_id = "_*{}".format(idoc)
            doc_id_map[doc_id] = {
                u"title": doc[1],
                u"versionTitle": doc[2]
            }

            input_doc = " ".join(map(lambda x: ascii_encode(x), doc[0]))
            fout.write("{} {}\n".format(doc_id, input_doc))
    with codecs.open("doc_ids.json", "wb", encoding="utf8") as fout_ids:
        json.dump(doc_id_map, fout_ids, ensure_ascii=False)

