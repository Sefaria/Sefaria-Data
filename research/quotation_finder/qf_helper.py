import django, re, requests, json
from collections import defaultdict
django.setup()
from collections import namedtuple
import unicodecsv as csv
from sources.functions import *
from sources.Scripts.pesukim_linking import *
import numpy as np
import pymongo
from sefaria.settings import *
from research.quotation_finder.dicta_api import *

client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)  # (MONGO_ASPAKLARIA_URL)
db_qf = client.quotations


def get_version_mapping(version: Version) -> dict:
    """
    version: version object of text being modified
    """
    def populate_change_map(old_text, en_tref, he_tref, _):
        nonlocal mapping
        mapping[en_tref] = old_text

    mapping = {}
    version.walk_thru_contents(populate_change_map)
    return mapping


def create_file_for_offline_run(version: Version, filename: str):
    vm = get_version_mapping(version)
    write_links_to_json(filename, vm)
    return vm


def offline_files_for_category(indexs, dir_name):
    """

    :param indexs: list of index names
    :return: list of version mappings for the indexs given (that have a hebrew version)
    """
    vms = []
    os.chdir("/home/shanee/www/Sefaria-Data/research/quotation_finder/offline/text_mappings")
    os.mkdir(dir_name)
    os.chdir(dir_name)
    for ind_name in indexs:
        ind = library.get_index(ind_name)
        he_versions = [v for v in ind.versionSet() if v.language == 'he']
        if he_versions == []:
            print(f"error: no hebrew version for '{ind_name}'")
            continue
        v = he_versions[0]
        vm = create_file_for_offline_run(v, filename=f'{ind_name}')
        print(f"created offline file for {ind_name}")
        vms.append(vm)
    return vms

if __name__ == '__main__':
    indexs = library.get_indexes_in_category("Musar")
    # Tanakh = library.get_indexes_in_category("Tanakh")
    # indexs = [ind for ind in library.get_indexes_in_category_path(['Tanakh'], include_dependant = True) if ind not in Tanakh and 'Targum' not in library.get_index(ind).categories]

    error_indexs = ['Legends of the Jews',
                    'Tzidkat HaTzadick',
                    'Flames of Faith',
                    'Sichat Malachei HaSharet',
                    'Rav Hirsch on Torah',
                    'Depths of Yonah',
                    'Footnotes to Kohelet by Bruce Heitler',
                    'From David to Destruction',
                    'JPS 1985 Footnotes',
                    'Moses; A Human Life',
                    'Rav Hirsch on Torah',
                    'Redeeming Relevance; Deuteronomy',
                    'Redeeming Relevance; Exodus',
                    'Redeeming Relevance; Genesis',
                    'Redeeming Relevance; Numbers',
                    'Saadia Gaon on Deuteronomy',
                    'Saadia Gaon on Exodus',
                    'Saadia Gaon on Numbers',
                    'Hadran for Tanach',
                    'Kabbolos Shabbos',
                    'Shalom Alechem',
                    ]
    offline_files_for_category(indexs, dir_name='Musar')
