# encoding=utf-8

import unicodecsv as csv
import json
import urllib2
import re
from sources import functions
from sefaria.model import *


def read_csv(filename):

    data = []
    with open(filename) as data_file:
        names = csv.DictReader(data_file, encoding='utf-8')

        for line in names:
            data.append(line)
    return data


def add_mitzva(mitzva, index):
    """
    Create an ArrayMapNode for an individual Mitzva
    :param mitzva: Dictionary with keys "English" and "Hebrew" for corresponding language names.
    :param index: Index of the mitzva to be called by Ref or url
    :return: Assembled ArrayMapNode
    """

    # check if English was added
    if re.search(u'English Translation Here', mitzva['English']):
        mitzva['English'] = u'Mitzva {}'.format(index)

    node = ArrayMapNode()
    node.wholeRef = 'Minchat Chinukh.{}'.format(index)
    node.depth = 0
    node.add_title(mitzva['English'], 'en', True)
    node.add_title(mitzva['Hebrew'], 'he', True)

    return node


def add_parsha(parsha_name, children, mitzva_node_list):
    """
    Creates a SchemaNode for a parsha with all ArrayMapNodes for mitzvot properly appended
    :param parsha_name: Name of the Parsha
    :param children: Integer or range (i.e. 3-8)
    :param mitzva_node_list: A list of ArrayMapNodes from which to select children for this Node.
    :return: SchemaNode
    """

    # determine if node has one child or many
    if children.find('-') >= 0:
        edges = [int(x) for x in children.split('-')]
        child_nodes = mitzva_node_list[edges[0]-1:edges[1]]

    else:
        child_nodes = [mitzva_node_list[int(children)-1]]

    node = SchemaNode()
    node.add_shared_term(parsha_name)
    for child in child_nodes:
        node.append(child)

    return node


def construct_alt_struct(parsha_file, mitzva_file):

    mitzvot, parashot = read_csv(mitzva_file), read_csv(parsha_file)
    mitzva_nodes= []
    root = SchemaNode()

    for index, mitzva in enumerate(mitzvot):
        mitzva_nodes.append(add_mitzva(mitzva, index+1))

    for parsha in parashot:
        root.append(add_parsha(parsha['Parsha'], parsha['Includes'], mitzva_nodes))

    return root

s = construct_alt_struct('Chinukh_by_Parsha.csv', 'Chinukh Mitzva names.csv')
data = {
        'Parsha': s.serialize()
}

raw = urllib2.urlopen('http://www.sefaria.org/api/v2/raw/index/Sefer_HaChinukh')
index = json.load(raw)
index['alt_structs'] = data
index['default_struct'] = 'Parsha'

functions.post_index(index)
