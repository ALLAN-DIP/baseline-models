function unitUpdate(unitTag) {
    let svgMap = document.getElementById('map-svg');
    let gNodes = Array.from(svgMap.querySelectorAll('g'));
    let textNodes = Array.from(svgMap.querySelectorAll('text'));

    // Get unit layer and current phase nodes
    let units = gNodes.find(node => {
        return node.getAttribute('id') == 'UnitLayer';
    })
    let text = textNodes.find(node => {
        return node.getAttribute('id') == 'CurrentPhase';
    })
    unitNodes = Array.from(units.querySelectorAll('use'));

    // Find specific unit
    let unitName = unitTag.toUpperCase();
    let unitId = `unit${unitName}`;

    unit = unitNodes.find(node => {
        return node.getAttribute('id').slice(0, 8) == unitId;
    })
    if (unit) {
        let symbol = (unit.getAttribute('xlink:href') == '#Fleet') ? 'F' : 'A';
        document.getElementById('output').textContent = `Currently selected unit: ${symbol}${unitName}`;
    }
    else{
        document.getElementById('output').textContent = `Currently selected territory: ${unitTag}`;
    }
    
}

document.getElementById('map-svg').addEventListener('load', function() {
    let svgMap = this;
    console.log(svgMap);
    let territories = svgMap.querySelectorAll('path');
    
    // Create event listeners for each territory in case clicked
    if (territories.length > 0) {
        territories.forEach(territory => {
            territory.addEventListener('click', function(event) {
                // let clickedPathId = event.target.className.baseVal; // For power name
                let clickedPathId = event.target.id;
                unitUpdate(clickedPathId);
            });
        });
    } else {
        console.error('No paths found :(');
    }
});