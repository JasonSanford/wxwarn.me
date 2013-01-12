(function() {
    var start_location = new L.LatLng(wx.user_location.geometry.coordinates[1], wx.user_location.geometry.coordinates[0]),
        road_layer = new L.TileLayer('http://{s}.tiles.mapbox.com/v3/jcsanford.map-xu5k4lii/{z}/{x}/{y}.png', {
                maxZoom: 16,
                subdomains: ['a', 'b', 'c', 'd'],
                attribution: 'Map data (c) <a href="http://www.openstreetmap.org/" target="_blank">OpenStreetMap</a> contributors, CC-BY-SA.'
            }),
        satellite_layer = new L.TileLayer('http://{s}.tiles.mapbox.com/v3/jcsanford.map-c487ey3y/{z}/{x}/{y}.png', {
                maxZoom: 16,
                subdomains: ['a', 'b', 'c', 'd'],
                attribution: 'Map data (c) <a href="http://www.openstreetmap.org/" target="_blank">OpenStreetMap</a> contributors, CC-BY-SA.'
            }),
        map = new L.Map('map', {
            center: start_location,
            zoom: 15,
            layers: [
                road_layer
            ]
        }),
        alert_layer = new L.GeoJSON(wx.weather_alert, {
            filter: function(feature, layer) {
                return feature.id === wx.weather_alert_location_id;
            },
            style: {
                color: '#ff0000',
                opacity: 1,
                weight: 1,
                fillColor: '#ff0000',
                fillOpacity: 0.35,
                clickable: false
            }
        }),
        start_marker = L.marker(start_location);
    map
        .fitBounds(alert_layer.getBounds())
        .addLayer(alert_layer)
        .addLayer(start_marker);
    L.control.layers({'Road': road_layer, 'Satellite': satellite_layer}, {'User Location': start_marker, 'Alert Area': alert_layer}).addTo(map);
}())