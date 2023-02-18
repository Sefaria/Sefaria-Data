import django

django.setup()

django.setup()
superuser_id = 171118
# import statistics
import csv
from sefaria.model import *
from sefaria.helper.schema import insert_last_child, reorder_children
from sefaria.helper.schema import remove_branch
from sefaria.tracker import modify_bulk_text
from sefaria.helper.category import create_category
from sources.functions import post_index
from sefaria.system.database import db
import time
# from docx import Document
introductory = [
'Transmission of the Oral Law',
'Positive Mitzvot',
'Negative Mitzvot',
'Overview of Mishneh Torah Contents'
]
books = [
# 'Transmission of the Oral Law',
# 'Positive Mitzvot',
# 'Negative Mitzvot',
# 'Overview of Mishneh Torah Contents',
'Foundations of the Torah',
'Human Dispositions',
'Torah Study',
'Foreign Worship and Customs of the Nations',
'Repentance',
'Reading the Shema',
'Prayer and the Priestly Blessing',
'Tefillin, Mezuzah and the Torah Scroll',
'Fringes',
'Blessings',
'Circumcision',
'The Order of Prayer',
'Sabbath',
'Eruvin',
'Rest on the Tenth of Tishrei',
'Rest on a Holiday',
'Leavened and Unleavened Bread',
'Shofar, Sukkah and Lulav',
'Sheqel Dues',
'Sanctification of the New Month',
'Fasts',
'Scroll of Esther and Hanukkah',
'Marriage',
'Divorce',
'Levirate Marriage and Release',
'Virgin Maiden',
'Woman Suspected of Infidelity',
'Forbidden Intercourse',
'Forbidden Foods',
'Ritual Slaughter',
'Oaths',
'Vows',
'Nazariteship',
'Appraisals and Devoted Property',
'Diverse Species',
'Gifts to the Poor',
'Heave Offerings',
'Tithes',
"Second Tithes and Fourth Year's Fruit",
'First Fruits and other Gifts to Priests Outside the Sanctuary',
'Sabbatical Year and the Jubilee',
'The Chosen Temple',
'Vessels of the Sanctuary and Those who Serve Therein',
'Admission into the Sanctuary',
'Things Forbidden on the Altar',
'Sacrificial Procedure',
'Daily Offerings and Additional Offerings',
'Sacrifices Rendered Unfit',
'Service on the Day of Atonement',
'Trespass',
'Paschal Offering',
'Festival Offering',
'Firstlings',
'Offerings for Unintentional Transgressions',
'Offerings for Those with Incomplete Atonement',
'Substitution',
'Defilement by a Corpse',
'Red Heifer',
'Defilement by Leprosy',
'Those Who Defile Bed or Seat',
'Other Sources of Defilement',
'Defilement of Foods',
'Vessels',
'Immersion Pools',
'Damages to Property',
'Theft',
'Robbery and Lost Property',
'One Who Injures a Person or Property',
'Murderer and the Preservation of Life',
'Sales',
'Ownerless Property and Gifts',
'Neighbors',
'Agents and Partners',
'Slaves',
'Hiring',
'Borrowing and Deposit',
'Creditor and Debtor',
'Plaintiff and Defendant',
'Inheritances',
'The Sanhedrin and the Penalties within their Jurisdiction',
'Testimony',
'Rebels',
'Mourning',
'Kings and Wars'
]

if __name__ == '__main__':
    print("hello world")

    for book in books:
        ref_iterator = Ref("Mishneh Torah, " + book + " 1:1")
        while ref_iterator:
            # print(ref_iterator.text().text)
            # if '&lt' in ref_iterator.text().text or '&gt' in ref_iterator.text().text:
            if '&' in ref_iterator.text().text:
                print(ref_iterator)
            ref_iterator = ref_iterator.next_segment_ref()
    for book in introductory:
        print(book)
        ref_iterator = Ref("Mishneh Torah, " + book + " 1")
        while ref_iterator:
            print(ref_iterator.text().text)
            # if '&lt' in ref_iterator.text().text or '&gt' in ref_iterator.text().text:
            if '&' in ref_iterator.text().text:
                print(ref_iterator)
            ref_iterator = ref_iterator.next_segment_ref()








