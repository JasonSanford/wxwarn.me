(function() {
    var start_location = wx.user.last_location ? new L.LatLng(wx.user.last_location.coordinates[1], wx.user.last_location.coordinates[0]) : new L.LatLng(37.92686760148135, -96.767578125),
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
        });

    L.control.layers({'Road': road_layer, 'Satellite': satellite_layer}, null).addTo(map)
    L.marker(start_location).addTo(map);
}())