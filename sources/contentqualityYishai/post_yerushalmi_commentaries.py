import django
django.setup()
from sefaria.model import *
from move_draft_text import ServerTextCopier

server = 'https://www.sefaria.org'
apikey = 'F3XF80E9J46VMrT95bwASLRPYkhmLT1GYrr34fGC2kw'
inds = [Version().load({'title': 'Haggahot RaDO on Jerusalem Talmud Berakhot', 'versionTitle': 'Piotrków, 1898-1900'}),
 Version().load({'title': 'Amudei Yerushalayim on Jerusalem Talmud Challah', 'versionTitle': 'Piotrków, 1898-1900'}),
 Version().load({'title': 'Amudei Yerushalayim on Jerusalem Talmud Sukkah', 'versionTitle': 'Piotrków, 1898-1900'}),
 Version().load({'title': 'Amudei Yerushalayim on Jerusalem Talmud Taanit', 'versionTitle': 'Piotrków, 1898-1900'}),
 Version().load({'title': 'Amudei Yerushalayim on Jerusalem Talmud Terumot', 'versionTitle': 'Piotrków, 1898-1900'}),
 Version().load({'title': 'Haggahot YaFeM on Jerusalem Talmud Shekalim', 'versionTitle': 'Piotrków, 1898-1900'}),
 Version().load({'title': 'Haggahot YaFeM on Jerusalem Talmud Berakhot', 'versionTitle': 'Piotrków, 1898-1900'}),
 Version().load({'title': 'Chidushei Chatam Sofer on Jerusalem Talmud Avodah Zarah', 'versionTitle': 'Piotrków, 1898-1900'}),
 Version().load({'title': 'Chidushei Chatam Sofer on Jerusalem Talmud Megillah', 'versionTitle': 'Piotrków, 1898-1900'}),
 Version().load({'title': 'Chidushei Chatam Sofer on Jerusalem Talmud Pesachim', 'versionTitle': 'Piotrków, 1898-1900'}),
 Version().load({'title': 'Chidushei Chatam Sofer on Jerusalem Talmud Berakhot', 'versionTitle': 'Piotrków, 1898-1900'}),
 Version().load({'title': 'Chidushei Chatam Sofer on Jerusalem Talmud Bava Batra', 'versionTitle': 'Piotrków, 1898-1900'}),
 Version().load({'title': 'Chidushei Chatam Sofer on Jerusalem Talmud Sukkah', 'versionTitle': 'Piotrków, 1898-1900'}),
 Version().load({'title': 'Chidushei Chatam Sofer on Jerusalem Talmud Eruvin', 'versionTitle': 'Piotrków, 1898-1900'}),
 Version().load({'title': 'Chidushei Chatam Sofer on Jerusalem Talmud Kiddushin', 'versionTitle': 'Piotrków, 1898-1900'}),
 Version().load({'title': 'Chidushei Chatam Sofer on Jerusalem Talmud Shekalim', 'versionTitle': 'Piotrków, 1898-1900'}),
 Version().load({'title': 'Chidushei Chatam Sofer on Jerusalem Talmud Peah', 'versionTitle': 'Piotrków, 1898-1900'}),
 Version().load({'title': 'Chidushei Chatam Sofer on Jerusalem Talmud Kilayim', 'versionTitle': 'Piotrków, 1898-1900'}),
 Version().load({'title': 'Chidushei Rabbi Eliyahu of Greiditz on Jerusalem Talmud Beitzah', 'versionTitle': 'Piotrków, 1898-1900'}),
 Version().load({'title': 'Haggahot Rabbi Menachem di Lonzano on Jerusalem Talmud Gittin', 'versionTitle': 'Piotrków, 1898-1900'}),
 Version().load({'title': 'Haggahot Rabbi Menachem di Lonzano on Jerusalem Talmud Moed Katan', 'versionTitle': 'Piotrków, 1898-1900'}),
 Version().load({'title': 'Haggahot Rabbi Menachem di Lonzano on Jerusalem Talmud Kiddushin', 'versionTitle': 'Piotrków, 1898-1900'}),
 Version().load({'title': 'Haggahot Rabbi Menachem di Lonzano on Jerusalem Talmud Shekalim', 'versionTitle': 'Piotrków, 1898-1900'}),
 Version().load({'title': 'Haggahot Rabbi Menachem di Lonzano on Jerusalem Talmud Peah', 'versionTitle': 'Piotrków, 1898-1900'}),
 Version().load({'title': 'Kikar LaAden on Jerusalem Talmud Terumot', 'versionTitle': 'Piotrków, 1898-1900'}),
 Version().load({'title': 'Kikar LaAden on Jerusalem Talmud Sheviit', 'versionTitle': 'Piotrków, 1898-1900'}),
 Version().load({'title': 'Kikar LaAden on Jerusalem Talmud Makkot', 'versionTitle': 'Piotrków, 1898-1900'}),
 Version().load({'title': 'Kikar LaAden on Jerusalem Talmud Sanhedrin', 'versionTitle': 'Piotrków, 1898-1900'})]

for ind in inds:
    ind = ind.title
    print(ind)
    stc = ServerTextCopier(server, apikey, ind)
    stc.do_copy()
    print('index posted')
    stc = ServerTextCopier(server, apikey, ind, False, versions='all')
    stc.do_copy()
    print('text posted')
    stc = ServerTextCopier(server, apikey, ind, False, post_links=2, step=400)
    stc.do_copy()
    print('links posted')
