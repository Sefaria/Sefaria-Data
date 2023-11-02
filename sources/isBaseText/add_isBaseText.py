import django
django.setup()
from sefaria.model import *

if __name__ == '__main__':
    for index in IndexSet():
        versions = index.versionSet()
        for version in versions:
            if not getattr(version, 'actualLanguage', None):
                version.actualLanguage = version.language
                print(f'adding actualLang {version.language} to {version}')
        langs = [v.actualLanguage for v in versions]
        if 'he' in langs:
            for version in versions:
                if version.actualLanguage != 'he' or version.versionTitle in ['Hebrew Translation',
                                                                              'Sefer haKuzari - Project Ben-Yehuda', 'Yehudah Even Shmuel, 1973']:
                    version.isBaseText = False
                else:
                    version.isBaseText = True
                version.save()
        else:
            if index.title in ['Teshuvot HaRitva', 'Musafia Teshuvot HaGeonim', 'Yismach Yisrael on Pesach Haggadah', #original is hebrew but we don't have it
                               'Minchat Ani on Pesach Haggadah', 'From Sinai to Ethiopia']\
                    or index.title in ['Legends of the Jews', 'Kol Dodi Dofek', 'Saadia Gaon on Deuteronomy', ##original is a third language that we don't have
                                       'Saadia Gaon on Exodus', 'Saadia Gaon on Numbers', 'Commentary on Selected Paragraphs of Arpilei Tohar']:
                for version in versions:
                    version.isBaseText = False
                    version.save()
            else:
                origLang = 'de' if index.title == 'Rav Hirsch on Torah' else 'en'
                for version in versions:
                    if version.actualLanguage == origLang:
                        version.isBaseText = True
                    else:
                        version.isBaseText = False
                    version.save()
