


'''
look for lines with perek, pasuk, and a - and tilde
'''

line = line.decode('utf-8')
text = {}
curr_perek = 0
curr_passuk = 0
if line.find("~")>=0 and line.find("-")>=0 and line.find(u"פרק")>=0:
    perek = re.findall(u'פרק [\u05D0-\u05EA]+', line)[0]
    passuk = re.findall(u'פסוק [\u05D0-\u05EA]+', line)[0]
    perek = perek.replace(u"פרק ", u"")
    poss_perek = getGematria(perek)
    if poss_perek < curr_perek:
        print 'perek prob'
        pdb.set_trace()
    passuk = passuk.replace(u"פסוק ", u"")
    poss_passuk = getGematria(passuk)
    if poss_passuk <= curr_passuk:
        print 'passuk prob'
        pdb.set_trace()
    if poss_perek > curr_perek:
        curr_perek = poss_perek
        text[curr_perek] = {}
    curr_passuk = poss_passuk
    text[curr_perek][curr_passuk] = ""
else:
    first_word = line.split(" ")[0]
    if first_word.find("[")>=0 and first_word.find("]")>=0:
        first_word = first_word.replace("[","").replace("]","")
        line = ' '.join(line.split(" ")[1:])
        text[curr_perek][curr_passuk] = line
    else:
        text[curr_perek][curr_passuk] += "<br>"+line