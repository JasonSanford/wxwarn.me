(function() {
    var start_location = new L.LatLng(37.92686760148135, -96.767578125)
    L.map('map', {
        center: start_location,
        zoom: 15,
        layers: [
            new L.TileLayer('http://{s}.tiles.mapbox.com/v3/jcsanford.map-xu5k4lii/{z}/{x}/{y}.png', {
                maxZoom: 16,
                subdomains: ['a', 'b', 'c', 'd'],
                attribution: 'Tiles Courtesy of <a href="http://www.mapbox.com/" target="_blank">MapBox</a>. Map data (c) <a href="http://www.openstreetmap.org/" target="_blank">OpenStreetMap</a> contributors, CC-BY-SA.'
            })
        ]
    }).addLayer(L.marker(start_location));
}())