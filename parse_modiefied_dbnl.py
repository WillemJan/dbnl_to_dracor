#!/usr/bin/env python3

import json
import os, sys
import datetime

from pprint import pprint

import lxml.html
import pandas as pd
import requests
from jinja2 import Template

from dracor_jinja2 import xml_template
from dracor_utils import escape, unescape

from io import BytesIO

BASEURL = f'https://www.dbnl.org/nieuws/xml.php?id=%s'

DBNL_AANLEVER = 'Bibliografische metadata RiR gepubliceerd in 1500-1700.xlsx'
LUCAS_AANLEVER = 'Inventarisatie_toneelstukken_DBNL.xlsx'

DBNL_DIR = 'dbnl_xml'
DRACOR_DIR = 'dracor_xml'

STUDENTEN_DIR = 'perlijsten'

LEVENSTEIN_SPEAKER = 3

OUTDIR = 'playlist_per_work'

import datetime

print("Running parse_dbnl_input.py on %s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))

if not os.path.isdir(DBNL_DIR):
    os.mkdir(DBNL_DIR)

if not os.path.isdir(DRACOR_DIR):
    os.mkdir(DRACOR_DIR)

def pre_remove(fname, to_remove=['<hi>', '</hi>', '<hi rend="i">']):
    with open(fname, 'r') as fh:
        xml_buffer = BytesIO(fh.read().encode())
        xml_data=xml_buffer.read().decode('utf-8')
        for r in to_remove:
            xml_data.replace(r, '')


    mem = ''
    for line in xml_data.split('\n'):
        if line.strip() == '</body>':
           mem += line
           break
        if line.strip() == '<body>' or mem:
           mem += line
           
    xml_buffer = BytesIO(mem.encode())
    xml_buffer.seek(0)

    return xml_buffer

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

    #for item in data:
    #    if not item.get('ti_id') in eratta:
    #        print(f"{item.get('ti_id')} not in {LUCAS_AANLEVER}")

    return eratta


def parse_student_aanlever():
    all_data = {}

    for f in os.listdir(STUDENTEN_DIR):
        if f.find('lock') > -1:
            continue
        all_data[f.replace('_geannoteerd.xlsx', '')] = []
        fn = STUDENTEN_DIR + '/' + f
        df = pd.read_excel(fn)
        data = json.loads(df.to_json())
        parse = {}

        for k in data.keys():
            parse[str(k)] = list(data.get(k).values())

        all_ids = set([i for i in range(0, len(parse['id']))])

        is_pref = []
        for v, c in enumerate(parse['is_prefered']):
            if c:
                is_pref.append(v)
                if v in all_ids:
                    all_ids.remove(v)

        is_new = []
        for v, c in enumerate(parse['is_new']):
            if c:
                is_new.append(v)
                if v in all_ids:
                    all_ids.remove(v)

        is_error = []
        for v, c in enumerate(parse['is_error']):
            if c:
                is_error.append(v)
                if v in all_ids:
                    all_ids.remove(v)


        all_speakers = {}

        new_list = []
        speaker_list = []
        for i in is_pref:
            if not i in is_new:
                all_speakers[parse['id'][i]] = {'gender' : parse['gender (Male/Female/Unknown/Other)'][i],
                                                       'speaker_variant' : parse['speaker_variant'][i]}
                speaker_list.append({parse['id'][i] : {'gender' : parse['gender (Male/Female/Unknown/Other)'][i],
                                                       'speaker_variant' : parse['speaker_variant'][i]}})
            else:
                all_speakers[parse['new_id'][i]] = {'gender' : parse['gender (Male/Female/Unknown/Other)'][i],
                                                       'speaker_variant' : parse['speaker_variant'][i]}
                new_list.append({parse['new_id'][i] : {'gender' : parse['gender (Male/Female/Unknown/Other)'][i],
                                                       'speaker_variant' : parse['speaker_variant'][i]}})

        rename_list = []
        for i in all_ids:
            if not parse['id'][i] == parse['new_id'][i]:
                if parse['new_id'][i]:
                    rename_list.append(
                          [parse['id'][i],
                          parse['new_id'][i],
                          all_speakers.get(parse['new_id'][i])])

        all_data[f.replace('_geannoteerd.xlsx', '')]={'new': new_list,
                                                             'speak': speaker_list,
                                                             'rename': rename_list,
                                                             'all' : all_speakers}
    return all_data 


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


def parse_fulltext(data, cur_id, annodata):
    rec = False
    srec = False

    speakerlist = set()

    chapters = []
    acts = []
    plays = []
    scenes = []

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
                print(speakerlist)
        if item.attrib.get('rend', '') == 'speaker':
            srec = True

        if item.tag == 'speaker':
            srec1 = True


        '''
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
        '''

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
            if item.attrib.get('type') == 'scene':
                rec = True
                if scenes:
                    read_order.append({'scene': scenes})
                ctype = 'scene'
                scenes = ['']


        if rec:
            if item.text and item.attrib.get('rend', '') == 'speaker' and item.text.strip():

                speak_xml = '\n\t<sp who="' +  escape(item.text) + '">\n'
                speak_xml += '\n\t\t<speaker>' +  escape(item.text) + '</speaker>\n'

                if ctype == 'chapter':
                   if "\n".join(chapters).find('<sp who') > -1:
                       chapters[-1] += '</sp>' + speak_xml
                   else:
                       chapters[-1] += speak_xml

                if ctype == 'act':
                   if "\n".join(acts).find('<sp who') > -1:
                       acts[-1] += '</sp>' + speak_xml
                   else:
                       acts[-1] += speak_xml

                if ctype == 'scene':
                   if "\n".join(scenes).find('<sp who') > -1:
                       print('here!!!')
                       scenes[-1] += '</sp>' + speak_xml
                   else:
                       print('aaaaahere!!!')
                       scenes[-1] += speak_xml

                if ctype == 'play':
                   if "\n".join(plays).find('<sp who') > -1:
                        plays[-1] += '</sp>' +  speak_xml
                   else:
                        plays[-1] += speak_xml


                nexupspeaker = False
            elif item.attrib.get('rend', '') == 'speaker':
                nexupspeaker = True
            elif nexupspeaker and item.text:
                speak_xml = '\n\t<sp who="' +  escape(item.text) + '">\n'
                speak_xml += '\n\t\t<speaker>' +  escape(item.text) + '</speaker>\n'
                nexupspeaker = False

                if ctype == 'chapter':
                   if "\n".join(chapters).find('<sp who') > -1:
                        chapters[-1] += '</sp>' + speak_xml
                   else:
                        chapters[-1] += '</l>\n' + speak_xml
                if ctype == 'act':
                   if "\n".join(acts).find('<sp who') > -1:
                       acts[-1] += '</sp>' + speak_xml
                   else:
                       acts[-1] += '</l>\n' + speak_xml
                if ctype == 'scene':
                   if "\n".join(scenes).find('<sp who') > -1:
                       scenes[-1] += '</sp>' + speak_xml
                   else:
                       scenes[-1] += speak_xml
                if ctype == 'play':
                   if "\n".join(plays).find('<sp who') > -1:
                       plays[-1] += '</sp>' + speak_xml
                   else:
                       plays[-1] += '</l>\n' + speak_xml

            else:
                if item.text:
                    txt = '\t\t\t<l>' + escape(item.text) + '</l>\n'
                    if item.text.strip():
                        if ctype == 'chapter':
                           chapters[-1] += txt
                        if ctype == 'act':
                           acts[-1] += txt
                        if ctype == 'play':
                           plays[-1] += txt
                    if ctype == 'scene':
                       if str(item.tag) == 'sp':
                           nexupspeaker = True
                       if item.text.strip():
                           scenes[-1] += '\t\t\t<l>' + escape(item.text) + '</l>\n'

    #print(cur_id)
    #pprint(alias)
    #pprint(read_order)
    #pprint(speakerlist)
    return read_order, speakerlist, alias


data = parse_dbnl_aanlever()
eratta = parse_lucas_aanlever(data)
speakers = parse_student_aanlever()
i = 0
for item in data:
    if item.get('ti_id') in eratta:
       currid = item.get('ti_id')
       # for now only parse the modified one..
       if not currid == 'asse001kwak01':
          continue
       print(currid)
       fname = f"{DBNL_DIR}{os.sep}{currid}.xml"
       fh = pre_remove(fname)
       fulltext = lxml.etree.fromstring(fh.read())
       merge = {}
       ceratta = eratta.get(currid)
       merge['readingorder'], merge['speakerlist'], merge['alias'] = parse_fulltext(fulltext, currid, speakers)
       '''
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

        '''
        #print(id_list)

        #df = pd.DataFrame(outdata)
        #fname = OUTDIR + os.sep + currid + '.xlsx'
        #print("Writing out %s with %i speakers" % (fname, len(outdata.get('comments'))))
        #df.to_excel(fname, index=False)

       for k in item:
           merge[k] = item.get(k)

       for k in ceratta:
           if k.lower() in merge and merge[k.lower()] == ceratta.get(k):
               pass
           else:
               merge[k.lower()] = ceratta.get(k)

       if 'titel' in merge and 'hoofdtitel' in merge:
          try:
              merge['main_title'] = merge['titel']
              merge['subtitle'] = merge.get('subtitel', '')
              merge['annotated'] = speakers[currid]
              merge['speakerlist'] = speakers[currid].get('all')
	      #pprint(merge['speakerlist'])
              print_dracor_xml(merge)
          except:
              pass

