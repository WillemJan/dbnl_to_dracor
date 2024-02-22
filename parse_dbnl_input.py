#!/usr/bin/env python3

import json
import os
from pprint import pprint
from lxml import etree

import lxml.html
import pandas as pd
import requests

baseurl = f'https://www.dbnl.org/nieuws/xml.php?id=%s' # DBN download TEI-files.
infile = 'Bibliografische metadata RiR gepubliceerd in 1500-1700.xlsx' # Input xls file.


#def _fetch_dbnlxml_byid(dbnlid: str, outdir='xml': str) -> bool:

from dataclasses import dataclass
from typing import List

@dataclass
class Play:
    title: str
    author: Author
    year: str
    place_of_publication: str
    publisher: str
    library: str
    category: str
    country: str
    edition: Edition
    translator: Translator
    link: str
    shelfmark: str
    full_text: str
    actors: List[Actor]

@dataclass
class Author:
    first_name: str
    last_name: str
    prefix: str

@dataclass
class Edition:
    edition_number: str
    edition_type: str

@dataclass
class Translator:
    first_name: str
    last_name: str

@dataclass
class Actor:
    actor_name: str
    role: str






def print_dracor_xml(data: list[dict]):
    for item in data:
        root = etree.Element("plays")
        play = etree.SubElement(root, "play")

        etree.SubElement(play, "title").text = item.get('titel', '')

        author = etree.SubElement(play, "author")
        etree.SubElement(author, "first_name").text = item.get('voornaam', '')
        etree.SubElement(author, "last_name").text = item.get('achternaam', '')

        etree.SubElement(play, "year").text = item.get('jaar', '')
        etree.SubElement(play, "place_of_publication").text = item.get('plaats_van_uitgave', '')
        etree.SubElement(play, "publisher").text = item.get('uitgever', '')
        etree.SubElement(play, "library").text = item.get('bibliotheek', '')
        etree.SubElement(play, "category").text = item.get('categorie', '')
        etree.SubElement(play, "country").text = item.get('cc_land', '')

        edition = etree.SubElement(play, "edition")

        druk_value = item.get('druk', '')
        if ' ' in druk_value:
            edition_number, edition_type = druk_value.split(maxsplit=1)
        else:
            edition_number, edition_type = '', ''


        etree.SubElement(edition, "edition_number").text = edition_number
        etree.SubElement(edition, "edition_type").text = edition_type

        if item.get('vertaler.voornaam') or item.get('vertaler.achternaam'):
            translator = etree.SubElement(play, "translator")
            etree.SubElement(translator, "first_name").text = item.get('vertaler.voornaam', '')
            etree.SubElement(translator, "last_name").text = item.get('vertaler.achternaam', '')

        etree.SubElement(play, "link").text = item.get('link', '')
        etree.SubElement(play, "shelfmark").text = item.get('signatuur', '')

        xml_output = etree.tostring(root, pretty_print=True, encoding='utf-8').decode()
        print(xml_output)


def parse_metadata(infile: str, baseurl: str) -> list[dict] | None:
    if not os.path.isfile(infile):
        print(f"Could not read '%s', missing file?" % infile)
        return None

    try:
        df = pd.read_excel(infile)
        wanted = json.loads(df.to_json())
    except:
        print(f"Error parsing %s, file corrupt?" % infile)
        return None


    # convert row's into a nice python list with dicts.
    '''
        [{'achternaam': 'Coornhert',
          'bibliotheek': 'Universiteitsbibliotheek Amsterdam',
          'categorie': 'werk',
          'cc_land': 'nl',
          'druk': '1ste druk',
          'geplaatst': 'coor001come04_01',
          'jaar': '1590',
          'link': 'https://www.dbnl.org/tekst/coor001come04_01',
          'plaats_van_uitgave': 'Gouda',
          'signatuur': 'OTM: OK 61-782 (2), scan van Google Books',
          'subtitel': [],
          'ti_id': 'coor001come04',
          'titel': 'Comedie van Israel',
          'uitgever': '[Jasper Tournay]',
          'vertaler.achternaam': [],
          'vertaler.voornaam': [],
          'vertaler.voorvoegsel': [],
          'voornaam': 'D.V.',
          'voorvoegsel': []},
         {'achternaam': 'Groot',

    '''

    all_data = []

    for nr in wanted.get('ti_id').keys():

        data = {}

        fn = 'xml' + os.sep + str(wanted.get('ti_id').get(nr)) + '.xml'
        if not os.path.isfile(fn):
            res = requests.get(baseurl % wanted.get('ti_id').get(nr))
            if not res.status_code == 200:
                print(f"Error getting %s" % fn)

            with open(fn, 'w') as fh:
                fh.write(res.content.decode('utf-8'))

        for key in wanted.keys():
            value = wanted.get(key).get(nr)
            if value is None:
                continue

            if not key in data:
                data[key] = value

        all_data.append(data)


    return all_data


#data = parse_metadata(infile, baseurl)
#pprint(data)
#print_dracor_xml(data)

