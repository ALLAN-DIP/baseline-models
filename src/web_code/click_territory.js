function updateMap(newMapPath){
    var oldMap = document.getElementById('map-object');
    oldMap.data = newMapPath;
    console.log(oldMap);
}

document.getElementById('map-object').addEventListener('load', function() {
    var svgMap = this.contentDocument;
    var map = this;

    var territories = svgMap.querySelectorAll('path');
    console.log(map)
    
    if (territories.length > 0) {
        console.log(`Paths found: ${territories.length}`);
        territories.forEach(territory => {
            territory.addEventListener('click', function(event) {
                // var clickedPathId = event.target.className.baseVal; // For power name
                var clickedPathId = event.target.id;
                document.getElementById('output').textContent = `Currently selected territory: ${clickedPathId}`;

                updateMap("../output/output_0_S1901M.svg")
            });
        });
    } else {
        console.error('No paths found :(');
    }
});