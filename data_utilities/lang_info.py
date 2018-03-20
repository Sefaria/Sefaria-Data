
def normalizeLetterFrequency(letter_freq_by_percent):
    # given a dictionary mapping each character to its percentage use in a language,
    # results in a normalized value where the most frequent letter is 0.0 and the least frequent letter is 1.0
    min_freq = min(letter_freq_by_percent.values())
    max_freq = max(letter_freq_by_percent.values())
    normalize = lambda x: abs((1.0 * x - max_freq) / (min_freq - max_freq))
    letter_freq_normalized = {char: normalize(value) for (char, value) in letter_freq_by_percent}
    return letter_freq_normalized


def lettersInOrderOfFrequency(letter_freq_by_percent):
    dict_reversed = {v: k for k, v in letter_freq_by_percent.items()}
    percents = sorted(dict_reversed.keys(), reverse=True)
    letters = []
    for percent in percents:
        letters.append(dict_reversed[percent])
    return letters

languages = {}

languages['en'] = {}
letter_freqs_english = {u"a": 8.167,
                        u"b": 1.492,
                        u"c": 2.782,
                        u"d": 4.253,
                        u"e": 12.702,
                        u"f": 2.228,
                        u"g": 2.015,
                        u"h": 6.094,
                        u"i": 6.966,
                        u"j": 0.153,
                        u"k": 0.772,
                        u"l": 4.025,
                        u"m": 2.406,
                        u"n": 6.749,
                        u"o": 7.507,
                        u"p": 1.929,
                        u"q": 0.095,
                        u"r": 5.987,
                        u"s": 6.327,
                        u"t": 9.056,
                        u"u": 2.758,
                        u"v": 0.978,
                        u"w": 2.360,
                        u"x": 0.150,
                        u"y": 1.974,
                        u"z": 0.074}

languages['en']['letters_in_order_of_frequency'] = lettersInOrderOfFrequency(letter_freqs_english)
languages['en']['letter_freqs'] = normalizeLetterFrequency(letter_freqs_english)
languages['en']['sofit_map'] = {chr(ord(letter) - 32).decode('utf-8'): letter for letter in letter_freqs_english} #dictionary mapping capital letters to lowercase letters
languages['en']['sofit_transx_table'] = {ord(letter) - 33: chr(ord(letter) - 32).decode('utf-8') for letter in letter_freqs_english}
languages['en']['re_chars'] = ur"a-zA-Z"
languages['en']['first_letter'] = ord('a')

languages['he'] = {'letter_freqs': {
                u'י': 0.0,
                u'ו': 0.2145,
                u'א': 0.2176,
                u'מ': 0.3555,
                u'ה': 0.4586,
                u'ל': 0.4704,
                u'ר': 0.4930,
                u'נ': 0.5592,
                u'ב': 0.5678,
                u'ש': 0.7007,
                u'ת': 0.7013,
                u'ד': 0.7690,
                u'כ': 0.8038,
                u'ע': 0.8362,
                u'ח': 0.8779,
                u'ק': 0.9124,
                u'פ': 0.9322,
                u'ס': 0.9805,
                u'ט': 0.9924,
                u'ז': 0.9948,
                u'ג': 0.9988,
                u'צ': 1.0
            },
        'sofit_map': {
            u'ך': u'כ',
            u'ם': u'מ',
            u'ן': u'נ',
            u'ף': u'פ',
            u'ץ': u'צ',
        },
        'letters_in_order_of_frequency': [ u'ו', u'י', u'א', u'מ', u'ה', u'ל', u'ר', u'נ', u'ב', u'ש', u'ת', u'ד', u'כ', u'ע', u'ח', u'ק', u'פ', u'ס', u'ז', u'ט', u'ג', u'צ' ],
        'sofit_transx_table': {
            1498: u'\u05db',
            1501: u'\u05de',
            1503: u'\u05e0',
            1507: u'\u05e4',
            1509: u'\u05e6'
        },
        're_chars': ur"א-ת",  #string to be used in regular expressions to look for characters in this language
        'first_letter': ord(u"א")
        }