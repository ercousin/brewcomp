#############################################################################
# Convert CSV Export to Results Formats for GTA Brews Homebrew Competitions
# - Recommend to use <comp>_Entries_All_All_<date>.csv
#############################################################################

import argparse
import datetime
import re
import os.path
from collections import defaultdict
import csv
import pprint

################
# GLOBALS
################
current_year = datetime.datetime.now().year


################
# Parse Args
################
parser = argparse.ArgumentParser()
parser.add_argument('-csv', dest="csv_file", required=True)
parser.add_argument('-year', default=current_year)
parser.add_argument('-d','--debug', action='store_true')
args = parser.parse_args()

assert os.path.isfile(args.csv_file), 'ERROR: Unable to open {}'.format(args.csv_file)


################
# Dependent GLOBALS
################
# Output File Names
debug_file = str(args.year) + "_debug_results.txt"
medal_engravings_file = str(args.year) + "_medal_engravings.txt"
results_html = str(args.year) + "_results.html"


################
# MAIN()
################
def main():

    results = gen_results_by_table(args.csv_file)

    engravings = gen_medal_engravings(results)
    with open(medal_engravings_file,'w', encoding='utf-8') as engravings_fh:
        engravings_fh.write(engravings)

    results_html_s = gen_html_results(results)
    with open(results_html,'w', encoding='utf-8') as results_fh:
        results_fh.write(results_html_s)


################
# Generate Results Data Structure
################
def gen_results_by_table(csv_file):
    results_by_table = {
                       'BOS': {
                              'Places': defaultdict(dict),
                       },
    }

    def process_csv_line(line):
#        print('DEBUG (process_csv_line): line = ' + str(line))
        def get_table(line):
            m = re.search(r'^([\d]+): ([\w/&;| ]+)$',line['Table'])
            table_num = re.sub(r'^0+','',m.group(1))
            table_name= re.sub(r'&amp;','&',m.group(2))
            table = table_num + ' - ' + table_name
            return table

        def get_entry_info(line):
            brewer = line['Brewer First Name'] + ' ' + line['Brewer Last Name']
            style  = line['Category'] + line['Sub Category'] + ': ' + line['Style']
            return {
                   'Brewer'    : brewer,
                   'Co-Brewer' : line['Co Brewer'],
                   'Entry Name': line['Entry Name'],
                   'Style'     : style,
                   'Club'      : line['Club'],
            }

        if (not int(line['Score']) > 0):
            return

        table = get_table(line)
        if (not table in results_by_table):
            results_by_table[table] = {
                                      'Entries Judged': 0,
                                      'Places'        : defaultdict(dict),
            }

        results_by_table[table]['Entries Judged'] += 1

        if (line['Place'] in ['1','2','3','5']):
            place  = 'HM' if (line['Place'] == '5') else line['Place']
            results_by_table[table]['Places'][place] = get_entry_info(line)

        bos_place = line['Best of Show Place']
        if (bos_place):
            results_by_table['BOS']['Places'][bos_place] = get_entry_info(line)

    with open(args.csv_file,'r', encoding='utf-8-sig') as csv_fh:
        for line in csv.DictReader(csv_fh):
            process_csv_line(line)

    for table in results_by_table.keys():
#        print('DEBUG (sort_places): ' + str(results_by_table[table]['Places']))
        results_by_table[table]['Places'] = dict(sorted(results_by_table[table]['Places'].items()))

    def tables_sorting(item):
        m = re.match(r'^([\w]+)( -)?',str(next(iter(item))))
        table_num = 999 if (m.group(1) == 'BOS') else int(m.group(1))
        return table_num

    results_by_table = dict(sorted(results_by_table.items(), key=tables_sorting))
    
    # Print to Debug File
    if args.debug:
        with open(debug_file,'w', encoding='utf-8') as debug_fh:
            results_s = pprint.pformat(results_by_table, width=250, compact=False, sort_dicts=False)
            debug_fh.write( results_s.encode('utf-8') )

    return results_by_table


################
# Medal Engravings
################
def gen_medal_engravings(results):
    # Medal Places
    def medals_place(place):
        return {
               '1' : '1st Place',
               '2' : '2nd Place',
               '3' : '3rd Place',
        }[place]

    engravings_s = ''
    for table in results.keys():
        engravings_s += '*' + table + ':*\n\n'
        for place_k in results[table]['Places'].keys():
            if (place_k == 'HM'):
                continue
            place_d = results[table]['Places'][place_k]
            engravings_s += str(args.year) + ' - ' + medals_place(place_k) + '\n'
            engravings_s += re.sub(r'^[\d]+ - ','',table) + '\n'
            engravings_s += place_d['Brewer'] + '\n'
    
            co_brewer = place_d['Co-Brewer']
            if (co_brewer):
                engravings_s += co_brewer + '\n\n'
            else:
                engravings_s += place_d['Entry Name'] + '\n\n'
    return engravings_s


################
# Results HTML
################
def gen_html_results(results):
    # Result Places
    def results_place(place):
        return {
               '1' : '1st',
               '2' : '2nd',
               '3' : '3rd',
               'HM': 'HM',
        }[place]

    # HTML String
    html_s = ''
    for table in results.keys():
        if (table == 'BOS'):
           html_s += '<h2>' + table + ':</h2>\n'
        else:
           html_s += '<h2>' + table + ' ({} entries):</h2>\n'.format(results[table]['Entries Judged'])
        html_s += '<figure class="wp-block-table">\n'
        html_s += '<table>\n'
        html_s += '  <thead>\n'
        html_s += '    <tr>\n'
        html_s += '      <th><b>Pl.</b></th>\n'
        html_s += '      <th><b>Brewer(s)</b></th>\n'
        html_s += '      <th><b>Entry Name</b></th>\n'
        html_s += '      <th><b>Style</b></th>\n'
        html_s += '      <th><b>Club</b></th>\n'
        html_s += '    </tr>\n'
        html_s += '  </thead>\n'
        html_s += '  <tbody>\n'
        for place_k in results[table]['Places'].keys():
            place_d = results[table]['Places'][place_k]
            html_s += '    <tr>\n'
            html_s += '      <td>' + results_place(place_k) + '</td>\n'
            brewers = place_d['Brewer']
            co_brewer = place_d['Co-Brewer']
            if co_brewer:
                brewers += ' Co-Brewer: ' + co_brewer
            html_s += '      <td>' + brewers + '</td>\n'
            html_s += '      <td>' + place_d['Entry Name'] + '</td>\n'
            html_s += '      <td>' + place_d['Style'] + '</td>\n'
            html_s += '      <td>' + place_d['Club'] + '</td>\n'
            html_s += '    </tr>\n'
            
        html_s += '  </tbody>\n'
        html_s += '</table>\n'
        html_s += '</figure>\n\n'
    return html_s


################
# Run MAIN()
################
main()
