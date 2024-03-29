#!/usr/bin/env python3

import json
import os
import datetime

from pprint import pprint

import lxml.html
import pandas as pd
import requests
from jinja2 import Template
from Levenshtein import distance

from dracor_jinja2 import xml_template
from dracor_utils import escape, unescape

# DBN download TEI-files.
BASEURL = f'https://www.dbnl.org/nieuws/xml.php?id=%s'
DBNL_AANLEVER = 'Bibliografische metadata RiR gepubliceerd in 1500-1700.xlsx'
LUCAS_AANLEVER = 'Inventarisatie_toneelstukken_DBNL.xlsx'

DBNL_DIR = 'dbnl_xml'
DRACOR_DIR = 'dracor_xml'

LEVENSTEIN_SPEAKER = 3

OUTDIR = 'playlist_per_work'

import datetime

print("Running parse_dbnl_input.py on %s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))

if not os.path.isdir(DBNL_DIR):
    os.mkdir(DBNL_DIR)

if not os.path.isdir(DRACOR_DIR):
    os.mkdir(DRACOR_DIR)


def print_dracor_xml(data: dict) -> None:
    #pprint(data)
    generated_xml = Template(xml_template).render(data=data)

    # Output directory.
    fname = os.path.join(DRACOR_DIR, data.get('ti_id') + '_dracor.xml')

    with open(fname, 'w') as fh:
        fh.write(generated_xml)


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


def speaker_filter(speakerlist: set, newspeaker: str) -> set | tuple:
    newspeaker = escape(newspeaker)

    '''
    #Realy small speakernames are allowed.
    if len(newspeaker) < 2:
        return speakerlist
    '''
    
    if newspeaker in speakerlist:
        for speaker in speakerlist:
            if newspeaker == speaker:
                return speakerlist

    '''
    #Disable Levenshtein for now.
    for speaker in speakerlist:
        if distance(speaker, newspeaker) < LEVENSTEIN_SPEAKER:
            return newspeaker, speaker
    '''
    speakerlist.add(newspeaker)
    return speakerlist


def parse_fulltext(data):
    rec = False
    srec = False

    speakerlist = set()

    chapters = []
    acts = []
    plays = []

    read_order = []

    alias = {}
    ctype = ''
    nexupspeaker = False
    srec1 = False


    for item in data.iter():

        if item.attrib.get('rend', '') == 'speaker' and item.text:
            target = item.text.strip()
            if target.endswith('.'):
                target = target[:-1]
            if not escape(target) in speakerlist:
                speakerinfo = speaker_filter(speakerlist, target)
                if type(speakerinfo) == tuple:
                    alias[speakerinfo[0]] = speakerinfo[1]
                else:
                    speakerlist = speakerinfo
        if item.attrib.get('rend', '') == 'speaker':
            srec = True

        if item.tag == 'speaker':
            srec1 = True

        if srec1 and item.tag == 'hi':
            srec1 = False
            target = item.text.strip()
            if target.endswith('.'):
                target = target[:-1]
            if not escape(target) in speakerlist:
                speakerinfo = speaker_filter(speakerlist, target)
                if type(speakerinfo) == tuple:
                    alias[speakerinfo[0]] = speakerinfo[1]
                else:
                    speakerlist = speakerinfo



        if srec and item.text:
            srec = False
            if not escape(item.text.strip()) in speakerlist:
                target = item.text.strip()
                if target.endswith('.'):
                    target = target[:-1]
                speakerinfo = speaker_filter(speakerlist, target)
                if type(speakerinfo) == tuple:
                    alias[speakerinfo[0]] = speakerinfo[1]
                else:
                    speakerlist = speakerinfo


        if item.tag == 'div':
            if item.attrib.get('type') == 'act':
                rec = True
                if acts:
                    read_order.append({'act': acts})
                acts = ['']
                ctype = 'act'
            if item.attrib.get('type') == 'chapter':
                rec = True
                if chapters:
                    read_order.append({'chapter': chapters})
                chapters = ['']
                ctype =  'chapter'
            if item.attrib.get('type') == 'play':
                rec = True
                if plays:
                    read_order.append({'play': plays})
                ctype = 'play'
                plays = ['']

        if rec:
            if item.text and item.attrib.get('rend', '') == 'speaker' and item.text.strip():
                speak_xml = '\n<speaker>' + escape(item.text) + '</speaker>\n'
                if ctype == 'chapter':
                   chapters[-1] += speak_xml
                if ctype == 'act':
                   acts[-1] += speak_xml
                if ctype == 'play':
                   plays[-1] += speak_xml
            elif item.attrib.get('rend', '') == 'speaker':
                nexupspeaker = True
            elif nexupspeaker and item.text:
                speak_xml = '\n<speaker>' + escape(item.text) + '</speaker>\n'
                nexupspeaker = False

            else:
                if item.text:
                    if ctype == 'chapter':
                       chapters[-1] += escape(item.text)
                    if ctype == 'act':
                       acts[-1] += escape(item.text)
                    if ctype == 'play':
                       plays[-1] += escape(item.text)


    return read_order, speakerlist, alias


data = parse_dbnl_aanlever()
eratta = parse_lucas_aanlever(data)
i = 0

for item in data:
    if item.get('ti_id') in eratta:
        currid = item.get('ti_id')
        merge = {}
        ceratta = eratta.get(currid)

        fname = f"{DBNL_DIR}{os.sep}{currid}.xml"
        if not os.path.isfile(fname):
            print("Missing file:", fname)
            continue

        with open(fname, 'r') as fh:
            fulltext = lxml.etree.fromstring(fh.read().encode('utf-8'))
        merge['readingorder'], merge['speakerlist'], merge['alias'] = parse_fulltext(
            fulltext)


        # Dumping out playlist here, in .xlsx format.
        id_list = ['#' + unescape(i.lower()).replace(' ', '-') for i in merge.get('speakerlist')]
        spv = [unescape(i) for i in merge.get('speakerlist')]
        outdata = {'URL': [ceratta.get('URL') for i in range(len(spv))] , 'id': id_list, 'new_id': ['' for i in range(len(id_list))] ,'speaker_variant': spv, 'is_prefered': ['' for i in range(len(spv)) ], 'is_new': ['' for i in range(len(spv))],
                   'is_error': ['' for i in range(len(spv))], 'gender (Male/Female/Unknown/Other)' : ['' for i in range(len(spv))], 'comments' : ['' for i in range(len(spv))]} 
                #, 'is_error': [], 'gender (Male/Female/Unknown/Other)': [], 'comments':[]}

        for alias in merge['alias']:
            nid = '#' + unescape(merge['alias'].get(alias).lower()).replace(' ', '-')
            alias = escape(alias)
            outdata['URL'].append(ceratta.get('URL'))
            outdata['id'].append(nid)
            outdata['new_id'].append('')
            outdata['speaker_variant'].append(alias)
            outdata['is_prefered'].append('')
            outdata['is_new'].append('')
            outdata['is_error'].append('')
            outdata['gender (Male/Female/Unknown/Other)'].append('')
            outdata['comments'].append('')

        df = pd.DataFrame(outdata)

        fname = OUTDIR + os.sep + currid + '.xlsx'

        print("Writing out %s with %i speakers" % (fname, len(outdata.get('comments'))))

        df.to_excel(fname, index=False)

        for k in item:
            merge[k] = item.get(k)

        for k in ceratta:
            if k.lower() in merge and merge[k.lower()] == ceratta.get(k):
                pass
            else:
                merge[k.lower()] = ceratta.get(k)

        if 'titel' in merge and 'hoofdtitel' in merge:
            merge['main_title'] = merge['titel']
            merge['subtitle'] = merge.get('subtitel', '')

        print_dracor_xml(merge)
