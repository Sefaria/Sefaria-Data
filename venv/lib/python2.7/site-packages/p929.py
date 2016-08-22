"""
 Tools for the 929 - Chapter-a-day Tanach learning project
 http://929.org.il
 One chapter is read each Sunday - Thursday
 Genesis 1 was read on Sunday, December 21, 2014

 p929.Perek(date) takes a datetime.date object, and returns the chapter read on that day
 If invoked with no arguments, returns the chapter that is read today.

 p929.todays_perek() is a convenience method that invokes Perek() with not arguments.
 It returns the Perek object for the chapter that is read today.

 If the date supplied to either of the above functions is Friday or Saturday, they returns Thursday's chapter.
 Both functions return string in "Bookname Chapternumber" format.

 p929.books is an array of tuples (book, chapters) of the books of Tanach and the number of chapters that they have, in order.
 p929.intervals is a list of triples (start, end, book) defining non-overlapping ranges over the set of chapters from 1 to 929.
"""

import datetime
import math


# Genesis 1 was read on Sunday, December 21, 2014
# We set the origin date one day before
origin = datetime.date(2014, 12, 20)

"""
"books" is taken from the indexes of http://sefaria.org, with:
>>> from model import *
>>> category = "Tanach"
>>> q = {"$and": [{"categories": category}, {"categories": {"$ne": "Commentary"}}, {"categories": {"$ne": "Commentary2"}}, {"categories": {"$ne": "Targum"}}]}
>>> [(i.title, i.nodes.lengths[0]) for i in IndexSet(q)]
"""
books = [
    (u'Genesis', 50), (u'Exodus', 40), (u'Leviticus', 27), (u'Numbers', 36), (u'Deuteronomy', 34), (u'Joshua', 24), (u'Judges', 21), (u'I Samuel', 31), (u'II Samuel', 24), (u'I Kings', 22), (u'II Kings', 25), (u'Isaiah', 66), (u'Jeremiah', 52), (u'Ezekiel', 48), (u'Hosea', 14), (u'Joel', 4), (u'Amos', 9), (u'Obadiah', 1), (u'Jonah', 4), (u'Micah', 7), (u'Nahum', 3), (u'Habakkuk', 3), (u'Zephaniah', 3), (u'Haggai', 2), (u'Zechariah', 14), (u'Malachi', 3), (u'Psalms', 150), (u'Proverbs', 31), (u'Job', 42), (u'Song of Songs', 8), (u'Ruth', 4), (u'Lamentations', 5), (u'Ecclesiastes', 12), (u'Esther', 10), (u'Daniel', 12), (u'Ezra', 10), (u'Nehemiah', 13), (u'I Chronicles', 29), (u'II Chronicles', 36)
]

def __construct_intervals():
    _intervals = []
    count = 0
    for name, length in books:
        newcount = count + length
        _intervals.append((count, newcount, name))
        count = newcount
    return _intervals
intervals = __construct_intervals()


class Perek(object):
    """
    Takes a datetime.date object, and returns the chapter read on that day.
    If date is not supplied, returns the chapter for today.

    If the date input is Friday or Saturday, they returns Thursday's chapter.

    Returns Perek object

    >>> str(p929.Perek(date = datetime.date(2017,5,5)))
    'Psalms 53'
    """

    def __init__(self, date=datetime.date.today()):
        self.date = date
        delta = self.date - origin

        weeks = math.floor(delta.days / 7.0)
        days = delta.days % 7
        days = 5 if days > 5 else days

        self.number = int((weeks * 5) + days)

        #future proof?
        #self.number = self.number % 929

        for interval in intervals:
            if interval[0] < self.number <= interval[1]:
                self.book_name = interval[2]
                self.book_chapter = int(self.number - interval[0])

        self.hashtag = "#p929 #ch{}".format(self.number)
        self.url_929 = "http://www.929.org.il/page/{}".format(self.number)
        self._sefaria_url_ref = "{}.{}".format(self.book_name.replace(" ","_"), self.book_chapter)
        self.url_sefaria = "http://www.sefaria.org/{}".format(self._sefaria_url_ref)
        self.as_a_phrase = "Perek for {} is #{}: {} {}".format(self.date.strftime("%A %d %B %Y"), self.number, self.book_name, self.book_chapter)

    def __str__(self):
        return self.as_a_phrase

    def __repr__(self):
        return "{}(datetime.date({},{},{}))".format(self.__class__.__name__, self.date.year, self.date.month, self.date.day)


def todays_perek():
    """
    Returns the chapter that is read today.
    If today is Friday or Saturday, this returns Thursday's chapter.

    Returns Perek object
    """
    return Perek()

