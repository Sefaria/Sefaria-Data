import urllib2
import re
import json

#def is_there_bavli():
# Get list of mesechtot
mesechtot = [u'Mishnah Berakhot',
                u'Mishnah Peah',
                u'Mishnah Demai',
                u'Mishnah Kilayim',
                u'Mishnah Sheviit',
                u'Mishnah Terumot',
                u'Mishnah Maasrot',
                u'Mishnah Maaser Sheni',
                u'Mishnah Challah',
                u'Mishnah Orlah',
                u'Mishnah Bikkurim',
                u'Mishnah Shabbat',
                u'Mishnah Eruvin',
                u'Mishnah Pesachim',
                u'Mishnah Shekalim',
                u'Mishnah Yoma',
                u'Mishnah Sukkah',
                u'Mishnah Beitzah',
                u'Mishnah Rosh Hashanah',
                u'Mishnah Taanit',
                u'Mishnah Megillah',
                u'Mishnah Moed Katan',
                u'Mishnah Chagigah',
                u'Mishnah Yevamot',
                u'Mishnah Ketubot',
                u'Mishnah Nedarim',
                u'Mishnah Nazir',
                u'Mishnah Sotah',
                u'Mishnah Gittin',
                u'Mishnah Kiddushin',
                u'Mishnah Bava Kamma',
                u'Mishnah Bava Metzia',
                u'Mishnah Bava Batra',
                u'Mishnah Sanhedrin',
                u'Mishnah Makkot',
                u'Mishnah Shevuot',
                u'Mishnah Eduyot',
                u'Mishnah Avodah Zarah',
                u'Pirkei Avot',
                u'Mishnah Horayot',
                u'Mishnah Zevachim',
                u'Mishnah Menachot',
                u'Mishnah Chullin',
                u'Mishnah Bekhorot',
                u'Mishnah Arakhin',
                u'Mishnah Temurah',
                u'Mishnah Keritot',
                u'Mishnah Meilah',
                u'Mishnah Tamid',
                u'Mishnah Middot',
                u'Mishnah Kinnim',
                u'Mishnah Kelim',
                u'Mishnah Oholot',
                u'Mishnah Negaim',
                u'Mishnah Parah',
                u'Mishnah Tahorot',
                u'Mishnah Mikvaot',
                u'Mishnah Niddah',
                u'Mishnah Makhshirin',
                u'Mishnah Zavim',
                u'Mishnah Tevul Yom',
                u'Mishnah Yadayim',
                u'Mishnah Oktzin'
]
# For each Mesechet of Mishnah check wether there is a talmud


def get_index(title):
    url = 'http://www.sefaria.org/api/index/'+ str(title)
    response = urllib2.urlopen(url)
    resp = response.read()
    return json.loads(resp)


def get_text(ref):
    url = 'http://www.sefaria.org/api/texts/' + ref
    response = urllib2.urlopen(url)
    resp = response.read()
    return json.loads(resp)


def get_mishnah_index(mesechet):
    mesechet=re.sub(" ", "_", mesechet)
    return get_index(mesechet)


def get_talmud_index(mesechet):
    ref = mesechet[8:]
    ref = re.sub(" ", "_", ref)
    return get_index(ref)


def find(title, talmud_length, mishna_length):
    current_mishnah_chapter = 1
    current_mishnah = 1
    cuurent_mishnah_offset = 0

    mishnah_text = {}

    for daf_index in range(2, talmud_length):
        amud = "a" if daf_index % 2 == 0 else "b"
        daf = (daf_index / 2) + 1
        bavli = get_text(title + "." + str(daf) + amud)["he"]

        # for mishnah_in_chapter in range(0, len(perek_text)):
        for line in range(len(bavli)):
            perek_text = mishnah_text.get(current_mishnah_chapter)
            if not perek_text:
                perek_text = get_text("Mishna_" + title + '.' + str(current_mishnah_chapter))["he"]
                perek_text = map(lambda t: re.sub(r'[,\.]', "", t), perek_text)
                mishnah_text[current_mishnah_chapter] = perek_text

            if u"\u05de\u05ea\u05e0\u05d9' " in bavli[line]:  # Match mishnah keyword
                if bavli[line + 1] in perek_text[current_mishnah]:  # Check for correct text
                    bavlis_mishnah = []
                    starting_line = line
                    ending_line = a = line + 1
                    while u"גמ׳" not in bavli[a]:
                        bavlis_mishnah += [bavli[a]]
                        ending_line = a
                        a += 1
                    line = a  # reset line counter to line w/ GM

                    last_mishnah_line_in_bavli = bavlis_mishnah[-1]
                    
                    print "Matched Mishnah: {} {}{} {}-{}".format(title, daf, amud, starting_line, ending_line)
            if u'\u05d4\u05d3\u05e8\u05df \u05e2\u05dc\u05da' in bavli[line]:
                print "End of perek: {} {} on {}{} {}".format(title, current_mishnah_chapter, daf, amud, line)
                current_mishnah_chapter += 1
                current_mishnah = 1
                cuurent_mishnah_offset = 0

        #todo: Mishnah carries over to next daf

for mesechet in mesechtot:
    try:
        bavli = get_talmud_index(mesechet)
        mishnah = get_mishnah_index(mesechet)
        find(bavli["title"],bavli["length"],mishnah["length"])
        #need to take the length from the index of the mishna and the talmud
    except:
        print 'no bavli for '+ mesechet
    break


import urllib2
import re
import json
title="Niddah"
length=143
mishna_length=10