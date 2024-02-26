#!/usr/bin/env python3

import os
import json
import lxml.html
import pandas as pd
import requests

from jinja2 import Template

from dracor_jinja2 import xml_template
from pprint import pprint

# DBN download TEI-files.
BASEURL = f'https://www.dbnl.org/nieuws/xml.php?id=%s'
DBNL_AANLEVER = 'Bibliografische metadata RiR gepubliceerd in 1500-1700.xlsx'
LUCAS_AANLEVER = 'Inventarisatie_toneelstukken_DBNL.xlsx'

DBNL_DIR = 'dbnl_xml'

if not os.path.isdir(DBNL_DIR):
    os.mkdir(DBNL_DIR)


def print_dracor_xml(data: dict) -> None:
    pprint(data)
    generated_xml = Template(xml_template).render(data=data)
    print(generated_xml)


def parse_dbnl_aanlever() -> list[dict] | None:
    if not os.path.isfile(DBNL_AANLEVER):
        print(f"Could not read '%s', missing file?" % DBNL_AANLEVER)
        return None

    try:
        df = pd.read_excel(DBNL_AANLEVER)
        wanted = json.loads(df.to_json())
    except:
        print(f"Error parsing %s, file corrupt?" % DBNL_AANLEVER)
        return None

    all_data = []
    for nr in wanted.get('ti_id').keys():
        data = {}
        fn = 'dbnl_xml' + os.sep + str(wanted.get('ti_id').get(nr)) + '.xml'
        if not os.path.isfile(fn):
            # Fetch input xml from DBNL
            res = requests.get(BASEURL % wanted.get('ti_id').get(nr))
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


def parse_lucas_aanlever(data: list[dict]) -> dict | None:
    if not os.path.isfile(LUCAS_AANLEVER):
        print(f"Could not read '%s', missing file?" % LUCAS_AANLEVER)
        return None

    try:
        df = pd.read_excel(LUCAS_AANLEVER)
        wanted = json.loads(df.to_json())
    except:
        print(f"Error parsing %s, file corrupt?" % LUCAS_AANLEVER)
        return None

    all_rows = list(wanted.keys())

    eratta = {}

    for nr in wanted.get('dbnl-ID').keys():

        if not wanted.get('dbnl-ID').get(nr):
            continue

        cur_id = wanted.get('dbnl-ID').get(nr)
        if cur_id in [i.get('ti_id') for i in data]:
            eratta[cur_id] = {}
            for k in all_rows:
                if wanted.get(k).get(nr):
                    eratta[cur_id][k] = wanted.get(k).get(nr)
        else:
            print(f"{cur_id} not found in {DBNL_AANLEVER}")

    for item in data:
        if not item.get('ti_id') in eratta:
            print(f"{item.get('ti_id')} not in {LUCAS_AANLEVER}")

    return eratta


data = parse_dbnl_aanlever()
eratta = parse_lucas_aanlever(data)

for item in data:
    if item.get('ti_id') in eratta:
        merge = {}
        ceratta = eratta.get(item.get('ti_id'))

        for k in item:
            merge[k] = item.get(k)

        for k in ceratta:
            if k.lower() in merge and merge[k.lower()] == ceratta.get(k):
                pass
                #print(k, 'same value, skipping')
            else:
                merge[k.lower()] = ceratta.get(k)

        if 'titel' in merge and 'hoofdtitel' in merge:
            merge['main_title'] = merge['titel']
            merge['subtitle'] = merge.get('subtitel', '')

        print_dracor_xml(merge)
