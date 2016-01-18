#!/usr/bin/python
import re
from argparse import ArgumentParser
from xlrd import open_workbook
import string
import os.path

parser = ArgumentParser(description="produces a sankey chart html doc based on the first sheet of a provided xls")
parser.add_argument("-f", "--filename", type=str, help="the path to the xls source file")
parser.add_argument("-o", "--output_dir", type=str, help="the path to the output directory", default='.')
parser.add_argument("-d", "--default_l2_display", type=str, help="the default L2 value to display before user selection\n\
                                                                 can be passed in as string value or int\
                                                                 if string: try matching on the value\
                                                                 if int: use the int as the index value of the L2 list",
                    default='')
parser.add_argument("-w", "--width", type=int, help="the desired chart width" )
parser.add_argument("-hi", "--height", type=int, help='the desired chart height.  Will try to set intelligent \
                                                        height based on number of links if none is passed in')
# will only accept 2-5 layers
parser.add_argument("-n", "--num_layers", type=int, help="the desired number of layers", choices=range(2, 6), default=4)
parser.add_argument("-cl2", "--combine-l2", action="store_true", default=False,
                    help="If -cl2 is passed lump all the rows together regardless of L2 value.  \
                    Otherwise produce a separate outfile for each L2 value")

args = parser.parse_args()
filename = args.filename
output_dir = args.output_dir
width = args.width if args.width else '100%'
if isinstance(width, int):
    width = str(width) + 'px'
height = args.height
num_layers = args.num_layers if args.num_layers else 6
combine_l2 = args.combine_l2 if args.combine_l2 else False


# parse up the filename so it displays properly in the output file name
head, tail = os.path.split(filename)
filename_no_extension = tail.split('.')[0]


# defs
def quote(foo):
    if isinstance(foo, int):
        return (foo)
    elif isinstance(foo, str) or isinstance(foo, unicode):
        return '\"' + foo + ' \"'
    else:
        print(str(foo) + ' is a ' + str(type(foo)))
        exit("def quote got passed a thing that was not a string or int")

print('\nUsing file \'' + filename + '\' as sourcefile')

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

l2_column_index = 0
has_l2_column = False
# get the values of the header row
# assumes first row has column headers
for index_col, value in enumerate(sheet0.row_values(0)):
    if value == 'L2':
        has_l2_column = True
        l2_column_index = index_col

ignore = ['N/A', 'L2']
l2_values = []
if has_l2_column and not combine_l2:
    for col_value in sheet0.col_values(l2_column_index):
        if col_value not in l2_values and col_value not in ignore:
            l2_values.append(col_value)
else:
    l2_values = [filename_no_extension]

# link_count carries the number of times each link exists, will be used for weight in the chart
link_count = {}

# the key for the layers dict is just the sankey layer number
# the value for each layer is a list of the strings we'll use to build the html
# the list preserves the order of appended items, which is needed for correct chart display
l2_layers = {}

na_regex = re.compile('N\/A|TBD|0')

for l2_value in l2_values:
    layers = {}
    for index_r in range(sheet0.nrows):
        # make N layers of lists in dict layers, we'll push in the values later but it needs the empty placeholder first
        for index_l in range(len(sheet0.row(index_r))):
                layers[index_l] = []

    # loop over the rows, skip the header row
    for index_r in range(sheet0.nrows):
        if index_r is 0:
            # skip the column headers row
            continue
        # if the combine_l2 flag was set then we don't care about matching the l2_value in the row
        if not combine_l2:
            # however, if the combine_l2 flag was NOT set then we only include rows where the l2_value matches the
            # current row l2 column, otherwise skip the row with a continue
            if not sheet0.cell_value(index_r, l2_column_index) == l2_value:
                continue

        previous_value = ''
        # loop over the columns in the row and cast returned unicode as string
        # sanitize the string, track the number of times each link occurs (link_count)
        # and push the link string into layers dict list
        for index_l, col_value in enumerate(sheet0.row(index_r)):
            # ignore L2 column
            if index_l == l2_column_index:
                continue
            # if there's an L2 column and we've passed it then we are going to offset the layers back one
            if index_l > l2_column_index and has_l2_column:
                index_l -= 1

            value = str(col_value.value)
            value = value.replace('\'', '\\\"')
            value = value.replace('\n', '')

            # skip index_l == 0, we don't have a previous value yet so there's nothing to link
            # skip N/A -> N/A, TBD -> TBD, and 0 -> 0 links, they create circular links which break the chart
            if index_l > 0 and not (re.match(na_regex, previous_value) and re.match(na_regex, value)):

                match_key = '[ ' + str(quote(previous_value)) + ', ' + str(quote(value)) + ', '
                if str(match_key) in link_count.keys():
                    link_count[match_key] += 1
                else:
                    link_count[match_key] = 1

                if match_key not in layers[index_l]:
                    layers[index_l].append(match_key)

            previous_value = value

    # save the resulting layer list with the l2_value as the key
    l2_layers[l2_value] = layers

json_output = """
                   var chart_data = {
              """
default_chart_data = 'var defaultDataArray = { '
checkbox_html = '<div id="L2_outer"> <span id="toggleInner">Click here to Show/Hide this div </span><div id="L2_inner" > '
first_l2 = True
for l2_key in l2_layers.keys():
    json_output += "\"" + l2_key + "\": {"
    checkbox_html += "<input type=checkbox class=\"selectL2 \" name=\"" + l2_key + "\" "
    if first_l2:
        default_chart_data += "\"" + l2_key + "\": {"
        checkbox_html += " checked=\"checked\" > " + l2_key + " "
    else:
        checkbox_html += " >" + l2_key + " "
    # better to control the layers by limiting what we put into layers{} but this is much simpler and it's fast anyway
    displayed_layer_count = 0
    for layer in sorted(l2_layers[l2_key].keys()):
        json_output += "\"" + str(layer) + "\": [ "
        if first_l2:
            default_chart_data += "\"" + str(layer) + "\": [ "
        displayed_layer_count += 1
        if displayed_layer_count <= num_layers:
            for match_key in l2_layers[l2_key][layer]:
                json_output += match_key + str(quote(link_count[match_key])) + ' ] \n,'
                if first_l2:
                    default_chart_data += match_key + str(quote(link_count[match_key])) + ' ] \n,'

        else:
            print('ignoring layer ' + str(layer) + '->' + str(layer + 1) + ' because num_layers is ' + str(num_layers))

        json_output = json_output.rstrip(',')
        json_output += ' ],'
        if first_l2:
            default_chart_data = default_chart_data.rstrip(',')
            default_chart_data += ' ],'

    json_output = json_output.rstrip(',')
    json_output += ' } ,'
    if first_l2:
        default_chart_data = default_chart_data.rstrip(',')
        default_chart_data += ' } ,'

    first_l2 = False


json_output = json_output.rstrip(',')
json_output += ' } ; '


# sets the height based on the number of lines we ended up with in output (only if height value not passed in)
num_lines = len(default_chart_data.splitlines())
height = args.height if args.height else int(num_lines * 10) + 100

default_chart_data = default_chart_data.rstrip(',')
default_chart_data += ' } ;'

checkbox_html += " </div> </div>"


html = """
<html>
    <head>
"""

html += """
        <script type="text/javascript"
           src="https://www.google.com/jsapi?autoload={'modules':[{'name':'visualization','version':'1.1','packages':['sankey']}]}">
        </script>
        <script src="http://code.jquery.com/jquery-1.12.0.min.js"></script>
        <script type="text/javascript" src="chart_data.js"></script>
        <script type="text/javascript" src="chart_handler.js"></script>
    """
html += """

"""
html += """

    </head>
    <body>
        <h1>
"""

html += ' Sankey Visualization <br><hr>'

html += """
    </h1>
    """
html += checkbox_html

html+= """
    <hr>
    <div id="sankey_multiple"
"""

html += ' style="width: ' + str(width) + '; height: ' + str(height) + 'px;">     </div>'

html += """

"""

html += """

</body>
<script type="text/javascript">

    var dataArr = dataToArray(defaultDataArray);
    google.setOnLoadCallback(drawChart(dataArr));

    </script>
</html>
"""

output_filename = 'Sankey_' + str(num_layers) + 'layers.html'
output_filename = output_filename.replace('\ ', '_')
output_path = os.path.join(output_dir, output_filename)

js_output_path = os.path.join(output_dir, "chart_data.js")
jsonfh = open(js_output_path, 'w')
jsonfh.write(json_output + """

""" + default_chart_data + """
 """)

jsonfh.close()

try:
    target = open(output_path, 'w')
except IOError:
    print('Could not write output to ' + output_path)
    exit('Exiting. Please resolve output path')
print('writing output to '+output_path)
target.write(html)
target.close()
