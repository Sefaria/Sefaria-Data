import django
django.setup()
from sefaria.model import *
from sefaria.helper.link import rebuild_links_for_title
import time
indices = """Kessef Mishneh on Mishneh Torah, Theft
Kessef Mishneh on Mishneh Torah, Marriage
Kessef Mishneh on Mishneh Torah, Ownerless Property and Gifts
Kessef Mishneh on Mishneh Torah, One Who Injures a Person or Property
Kessef Mishneh on Mishneh Torah, Plaintiff and Defendant
Kessef Mishneh on Mishneh Torah, Sales
Kessef Mishneh on Mishneh Torah, Creditor and Debtor
Kessef Mishneh on Mishneh Torah, Damages to Property
Kessef Mishneh on Mishneh Torah, Borrowing and Deposit
Kessef Mishneh on Mishneh Torah, Hiring
Kessef Mishneh on Mishneh Torah, Neighbors""".splitlines()
indices = [indices[1]]
for i in indices:
    print("Relinking...\n"+i)
    rebuild_links_for_title(i, 15399)
    time.sleep(20)