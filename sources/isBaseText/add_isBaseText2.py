import django
django.setup()
from sefaria.model import *
import re

if __name__ == '__main__':
    for index in IndexSet():
        versions = index.versionSet()
        langs = {getattr(v, 'actualLanguage', '') for v in versions}
        for version in versions:
            if not hasattr(version, 'actualLanguage'):
                if index.title == 'Pele Yoetz':
                    if version.versionTitle == 'Torat Emet':
                        version.actualLanguage = 'he'
                        continue
                    elif version.versionTitle in ['Sefaria Community Translation', 'itorah.com/pele-yoetz']:
                        version.actualLanguage = 'en'
                        continue
                print(f'version {version} of index {index} has no actualLanguage')
                continue

            #add direction
            version.direction = 'rtl' if version.language == 'he' else 'ltr'

            #fix actual language
            if version.versionTitle in ['Vocalized Zohar, Israel 2013', 'Sulam Edition, Jerusalem 1945']: #aramaic
                #also megilat antiochus. what with targumim?
                pass #aramaic code?
            elif version.versionTitle == 'Cuzary  de Yehuda ha Leví(es)':
                version.versionTitle = 'Cuzary de Yehuda ha Leví [es]'
                version.actualLanguage = 'es'
            elif version.versionTitle == 'Kitab al Khazari [Judeo-Arabic]':
                version.versionTitle = 'Kitab al Khazari [jrb]'
                version.actualLanguage = 'jrb'
            elif version.versionTitle == 'Mishneh Torah, Arrepentimiento[esp]':
                version.versionTitle = 'Mishneh Torah, Arrepentimiento [es]'
                version.actualLanguage = 'es'
            elif version.versionTitle == 'Trazladado en la lingua Espanyola, Estamperia de A. H. Boyadjian, Konstantinopla 1873. Transkrito por Yehuda Sidi, 2021 [lad]':
                # version.versionTitle = 'Trazladado en la lingua Espanyola, Estamperia de A. H. Boyadjian, Konstantinopla 1873. Transkrito por Yehuda Sidi, 2021'
                version.actualLanguage = 'lad'
            elif version.versionTitle == '[pt-br]':
                # version.versionTitle = 'Mishnah Bava Kamma in Portuguese [pt]' #?
                version.actualLanguage = 'pt' #?


            #truncate code from versionTitle
            regex = '\[[^\]]*\]$'
            if re.search(regex, version.versionTitle):
                if re.search('\[([^\]\d]*)\]$', version.versionTitle) and re.findall('\[([^\]\d]*)\]$', version.versionTitle)[0] != version.actualLanguage:
                    if not any(word in version.versionTitle for word in ['Onkelos', 'translitteration', 'Rev']):
                        print(version.title, version.versionTitle, version.actualLanguage)
                else:
                    pass
                    # version.versionTitle = re.sub(regex, '', version.versionTitle)


            # add isSource and isPrimary

            # original is hebrew but we don't have it
            if index.title in ['Teshuvot HaRitva', 'Musafia Teshuvot HaGeonim', 'Yismach Yisrael on Pesach Haggadah',
                               'Minchat Ani on Pesach Haggadah', 'From Sinai to Ethiopia']:
                version.isPrimary = True
                version.isSource = False

            #original is a third language that we don't have
            elif index.title in ['Legends of the Jews', 'Kol Dodi Dofek', 'Saadia Gaon on Deuteronomy',
                                       'Saadia Gaon on Exodus', 'Saadia Gaon on Numbers', 'Commentary on Selected Paragraphs of Arpilei Tohar']:
                if version.versionTitle in ['The Legends of the Jews by Louis Ginzberg [1909]', 'Eliyahu Munk, HaChut Hameshulash', 'Selected Paragraphs from Arfilei Tohar, comm. Pinchas Polonsky']:
                    version.isPrimary = True
                    version.isSource = False

            #second temple
            elif 'Philo' in index.categories:
                version.isPrimary = True
                if index.title == 'The Midrash of Philo':
                    version.isSource = True # this is arguable
                else:
                    version.isSource = False
            elif 'Josephus' in index.categories:
                if version.actualLanguage == 'he':
                    version.isPrimary = True
                    version.isSource = False
            elif 'Apocrypha' in index.categories:
                if index.title == 'Megillat Antiochus':
                    if version.versionTitle == 'the Open Siddur Project - Aramaic':
                        version.isSource = True
                elif index.title == 'Ben Sira':
                    if version.versionTitle == 'Ben Sira, David Kahana ed. -- Wikisource':
                        version.isSource = True
                        version.isPrimary = True
                else:
                    if version.actualLanguage == 'he':
                        version.isPrimary = True

            #original is a third landuage we have
            elif index.title in ['Rav Hirsch on Torah', 'What is the Talmud']:  # original German we have
                if version.actualLanguage == 'de':
                    version.isSource = True
            elif index.title == 'On Resurrection of the Dead':
                if version.actualLanguage == 'es':
                    version.isSource = True
            elif index.title == 'Kuzari':
                if version.versionTitle == 'Kitab al Khazari [jrb]':
                    version.isSource = True


            elif 'he' in langs:
                if index.title == 'Zohar':
                    if version.versionTitle in ['Vocalized Zohar, Israel 2013', 'Sulam Edition, Jerusalem 1945']:
                        version.isSource = True
                        version.isPrimary = True
                else:
                    if version.actualLanguage == 'he':
                        version.isSource = True
                        version.isPrimary = True

            elif 'en' in langs:
                if version.actualLanguage == 'en':
                    version.isSource = True
                    version.isPrimary = True

            else:
                print('no hebrew and english', index.title, version.versionTitle)

            if not getattr(version, 'isSource', None):
                version.isSource = False

            try:
                version.save()
            except Exception as e:
                if not isinstance(e, TypeError): # any save of changed versionTitle cause TypeError (b/c ES) but works
                    print(f'error with saveing {version}: {e}')

for index in IndexSet():
    if not [v for v in index.versionSet() if hasattr(v, 'isPrimary')]:
        print(f'no default for {index}')
