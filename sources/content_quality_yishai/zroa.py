import django
django.setup()
from sefaria.helper.category import move_index_into
from sefaria.model import *

move_index_into('Zeroa Yamin', ["Mishnah", "Acharonim on Mishnah"])
c = Category().load({'path': ["Mishnah", "Acharonim on Mishnah", "Zeroa Yamin", "Seder Nezikin"]})
c.delete()
c = Category().load({'path': ["Mishnah", "Acharonim on Mishnah", "Zeroa Yamin"]})
c.delete()
