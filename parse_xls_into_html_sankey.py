#!/usr/bin/python
import re
from argparse import ArgumentParser
from xlrd import open_workbook
import string
import os.path

parser = ArgumentParser(description="produces a sankey chart html doc based on a provided xls")
parser.add_argument("-f", "--filename", type=str, help="the path to the xls source file")
parser.add_argument("-w", "--width", type=int, help="the desired chart width", default=1400)
parser.add_argument("-hi", "--height", type=int, help='the desired chart height.  Will try to set intelligent \
                                                        height based on number of links if none is passed in')
# will only accept 2-5 layers
parser.add_argument("-n", "--num_layers", type=int, help="the desired number of layers", choices=range(2, 6), default=4)

args = parser.parse_args()
filename = args.filename
width = args.width
height = args.height
num_layers = args.num_layers if args.num_layers else 6

# defs
def quote(foo):
    if isinstance(foo, int):
        return (foo)
    elif isinstance(foo, str) or isinstance(foo, unicode):
        return '\'' + foo + ' \''
    else:
        print(str(foo) + ' is a ' + str(type(foo)))
        exit("def quote got passed a thing that was not a string or int")

print('\nUsing file \'' + filename + '\' as sourcefile')

try:
    book = open_workbook(filename)
except IOError:
    print('Could not read file: ' + filename)
    exit()

# link_count carries the number of times each link exists, will be used for weight in the chart
link_count = {}

# the key for the layers dict is just the sankey layer number
# the value for each layer is a list of the strings we'll use to build the html
# the list preserves the order of appended items, which is needed for correct chart display
layers = {}

na_regex = re.compile('N\/A|TBD|0')

errors_found = 0
# check for errors in importing the data
for sheet in book.sheets():
    for index_r in range(sheet.nrows):
        for index_col, type in enumerate(sheet.row_types(index_r)):
            if type == 5:
                print('')
                print('There was an error in importing row: ' + str(index_r + 1))
                print('Please take out weird characters (ex: \'#\') in column: ' + string.uppercase[index_col])
                print('Imported values were: ' + str(sheet.row_slice(index_r)))
                errors_found += 1
if errors_found:
    exit('\nExiting application.\nSee error text above for details')

for sheet in book.sheets():
    for index_r in range(sheet.nrows):

        # make N layers of lists in dict layers, we'll push in the values later but it needs the empty placeholder first
        for index_l in range(len(sheet.row(index_r))):
            layers[index_l] = []

    # loop over the rows, skip the header row
    for index_r in range(sheet.nrows):
        if index_r is 0:
            # skip the column headers row
            continue

        previous_value = ''
        # loop over the columns in the row and cast returned unicode as string
        # sanitize the string, track the number of times each link occurs (link_count)
        # and push the link string into layers dict list
        for index_l, col_value in enumerate(sheet.row(index_r)):
            value = str(col_value.value)
            value = value.replace('\'', '\\\'')
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

output = '    data.addRows( [ '
# better to control the layers by limiting what we put into layers{} but this is much simpler and it's fast anyway
displayed_layer_count = 0
for layer in sorted(layers.keys()):
    displayed_layer_count += 1
    if displayed_layer_count <= num_layers:
        for match_key in layers[layer]:
            output += match_key + str(quote(link_count[match_key])) + ' ] \n,'
    else:
        print('ignoring layer ' + str(layer) + '->' + str(layer + 1) + ' because num_layers is ' + str(num_layers))

output = output.rstrip(',')
output += ' ] );'

# sets the height based on the number of lines we ended up with in output (only if height value not passed in)
num_lines = len(output.splitlines())
height = height if height else int(num_lines * 10)

# html fragments for output file
html = """
<html>
<body>
<script type="text/javascript"
           src="https://www.google.com/jsapi?autoload={'modules':[{'name':'visualization','version':'1.1','packages':['sankey']}]}">
</script>

<div id="sankey_multiple"
"""

html += ' style="width: ' + str(width) + 'px; height: ' + str(height) + 'px;"> '

html += """
</div>
<script type="text/javascript">
google.setOnLoadCallback(drawChart);
   function drawChart() {
    var data = new google.visualization.DataTable();
    data.addColumn('string', 'From');
    data.addColumn('string', 'To');
    data.addColumn('number', 'Weight');
"""
html += output
html += """

    // Set chart options
    var options = {
        sankey: {
	    link: {
		colorMode: 'source',
		color: {
		    stroke: 'lightgray',
		    strokeWidth: 1
	        },
	    },
	    node: {
	        interactivity: true,
		width: 15,
		label: {
		      fontName: 'Arial',
		      fontSize: 12,
		      bold: true,
		    },
	   }
	}
    };

    // Instantiate and draw our chart, passing in some options.
    var chart = new google.visualization.Sankey(document.getElementById('sankey_multiple'));
    chart.draw(data, options);
   }
</script>
</body>
</html>
"""

# parse up the filename so it displays properly in the output file name
head, tail = os.path.split(filename)
tail = tail.split('.')[0]

target = open('sankey_chart_' + tail + '_' + str(num_layers) + 'layers.html', 'w')
print('writing output to sankey_chart_' + tail + '_' + str(num_layers) + 'layers.html')
target.write(html)
target.close()
