$('.map-tab').on('click', function (event) {
    var $tab = $(this),
        state = $tab.data('state');

    if (!wx.weather_alerts[state].map) {
        var road_layer = new L.TileLayer('http://{s}.tiles.mapbox.com/v3/jcsanford.map-xu5k4lii/{z}/{x}/{y}.png', {
                maxZoom: 16,
                subdomains: ['a', 'b', 'c', 'd'],
                attribution: 'Map data (c) <a href="http://www.openstreetmap.org/" target="_blank">OpenStreetMap</a> contributors, CC-BY-SA.'
            }),
        satellite_layer = new L.TileLayer('http://{s}.tiles.mapbox.com/v3/jcsanford.map-c487ey3y/{z}/{x}/{y}.png', {
                maxZoom: 16,
                subdomains: ['a', 'b', 'c', 'd'],
                attribution: 'Map data (c) <a href="http://www.openstreetmap.org/" target="_blank">OpenStreetMap</a> contributors, CC-BY-SA.'
            }),
        alerts_layer = new L.GeoJSON(null, {
            style: {
                color: '#ff0000',
                opacity: 1,
                weight: 1,
                fillColor: '#ff0000',
                fillOpacity: 0.35
            }
        });
        wx.weather_alerts[state].map = new L.Map($('#tab-' + state + '-map').find('.map-container')[0], {
            center: new L.LatLng(40, -100),
            zoom: 8,
            layers: [
                road_layer
            ]
        });
        wx.weather_alerts[state].alerts_layer = alerts_layer;
        wx.weather_alerts[state].map.addLayer(alerts_layer);
        L.control.layers({'Road': road_layer, 'Satellite': satellite_layer}, {'Alert Areas': alerts_layer}).addTo(wx.weather_alerts[state].map);
        setTimeout(function () {
            wx.weather_alerts[state].map.invalidateSize();
        }, 500);
        for (var i = 0, len = wx.weather_alerts[state].weather_alert_ids.length; i < len; i++) {
            var weather_alert_id = wx.weather_alerts[state].weather_alert_ids[i];
            $.ajax({
                url: '/weather_alerts/' + weather_alert_id + '.geojson',
                dataType: 'json',
                type: 'GET',
                success: function(data) {
                    processAlert(data, state);
                },
                error: function(xhr) {

                }
            });
        }
    }
});

function processAlert(data, state) {
    wx.weather_alerts[state].alerts_layer.addData(data);
    setTimeout(function () {
        wx.weather_alerts[state].map.fitBounds(wx.weather_alerts[state].alerts_layer.getBounds());
    }, 1000);
}