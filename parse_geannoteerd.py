#!/usr/bin/env python3

import os
import pandas as pd
import json

from pprint import pprint

WORK_DIR = 'geannoteerd'


def parse_input(data):
    data = json.loads(data.to_json())
    parse = {}

    for k in data.keys():
        parse[str(k)] = list(data.get(k).values())

    is_pref = []

    for v, c in enumerate(parse['is_prefered']):
        if c:
            print(parse['id'][v])


for f in os.listdir(WORK_DIR):
    parse_input(pd.read_excel(WORK_DIR + os.sep + f))
