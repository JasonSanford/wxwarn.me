var map, jason;
(function() {
    var start_location = new L.LatLng(40, -100),
        road_layer = new L.TileLayer('http://{s}.tiles.mapbox.com/v3/jcsanford.map-vita0cry/{z}/{x}/{y}.png', {
                maxZoom: 16,
                subdomains: ['a', 'b', 'c', 'd'],
                attribution: 'Map data (c) <a href="http://www.openstreetmap.org/" target="_blank">OpenStreetMap</a> contributors, CC-BY-SA.'
            }),
        satellite_layer = new L.TileLayer('http://{s}.tiles.mapbox.com/v3/jcsanford.map-c487ey3y/{z}/{x}/{y}.png', {
                maxZoom: 16,
                subdomains: ['a', 'b', 'c', 'd'],
                attribution: 'Map data (c) <a href="http://www.openstreetmap.org/" target="_blank">OpenStreetMap</a> contributors, CC-BY-SA.'
            }),
        route = new L.GeoJSON(dcr.route_geojson, {
            style: function(feature) {
                switch (feature.properties.span) {
                    case 'past':
                        return {
                            color: '#00ff00',
                            opacity: 0.8
                        };
                    case 'future':
                        return {
                            color: '#ff0000'
                        };
                }
            }
        });
    jason = L.marker(L.latLng(dcr.jason.geometry.coordinates[1], dcr.jason.geometry.coordinates[0])).bindPopup('Distance: ' + dcr.jason.properties.distance + '<br>At: ' + dcr.jason.properties.time);
    map = new L.Map('map', {
        center: start_location,
        zoom: 8,
        layers: [
            road_layer
        ],
        attributionControl: false
    });

    map
        .fitBounds(route.getBounds())
        .addLayer(route)
        .addLayer(jason);
    L.control.layers({'Road': road_layer, 'Satellite': satellite_layer}, {'Jason': jason, 'Route': route}).addTo(map);
}());
