(function() {
    function onEachFeature(feature, layer) {
        if (feature.properties) {
            var created_date = new Date(feature.properties.created),
                updated_date = new Date(feature.properties.updated),
                created_date_pretty = created_date.toLocaleString(),
                updated_date_pretty = updated_date.toLocaleString();
            infos = [];
            infos.push('First located here: ' + created_date_pretty);
            infos.push('Last found here: ' + updated_date_pretty);
            layer.bindPopup(infos.join('<br>'));
        }
    }

    var start_location = new L.LatLng(wx.user.last_location.geometry.coordinates[1], wx.user.last_location.geometry.coordinates[0]),
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
        last_location_layer = new L.GeoJSON(wx.user.last_location, {
            onEachFeature: onEachFeature
        }),
        last_locations_layer = new L.GeoJSON(wx.user.last_locations, {
            onEachFeature: onEachFeature
        }),
        map = new L.Map('map', {
            center: start_location,
            zoom: 15,
            layers: [
                road_layer,
                last_location_layer
            ]
        });

    L.control.layers({'Road': road_layer, 'Satellite': satellite_layer}, {'Last Location': last_location_layer, 'Last Day Locations': last_locations_layer}).addTo(map);
}());
