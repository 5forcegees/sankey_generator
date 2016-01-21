#!/usr/bin/python
import re
from argparse import ArgumentParser
from xlrd import open_workbook
import string
import os.path
import collections
import json

parser = ArgumentParser(description="produces a sankey chart html doc based on the first sheet of a provided xls")
parser.add_argument("-f", "--filename", type=str, help="the path to the xls source file")
parser.add_argument("-o", "--output_dir", type=str, help="the path to the output directory", default='.')

args = parser.parse_args()
filename = args.filename
output_dir = args.output_dir

# parse up the filename so it displays properly in the output file name
head, tail = os.path.split(filename)
filename_no_extension = tail.split('.')[0]

try:
    book = open_workbook(filename)
except IOError:
    print('Could not read file: ' + filename)
    exit()

#assumes we only care about the first sheet
sheet0 = book.sheets()[0]

errors_found = 0
# check for errors in importing the data
for index_r in range(sheet0.nrows):
    for index_col, type in enumerate(sheet0.row_types(index_r)):
        if type == 5:
            print('')
            print('There was an error in importing row: ' + str(index_r + 1))
            print('Please take out weird characters (ex: \'#\') in column: ' + string.uppercase[index_col])
            print('Imported values were: ' + str(sheet0.row_slice(index_r)))
            errors_found += 1
if errors_found:
    exit('\nExiting application.\nSee error text above for details')

rows_by_screen = {}
screen_counts = {}
# loop over the rows, skip the header row
for index_r in range(sheet0.nrows):
    if index_r is 0:
        # skip the column headers row
        continue

    # sacrificing some flexibility for simplicity here, no point in spending a bunch of time on this
    # assuming first 4 columns are screen, facade, core, then e
    # { screen: { layer_num: { value : count }}}
    screen_value = str(sheet0.cell_value(index_r, 0))
    facade_value = str(sheet0.cell_value(index_r, 1))
    core_value = str(sheet0.cell_value(index_r, 2))
    e_value = str(sheet0.cell_value(index_r, 3))
    if screen_value not in rows_by_screen:
        rows_by_screen[screen_value] = {}
        rows_by_screen[screen_value][0] = {}
        rows_by_screen[screen_value][1] = {}
        rows_by_screen[screen_value][2] = {}

    if screen_value not in screen_counts:
        screen_counts[screen_value] = 1
    else:
        screen_counts[screen_value] += 1


    if facade_value not in rows_by_screen[screen_value][0]:
        rows_by_screen[screen_value][0][facade_value] = 1
    else:
        count = int(rows_by_screen[screen_value][0][facade_value]) + 1
        rows_by_screen[screen_value][0][facade_value] = count

    if core_value not in rows_by_screen[screen_value][1]:
        rows_by_screen[screen_value][1][core_value] = 1
    else:
        count = int(rows_by_screen[screen_value][1][core_value]) + 1
        rows_by_screen[screen_value][1][core_value] = count

    if e_value not in rows_by_screen[screen_value][2]:
        rows_by_screen[screen_value][2][e_value] = 1
    else:
        count = int(rows_by_screen[screen_value][2][e_value]) + 1
        rows_by_screen[screen_value][2][e_value] = count

js_output_path = os.path.join(output_dir, "chart_data.js")
jsonfh = open(js_output_path, 'w')
print('writing chart_data.js to ' + js_output_path)
jsonfh.write("""
                   var chart_data =
                """ + json.dumps(rows_by_screen, sort_keys=True) + """ ;

                var screen_counts =
                """ + json.dumps(screen_counts, sort_keys=True) + """ ;
""")
jsonfh.close()
