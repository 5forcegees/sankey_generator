# sankey_generator
Accepts xls input file of 2-5 columns and outputs an html document sankey chart
XLS source file must be sanitized (no weird characters, just letters and numbers) to be parsed properly

Ex:
./parse_xls_into_html_sankey.py -f ../sourcefiles/fullsource_clean.xls
