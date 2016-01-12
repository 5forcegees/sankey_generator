#!/usr/bin/python
from csv import reader, QUOTE_NONE
from argparse import ArgumentParser
import re

parser = ArgumentParser(description="produces a sankey chart html doc based on a provided csv")
parser.add_argument("-f", "--filename", type=str, help="the path to the csv source file")
parser.add_argument("-w", "--width",type=int, help="the desired chart width" )
parser.add_argument("-hi", "--height",type=int, help="the desired chart height" )
#will only accept 2-5 layers
parser.add_argument("-n", "--num_layers",type=int, help="the desired number of layers",  choices=range(2,6) )

args = parser.parse_args()
filename = args.filename
width = args.width if args.width else 1400
height = args.height if args.width else 10000
num_layers = args.num_layers if args.num_layers else 6 

# defs
def quote(foo):
    if type(foo) is int:
        return(foo)
    elif type(foo) is str:
        return('\''+ foo +' \'')
    else:
	print(str(foo) + ' is a ' + str(type(foo)))
	exit("def quote got passed a thing that was not a string or int")

print('using file \'' + filename + '\' as sourcefile')

# script body
try:
    reader = reader(open(filename, 'rU'), delimiter='|', dialect='excel-tab', quoting=QUOTE_NONE)
except IOError:
    print('Could not read file: ' + filename )
    help_and_exit()

#link_count carries the number of times each link exists, will be used for weight in the chart
link_count = {}

# the key for the layers dict is just the sankey layer number
# the value for each layer is a list of the strings we'll use to build the html
# the list preserves the order of appended items, which is needed for correct chart display
layers = {}
quote_regex = re.compile('^[\'\"]')
na_regex = re.compile('N\/A|\#N\/A|0')

#this is kind of a heavy handed way to do this but 
# since we know the patterns of the first and second rows...
layer1_regex = re.compile('^SC')
layer2_regex = re.compile('^\d{3}')
match_all_regex = re.compile('.*')

for index_r, content_line in enumerate(reader):
    if index_r is 0:
        #skip the column headers row
        continue
    for index_cl, line in enumerate(content_line):
        previous_value = ''
	#make N layers of lists in dict layers
        for index_l, value in enumerate(line.split(',')):
	    if index_l >= len(layers):
                layers[index_l] = []
	
	#split up the line, increment the link_count and save the links in layer
        for index_l, value in enumerate(line.split(',')):
	    if index_l == 1:
	        loop_regex = layer1_regex
	    elif index_l == 2:
	        loop_regex = layer2_regex
	    else:
	        loop_regex = match_all_regex

	    # skip index_l == 0, we don't have a previous value yet so there's nothing to link
            # skip N/A, 0, ', " , etc.  they create circular links or otherwise throw off layers
	    if index_l > 0 \
		    and not (re.match(na_regex, previous_value) or re.match(na_regex, value) ) \
		    and not (re.match(quote_regex, previous_value)) \
		    and not (previous_value == 'TBD' and value == 'TBD' ) \
	            and ( re.match(loop_regex, previous_value ) ):

	        match_key = '[ ' + quote(previous_value) + ', ' + quote(value) + ', ' 
	        if str(match_key) in link_count.keys():
                    link_count[match_key] += 1
                else:
                    link_count[match_key] = 1

                if match_key not in layers[index_l]:
                    layers[index_l].append(match_key)

            previous_value = value

output = '    data.addRows( [ '
#better to control the layers by limiting what we put into layers{} but this is much simpler 
displayed_layer_count = 0
for layer in sorted(layers.keys()):
    displayed_layer_count += 1
    if displayed_layer_count <= num_layers :
        for match_key in layers[layer]:
            output += match_key + str(quote(link_count[match_key])) + ' ] \n,'
    else:
	print('ignoring layer '+ str(layer) + '->' +str(layer + 1) + ' because num_layers is ' + str(num_layers) )

output = output.rstrip(',')	
output += ' ] );'

tf1 = open('html/top1.html', 'r')
top1 = tf1.read()
tf1.close()

tf2 = open('html/top2.html', 'r')
top2 = tf2.read()
tf2.close()

top = top1 + ' style="width: '+ str(width) +'px; height: '+ str(height) +'px;"> ' + top2

bf = open('html/bottom.html', 'r')
bottom = bf.read()
bf.close()

filename_no_extension = filename.split('.')
target = open('sankey_chart_'+filename_no_extension[0]+'_'+str(num_layers)+'layers.html', 'w')
print('writing output to sankey_chart_'+filename_no_extension[0]+'_'+str(num_layers)+'layers.html')
target.write(top + output + bottom)
target.close()

