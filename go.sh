#!/bin/bash
# test if output is at least xml-valid.
#
python3 parse_dbnl_input.py > output_all.txt ; xmllint coor001come04_dracor.xml  --format   > coor001come04_dracor1.xml ; mv coor001come04_dracor1.xml coor001come04_dracor.xml
