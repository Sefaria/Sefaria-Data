# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import urllib
import re

female_numbers = u"אחת|שתיים|שלוש|ארבע|חמש|שש|שבע|שמונה|תשע|עשר|אחת עשרה|שתים עשרה|שלוש עשרה|ארבע עשרה|חמש עשרה|שש עשרה|שבע עשרה|שמונה עשרה|תשע עשרה|עשרים"
male_numbers = u"אחד|שניים|שלושה|ארבעה|חמישה|שישה|שבעה|שמונה|תשעה|עשרה|אחד עשר|שנים עשר|שלושה עשר|ארבעה עשר|חמישה עשר|שישה עשר|שבעה עשר|שמונה עשר|תשעה עשר"
mixed_numbers = u"אחת עשר|שתים עשר|שלוש עשר|ארבע עשר|חמש עשר|שש עשר|שבע עשר|שמונה עשר|תשע עשר"
he_numbers = male_numbers + u"|" + female_numbers + u"|" + mixed_numbers
num_map = {
    u"אחת": 1,
    u"שתיים": 2,
    u"שלוש": 3,
    u"ארבע": 4,
    u"חמש": 5,
    u"שש": 6,
    u"שבע": 7,
    u"שמונה": 8,
    u"תשע": 9,
    u"עשר": 10,
    u"אחת עשרה": 11,
    u"שתים עשרה": 12,
    u"שלוש עשרה": 13,
    u"ארבע עשרה": 14,
    u"חמש עשרה": 15,
    u"שש עשרה": 16,
    u"שבע עשרה": 17,
    u"שמונה עשרה": 18,
    u"תשע עשרה": 19,
    u"עשרים": 20,
    u"אחד": 1,
    u"שניים": 2,
    u"שלושה": 3,
    u"ארבעה": 4,
    u"חמישה": 5,
    u"שישה": 6,
    u"שבעה": 7,
    u"תשעה": 9,
    u"עשרה": 10,
    u"אחד עשר": 11,
    u"שנים עשר": 12,
    u"שלושה עשר": 13,
    u"ארבעה עשר": 14,
    u"חמישה עשר": 15,
    u"שישה עשר": 16,
    u"שבעה עשר": 17,
    u"שמונה עשר": 18,
    u"תשעה עשר": 19,
    u"אחת עשר": 11,
    u"שתים עשר": 12,
    u"שלוש עשר": 13,
    u"ארבע עשר": 14,
    u"חמש עשר": 15,
    u"שש עשר": 16,
    u"שבע עשר": 17,
    u"תשע עשר": 19,
}


sdarim_source = u'''
<tbody>
<tr valign="top">
<td style="background-color: #F2F3F4; text-align: right; font-weight: bold; padding-left: 5px;"><a href="/wiki/%D7%A1%D7%93%D7%A8_%D7%96%D7%A8%D7%A2%D7%99%D7%9D" title="סדר זרעים">סדר זרעים</a></td>
<td style="background-color: #F2F3F4; text-align: right; font-weight: bold; padding-left: 5px;"><a href="/wiki/%D7%A1%D7%93%D7%A8_%D7%9E%D7%95%D7%A2%D7%93" title="סדר מועד">סדר מועד</a></td>
<td style="background-color: #F2F3F4; text-align: right; font-weight: bold; padding-left: 5px;"><a href="/wiki/%D7%A1%D7%93%D7%A8_%D7%A0%D7%A9%D7%99%D7%9D" title="סדר נשים">סדר נשים</a></td>
<td style="background-color: #F2F3F4; text-align: right; font-weight: bold; padding-left: 5px;"><a href="/wiki/%D7%A1%D7%93%D7%A8_%D7%A0%D7%96%D7%99%D7%A7%D7%99%D7%9F" title="סדר נזיקין">סדר נזיקין</a></td>
<td style="background-color: #F2F3F4; text-align: right; font-weight: bold; padding-left: 5px;"><a href="/wiki/%D7%A1%D7%93%D7%A8_%D7%A7%D7%93%D7%A9%D7%99%D7%9D" title="סדר קדשים">סדר קדשים</a></td>
<td style="background-color: #F2F3F4; text-align: right; font-weight: bold; padding-left: 5px;"><a href="/wiki/%D7%A1%D7%93%D7%A8_%D7%98%D7%94%D7%A8%D7%95%D7%AA" title="סדר טהרות">סדר טהרות</a></td>
</tr>
</tbody>'''

#scraped from http://he.wikipedia.org/wiki/מסכת
mesechet_source = u'''
<tbody>
<tr valign="top">
<td style="padding-right: 5px; text-align: right;"><a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%91%D7%A8%D7%9B%D7%95%D7%AA" title="מסכת ברכות">ברכות</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%A4%D7%90%D7%94" title="מסכת פאה">פאה</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%93%D7%9E%D7%90%D7%99" title="מסכת דמאי">דמאי</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%9B%D7%9C%D7%90%D7%99%D7%99%D7%9D" title="מסכת כלאיים">כלאיים</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%A9%D7%91%D7%99%D7%A2%D7%99%D7%AA" title="מסכת שביעית">שביעית</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%AA%D7%A8%D7%95%D7%9E%D7%95%D7%AA" title="מסכת תרומות">תרומות</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%9E%D7%A2%D7%A9%D7%A8%D7%95%D7%AA" title="מסכת מעשרות">מעשרות</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%9E%D7%A2%D7%A9%D7%A8_%D7%A9%D7%A0%D7%99" title="מסכת מעשר שני">מעשר שני</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%97%D7%9C%D7%94" title="מסכת חלה">חלה</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%A2%D7%A8%D7%9C%D7%94" title="מסכת ערלה">ערלה</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%91%D7%99%D7%9B%D7%95%D7%A8%D7%99%D7%9D" title="מסכת ביכורים">ביכורים</a></td>
</tr>
<tr valign="top">
<td style="padding-right: 5px; text-align: right;"><a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%A9%D7%91%D7%AA" title="מסכת שבת">שבת</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%A2%D7%99%D7%A8%D7%95%D7%91%D7%99%D7%9F" title="מסכת עירובין">עירובין</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%A4%D7%A1%D7%97%D7%99%D7%9D" title="מסכת פסחים">פסחים</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%A9%D7%A7%D7%9C%D7%99%D7%9D" title="מסכת שקלים">שקלים</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%99%D7%95%D7%9E%D7%90" title="מסכת יומא">יומא</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%A1%D7%95%D7%9B%D7%94" title="מסכת סוכה">סוכה</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%91%D7%99%D7%A6%D7%94" title="מסכת ביצה">ביצה</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%A8%D7%90%D7%A9_%D7%94%D7%A9%D7%A0%D7%94" title="מסכת ראש השנה">ראש השנה</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%AA%D7%A2%D7%A0%D7%99%D7%AA" title="מסכת תענית">תענית</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%9E%D7%92%D7%99%D7%9C%D7%94" title="מסכת מגילה">מגילה</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%9E%D7%95%D7%A2%D7%93_%D7%A7%D7%98%D7%9F" title="מסכת מועד קטן">מועד קטן</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%97%D7%92%D7%99%D7%92%D7%94" title="מסכת חגיגה">חגיגה</a></td>
</tr>
<tr valign="top">
<td style="padding-right: 5px; text-align: right;"><a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%99%D7%91%D7%9E%D7%95%D7%AA" title="מסכת יבמות">יבמות</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%9B%D7%AA%D7%95%D7%91%D7%95%D7%AA" title="מסכת כתובות">כתובות</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%A0%D7%93%D7%A8%D7%99%D7%9D" title="מסכת נדרים">נדרים</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%A0%D7%96%D7%99%D7%A8" title="מסכת נזיר">נזיר</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%A1%D7%95%D7%98%D7%94" title="מסכת סוטה">סוטה</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%92%D7%99%D7%98%D7%99%D7%9F" title="מסכת גיטין">גיטין</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%A7%D7%99%D7%93%D7%95%D7%A9%D7%99%D7%9F" title="מסכת קידושין">קידושין</a></td>
</tr>
<tr valign="top">
<td style="padding-right: 5px; text-align: right;"><a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%91%D7%91%D7%90_%D7%A7%D7%9E%D7%90" title="מסכת בבא קמא" class="mw-redirect">בבא קמא</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%91%D7%91%D7%90_%D7%9E%D7%A6%D7%99%D7%A2%D7%90" title="מסכת בבא מציעא" class="mw-redirect">בבא מציעא</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%91%D7%91%D7%90_%D7%91%D7%AA%D7%A8%D7%90" title="מסכת בבא בתרא" class="mw-redirect">בבא בתרא</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%A1%D7%A0%D7%94%D7%93%D7%A8%D7%99%D7%9F" title="מסכת סנהדרין">סנהדרין</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%9E%D7%9B%D7%95%D7%AA" title="מסכת מכות">מכות</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%A9%D7%91%D7%95%D7%A2%D7%95%D7%AA" title="מסכת שבועות">שבועות</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%A2%D7%93%D7%99%D7%95%D7%AA" title="מסכת עדיות">עדיות</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%A2%D7%91%D7%95%D7%93%D7%94_%D7%96%D7%A8%D7%94" title="מסכת עבודה זרה">עבודה זרה</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%90%D7%91%D7%95%D7%AA" title="מסכת אבות">אבות</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%94%D7%95%D7%A8%D7%99%D7%95%D7%AA" title="מסכת הוריות">הוריות</a></td>
</tr>
<tr valign="top">
<td style="padding-right: 5px; text-align: right;"><a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%96%D7%91%D7%97%D7%99%D7%9D" title="מסכת זבחים">זבחים</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%9E%D7%A0%D7%97%D7%95%D7%AA" title="מסכת מנחות">מנחות</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%97%D7%95%D7%9C%D7%99%D7%9F" title="מסכת חולין">חולין</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%91%D7%9B%D7%95%D7%A8%D7%95%D7%AA" title="מסכת בכורות">בכורות</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%A2%D7%A8%D7%9B%D7%99%D7%9F" title="מסכת ערכין">ערכין</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%AA%D7%9E%D7%95%D7%A8%D7%94" title="מסכת תמורה">תמורה</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%9B%D7%A8%D7%99%D7%AA%D7%95%D7%AA" title="מסכת כריתות">כריתות</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%9E%D7%A2%D7%99%D7%9C%D7%94" title="מסכת מעילה">מעילה</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%AA%D7%9E%D7%99%D7%93" title="מסכת תמיד">תמיד</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%9E%D7%99%D7%93%D7%95%D7%AA" title="מסכת מידות">מידות</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%A7%D7%99%D7%A0%D7%99%D7%9D" title="מסכת קינים">קינים</a></td>
</tr>
<tr valign="top">
<td style="padding-right: 5px; text-align: right;"><a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%9B%D7%9C%D7%99%D7%9D" title="מסכת כלים">כלים</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%90%D7%94%D7%9C%D7%95%D7%AA" title="מסכת אהלות">אהלות</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%A0%D7%92%D7%A2%D7%99%D7%9D" title="מסכת נגעים">נגעים</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%A4%D7%A8%D7%94" title="מסכת פרה">פרה</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%98%D7%94%D7%A8%D7%95%D7%AA" title="מסכת טהרות">טהרות</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%9E%D7%A7%D7%95%D7%90%D7%95%D7%AA" title="מסכת מקואות">מקואות</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%A0%D7%99%D7%93%D7%94" title="מסכת נידה">נידה</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%9E%D7%9B%D7%A9%D7%99%D7%A8%D7%99%D7%9F" title="מסכת מכשירין">מכשירין</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%96%D7%91%D7%99%D7%9D" title="מסכת זבים">זבים</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%98%D7%91%D7%95%D7%9C_%D7%99%D7%95%D7%9D" title="מסכת טבול יום">טבול יום</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%99%D7%93%D7%99%D7%99%D7%9D" title="מסכת ידיים">ידיים</a> • <a href="/wiki/%D7%9E%D7%A1%D7%9B%D7%AA_%D7%A2%D7%95%D7%A7%D7%A6%D7%99%D7%9D" title="מסכת עוקצים">עוקצים</a></td>
</tr>
</tbody>
'''

base_url = u'http://he.wikipedia.org'
entry_re = ur'(?P<perek>.*)\((?P<count>' + he_numbers + ur')\sמשניות'
ere = re.compile(entry_re)

success = fail = 0
soup = BeautifulSoup(mesechet_source)
for link in soup.find_all('a'):
    link_text = link.get('href')
    print urllib.unquote(link_text).decode('utf8')

    #original fetch code
    #full_link = base_url + link_text
    #page = urllib.urlopen(full_link)
    #with open(link_text[1:], 'w') as f:
    #    f.write(page.read())

    with open(link_text[1:], 'r') as f:
        book_soup = BeautifulSoup(f.read())

    variants = [u'.D7.A4.D7.A8.D7.A7.D7.99_.D7.94.D7.9E.D7.A1.D7.9B.D7.AA',
        u".D7.A9.D7.9E.D7.95.D7.AA_.D7.A4.D7.A8.D7.A7.D7.99_.D7.94.D7.9E.D7.A1.D7.9B.D7.AA",
        u".D7.A9.D7.9E.D7.95.D7.AA_.D7.A4.D7.A8.D7.A7.D7.99_.D7.94.D7.9E.D7.A1.D7.9B.D7.AA_.D7.95.D7.AA.D7.95.D7.9B.D7.9F_.D7.9E.D7.A9.D7.A0.D7.99.D7.95.D7.AA.D7.99.D7.94.D7.9D",
        u".D7.A4.D7.A8.D7.A7.D7.99_.D7.94.D7.9E.D7.A1.D7.9B.D7.AA_.D7.91.D7.9E.D7.A9.D7.A0.D7.94"
         ]
    for v in variants:
        psec = book_soup.find(id=v)
        if psec:
            break
    ol = psec.parent.next_sibling.next_sibling

    for child in ol.find_all('li'):
        for i in range(len(child.contents)):
            entry = unicode(child.contents[i].string)
            m = ere.match(entry)
            if m:
                addition = ";".join([unicode(t.string) for t in child.contents[i+1:]])
                break

        if not m:
            print u"FAILED ON:"
            print child.encode_contents()
            fail += 1
        else:
            success += 1
            print m.group('perek') + u" : {} : ".format(num_map[m.group('count')]) + addition

print
print
print "Successes: {}".format(success)
print "Failures: {}".format(fail)
print "Success Rate: {}%".format(round(success / float(fail + success) * 100,2))