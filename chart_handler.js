function updateChart(){
    var selected = [];
    var rawData = {};
    $('input:checked').each(function() {
        selected.push($(this).attr('name'));
    });
    for (chartKey in selected){
        rawData[selected[chartKey]] = chart_data[selected[chartKey]];
    }
    var dataToDraw = dataToArray(rawData);
    drawChart(dataToDraw);
}

$( document ).ready( function(){

    $("#toggleInner").click( function(){
       $("#L2_inner").toggle();
    });

    $(".selectL2").click(function(){
        updateChart();
    });


});

function updateHeight(px){
    $("#sankey_multiple").height(px);
}

var headerArr = [];
var foundMatch = false;
var replaceIndex = -1;
function dataToArray(data){
    var matchCounts = {};
    var layers = {};

    for (l2_value in data) {
        headerArr.push(l2_value);
        for (layer in data[l2_value] ){
            layers[layer] = [];
        }
    }
    for (l2_value in data) {
        headerArr.push(l2_value);
        rawLink = '';
        for (layer in data[l2_value] ){
            layers[layer].push(data[l2_value][layer]);
        }
    }

    var returnArray = [];
    var rowValue = [];
    replaceIndex = -1;
    for (layer in layers){
        //console.log("layer: " + layer);
        for ( keyValue in layers[layer]){
            //console.log("keyValue: "+keyValue)
            replaceIndex = -1;
            for (row in layers[layer][keyValue] ){
                foundMatch = false;
                rowValue = setWeight(layers[layer][keyValue][row], returnArray);
                //console.log("got returned rowValue: " + rowValue );
                if (foundMatch){
                    console.log("splicing row: " + returnArray[replaceIndex] + " and pushing row row " + rowValue);
                    var spliced = returnArray.splice(replaceIndex, 1, rowValue);
                    console.log("spliced: " + spliced);

                }else{
                    returnArray.push(layers[layer][keyValue][row]);
                }
            }
        }
    }
    var height = returnArray.length * 10;
    updateHeight(height);
    return returnArray;
}

function setWeight(row, returnArray){
    var rawRow = row.toString();
    var parsedRow = rawRow.split(',');
    //console.log(rawRow);
    if (returnArray.length > 0 ){
        for (returnArrayIndex in returnArray){
            var str = returnArray[returnArrayIndex];
            var rawReturnArray = str.toString();
            var parsedReturnArray = rawReturnArray.split(',');
            if (parsedReturnArray[0] == parsedRow[0] && parsedReturnArray[1] == parsedRow[1]){
                var updatedRow = [];
                updatedRow[0] = parsedRow[0];
                updatedRow[1] = parsedRow[1];
                updatedRow[2] = +parsedRow[2] + +parsedReturnArray[2];
                console.log( "returning updatedRow: " + updatedRow );
                foundMatch = true;
                replaceIndex = returnArrayIndex;
                return updatedRow;
            }
        }
        return row;
    }else{
        return row;
    }
}

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