import django
django.setup()
from sefaria.model import *

inds = ["Chidushei Halachot on Bava Metzia", "Chidushei Halachot on Bava Kamma", "Chidushei Halachot on Berakhot", "Chidushei Halachot on Yoma", "Chidushei Halachot on Niddah", "Chidushei Halachot on Rosh Hashanah", "Chidushei Halachot on Shabbat", "Chidushei Agadot on Bava Batra", "Chidushei Agadot on Bava Metzia", "Chidushei Agadot on Bava Kamma", "Chidushei Agadot on Yevamot", "Chidushei Agadot on Keritot", "Chidushei Agadot on Megillah", "Chidushei Agadot on Niddah", "Chidushei Agadot on Sotah", "Chidushei Agadot on Sanhedrin", "Chidushei Agadot on Avodah Zarah", "Chidushei Agadot on Kiddushin"]
for ind in inds:
    Ref(ind).linkset().delete()
