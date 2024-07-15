from datetime import datetime, timedelta
import django
django.setup()
from sefaria.model import *
from sefaria.utils.calendars import get_all_calendar_items, parashat_hashavua_and_haftara

def get_all_days_of_year(year):
    # Start with January 1 of the given year
    start_date = datetime(year, 1, 1)
    # Check if it's a leap year
    is_leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
    # End with December 31 of the given year
    end_date = datetime(year, 12, 31)

    # Number of days in the year
    days_in_year = (end_date - start_date).days + 1

    # Generate a list of all the dates in the year
    date_list = [start_date + timedelta(days=i) for i in range(days_in_year)]

    return date_list

import difflib
correct_spellings = """Bereshit
Noach
Lekh Lekha
Vayera
Chayyei Sarah
Toldot
Vayeitzei
Vayishlach
Vayeshev
Mikketz 
Vayiggash
Vayechi
Shemot
Vaera
Bo
Beshalach
Yitro
Mishpatim
Terumah
Tetzaveh
Ki Tissa
Vayakhel
Vayakhel-Pekudei
Pekudei
Vayikra
Tzav
Shemini
Tazria
Tazria-Metzora
Metzora
Acharei Mot
Acharei Mot-Kedoshim
Kedoshim
Emor
Behar
Behar-Bechukotai
Bechukotai
Bamidbar
Naso
Beha'alotkha
Shelach
Korach
Chukkat
Chukkat-Balak
Balak
Pinchas
Mattot
Mattot-Masei
Masei
Devarim
Vaetchanan
Eikev
Re'eh
Shoftim
Ki Teitzei
Ki Tavo
Nitzavim
Nitzavim-Vayeilekh
Vayeilekh
Ha'azinu
VeZot HaBerakhah 
Parashat Parah
Parashat HaChodesh
Parashat Zakhor 
Parashat Shekalim 
Shabbat Shuvah 
Shabbat Shirah
Shabbat HaGadol
Shabbat Chazon
Shabbat Nachamu
Shabbat Mevarkhim
Sukkot Shabbat Chol HaMoed
Pesach Shabbat Chol haMoed""".splitlines()
def most_similar_string(X, Y):
    best_match = difflib.get_close_matches(X, Y, n=1)
    return best_match[0].strip() if best_match else None

# Example usage
# results_set = set()
# for year in range(2020, 2027):
#     date_list = get_all_days_of_year(year)
#     for date in date_list:
#         results = parashat_hashavua_and_haftara(date, diaspora=True, custom=None)
#         print(results[0]['displayValue'])
#         if 'topic' not in results[0]:
#             results_set.add(results[0]['displayValue']['en'])
# print(results_set)
from sefaria.system.database import db
parshiot_found = [] #
for p in db.parshiot.find():
    x = most_similar_string(p['parasha'], correct_spellings)
    if x:
        if p['parasha'] not in parshiot_found:
            topic = Topic().load({"parasha": p['parasha']})
            if "Parashat " in x or "Shabbat" in x:
                topic.add_title(x, 'en', True, True)
            else:
                topic.add_title("Parashat "+x, 'en', True, True)
            topic.parasha = x
            topic.save()
            parshiot_found.append(p['parasha'])
        p['parasha'] = x
        db.parshiot.save(p)
    else:
        print("Warning: ", p['parasha'])
