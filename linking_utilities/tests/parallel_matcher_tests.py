# -*- coding: utf-8 -*-
from sefaria.model import *
import bleach
import re

one = """ומנין שהתפילין עוז הם לישראל דכתי' (דברים כח, י) וראו כל עמי הארץ כי שם ה' נקרא עליך ויראו ממך ותניא ר' אליעזר הגדול אומר אלו תפילין שבראש"""
two = """המניח תפילין בחלום יצפה לגדולה שנאמר (דברים כח, י) וראו כל עמי הארץ כי שם י"י נקרא עליך וגו' ותניא רבי אליעזר הגדול אומר אלו תפילין שבראש המתפלל בחלום סימן יפה לו וה"מ דלא סיים"""

stop_words = ["ר'",'רב','רבי','בן','בר','בריה','אמר','כאמר','וכאמר','דאמר','ודאמר','כדאמר','וכדאמר','ואמר','כרב',
              'ורב','כדרב','דרב','ודרב','וכדרב','כרבי','ורבי','כדרבי','דרבי','ודרבי','וכדרבי',"כר'","ור'","כדר'",
              "דר'","ודר'","וכדר'",'א״ר','וא״ר','כא״ר','דא״ר','דאמרי','משמיה','קאמר','קאמרי','לרב','לרבי',
              "לר'",'ברב','ברבי',"בר'",'הא','בהא','הך','בהך','ליה','צריכי','צריכא','וצריכי','וצריכא','הלל','שמאי']
stop_phrases = ['למה הדבר דומה','כלל ופרט וכלל','אלא כעין הפרט','מה הפרט','כלל ופרט','אין בכלל','אלא מה שבפרט']


def tokenize_words(base_str):
    base_str = base_str.strip()
    base_str = bleach.clean(base_str, tags=[], strip=True)
    for match in re.finditer(r'\(.*?\)', base_str):
        if library.get_titles_in_string(match.group()) and len(match.group().split()) <= 5:
            base_str = base_str.replace(match.group(), "")
            # base_str = re.sub(ur"(?:\(.*?\)|<.*?>)", u"", base_str)
    base_str = re.sub(r'־',' ',base_str)
    base_str = re.sub(r'[A-Za-z]','',base_str)
    for phrase in stop_phrases:
        base_str = base_str.replace(phrase,'')
    word_list = re.split(r"\s+", base_str)
    word_list = [w for w in word_list if len(w.strip()) > 0 and w not in stop_words]
    return word_list

one_words = tokenize_words(one)
two_words = tokenize_words(two)
pass