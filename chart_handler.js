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

var headerArr = [];
function dataToArray(data){
    var layers = {};
    for (l2_value in data) {
        headerArr.push(l2_value);
        for (layer in data[l2_value] ){
            layers[layer] = [];
        }
    }
    for (l2_value in data) {
        headerArr.push(l2_value);
        for (layer in data[l2_value] ){
            layers[layer].push(data[l2_value][layer]);
        }
    }
    returnArray = [];
    for (layer in layers){
        for ( keyValue in layers[layer]){
            for (row in layers[layer][keyValue] ){
                var rowValue = layers[layer][keyValue][row];
                returnArray.push(rowValue);
            }
        }
    }
    return returnArray;
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
                fontName: 'Arial',
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