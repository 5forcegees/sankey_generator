
// some jquery to:
// show/hide the checkboxes
// trigger the chartUpdate
$( document ).ready( function(){
    $(".selectL2").click(function(){
        updateChart();
    });

});

//update the height of the chart div to account for the changed number of links
function updateHeight(px){
    $("#sankey_multiple").height(px);
}

function clearAllChecks() {
     $('input:checkbox').removeAttr('checked');
     updateChart();
}

// whenever one of the L2 checkboxes on the page is clicked, collect the list of selected checkboxes,
//     get the associated data sets out of chart_data
//     flatten the different sets of L2 links into an array of arrays while maintaining layer order
//     aggregate the weight of links that are duplicated for more than one L2 value
//     redraw the chart with the new set of links
function updateChart(){
    var selected = [];
    var rawData = {};
    $('input:checked').each(function() {
        selected.push($(this).attr('name'));
    });
    if (selected.length == 0) {
        drawChart([]);
        $('#introText').show();
    }else{
        $('#introText').hide();
        for (chartKey in selected){
            rawData[selected[chartKey]] = chart_data[selected[chartKey]];
        }
    }
    var dataToDraw = dataToArray(rawData);
    drawChart(dataToDraw);
}

var foundMatch = false;
var replaceIndex = -1;
// take the nested chart_data data set { L2_values: { layer_numbers: [ array of links ]}}
// flatten to returnArray [array of links] while maintaining layer order (i.e all the different layer_numbers 0, 1, 2...
//     are flattened into array with all layer 0 first, then all layer 1, then all layer 2, etc )
// each link will only occur once in the returnArray.  duplicated links will have the weights aggregated
function dataToArray(data){
    var returnArray = [];
    var rowValue = [];
    for (l2_value in data) {
        for (layer in data[l2_value] ){
            for (rowIndex in data[l2_value][layer]){
                foundMatch = false;
                replaceIndex = -1;
                rowValue = setWeight(data[l2_value][layer][rowIndex], returnArray);

                if (foundMatch){
                    //replace the matched link with the link containing the updated weight
                    var spliced = returnArray.splice(replaceIndex, 1, rowValue);
                }else{
                    //the link is not in the chart display data, put it in as-is
                    returnArray.push(data[l2_value][layer][rowIndex]);
                }
            }
        }
    }
    // now that we know the number of links we're going to draw, update the chart height
    var height = returnArray.length * 10;
    updateHeight(height);

    return returnArray;
}

// take the link to be inserted and the flattened returnArray
// if the row is already in returnArray, aggregate the weights and return the updated link
// if the row is not in returnArray, just return the link
function setWeight(row, returnArray){
    var rawRow = row.toString();
    var parsedRow = rawRow.split(',');
    if (returnArray.length > 0 ){
        for (returnArrayIndex in returnArray){
            var str = returnArray[returnArrayIndex];
            var rawReturnArray = str.toString();
            var parsedReturnArray = rawReturnArray.split(',');
            if (parsedReturnArray[0] == parsedRow[0] && parsedReturnArray[1] == parsedRow[1]){
                // the passed in link is already in the returnArray, aggregate the weights
                var updatedWeight = +parsedRow[2] + +parsedReturnArray[2];

                // set the index to be replaced, set the foundMatch bool to drive the link splice in dataToArray
                replaceIndex = returnArrayIndex;
                foundMatch = true;

                // and return the link with the aggregated weight
                var updatedRow = [parsedRow[0], parsedRow[1], updatedWeight ];
                return updatedRow;
            }
        }
        // the row isn't anywhere in returnArray, return it as-is for insertion
        return row;
    }else{
        // returnArray doesn't have any entries yet so there's nothing to check.  just return the row
        return row;
    }
}

// set up the chart columns and options, pass it the div and data, then draw the chart
// height and width of chart are set based on the div height and width
function drawChart(dataElements) {
    var data = new google.visualization.DataTable();
    data.addColumn('string', 'From');
    data.addColumn('string', 'To');
    data.addColumn('number', 'Weight');
    data.addRows( dataElements );

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
                fontName: 'PT Sans, Arial',
                fontSize: 12,
                bold: true,
                },
            }
        }
    };

    // Instantiate and draw our chart, passing in some options.
    var chart = new google.visualization.Sankey(document.getElementById('sankey_multiple'));

    window.chart = chart;
    window.data = data;
    chart.draw(data, options);
}

google.setOnLoadCallback(drawChart(dataToArray(defaultDataArray)));