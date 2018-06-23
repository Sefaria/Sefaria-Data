# -*- coding: utf-8 -*-
from sefaria.model import *
import bleach
import re

one = u"""ומנין שהתפילין עוז הם לישראל דכתי' (דברים כח, י) וראו כל עמי הארץ כי שם ה' נקרא עליך ויראו ממך ותניא ר' אליעזר הגדול אומר אלו תפילין שבראש"""
two = u"""המניח תפילין בחלום יצפה לגדולה שנאמר (דברים כח, י) וראו כל עמי הארץ כי שם י"י נקרא עליך וגו' ותניא רבי אליעזר הגדול אומר אלו תפילין שבראש המתפלל בחלום סימן יפה לו וה"מ דלא סיים"""

stop_words = [u"ר'",u'רב',u'רבי',u'בן',u'בר',u'בריה',u'אמר',u'כאמר',u'וכאמר',u'דאמר',u'ודאמר',u'כדאמר',u'וכדאמר',u'ואמר',u'כרב',
              u'ורב',u'כדרב',u'דרב',u'ודרב',u'וכדרב',u'כרבי',u'ורבי',u'כדרבי',u'דרבי',u'ודרבי',u'וכדרבי',u"כר'",u"ור'",u"כדר'",
              u"דר'",u"ודר'",u"וכדר'",u'א״ר',u'וא״ר',u'כא״ר',u'דא״ר',u'דאמרי',u'משמיה',u'קאמר',u'קאמרי',u'לרב',u'לרבי',
              u"לר'",u'ברב',u'ברבי',u"בר'",u'הא',u'בהא',u'הך',u'בהך',u'ליה',u'צריכי',u'צריכא',u'וצריכי',u'וצריכא',u'הלל',u'שמאי']
stop_phrases = [u'למה הדבר דומה',u'כלל ופרט וכלל',u'אלא כעין הפרט',u'מה הפרט',u'כלל ופרט',u'אין בכלל',u'אלא מה שבפרט']


def tokenize_words(base_str):
    base_str = base_str.strip()
    base_str = bleach.clean(base_str, tags=[], strip=True)
    for match in re.finditer(ur'\(.*?\)', base_str):
        if library.get_titles_in_string(match.group()) and len(match.group().split()) <= 5:
            base_str = base_str.replace(match.group(), u"")
            # base_str = re.sub(ur"(?:\(.*?\)|<.*?>)", u"", base_str)
    base_str = re.sub(ur'־',u' ',base_str)
    base_str = re.sub(ur'[A-Za-z]',u'',base_str)
    for phrase in stop_phrases:
        base_str = base_str.replace(phrase,u'')
    word_list = re.split(ur"\s+", base_str)
    word_list = [w for w in word_list if len(w.strip()) > 0 and w not in stop_words]
    return word_list

one_words = tokenize_words(one)
two_words = tokenize_words(two)
pass