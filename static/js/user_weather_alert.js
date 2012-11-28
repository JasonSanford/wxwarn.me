(function() {
    var start_location = new L.LatLng(wx.user_location.coordinates[1], wx.user_location.coordinates[0]),
        map = new L.Map('map', {
            center: start_location,
            zoom: 15,
            layers: [
                new L.TileLayer('http://{s}.tiles.mapbox.com/v3/jcsanford.map-xu5k4lii/{z}/{x}/{y}.png', {
                    maxZoom: 16,
                    subdomains: ['a', 'b', 'c', 'd'],
                    attribution: 'Tiles Courtesy of <a href="http://www.mapbox.com/" target="_blank">MapBox</a>. Map data (c) <a href="http://www.openstreetmap.org/" target="_blank">OpenStreetMap</a> contributors, CC-BY-SA.'
                })
            ]
        }),
        alert_layer = new L.GeoJSON(wx.weather_alert, {
            filter: function(feature, layer) {
                return feature.id === wx.weather_alert_fips;
            }
        });
    map
        .fitBounds(alert_layer.getBounds())
        .addLayer(alert_layer)
        .addLayer(L.marker(start_location));
}())