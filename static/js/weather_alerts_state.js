wx.default_style = {
    color: '#ff0000',
    opacity: 1,
    weight: 1,
    fillColor: '#ff0000',
    fillOpacity: 0.35
};

wx.highlight_style = {
    color: '#0000ff',
    opacity: 1,
    weight: 1,
    fillColor: '#0000ff',
    fillOpacity: 0.35
};


$(document).ready(function (event) {

    var road_layer = new L.TileLayer('http://{s}.tiles.mapbox.com/v3/jcsanford.map-vita0cry/{z}/{x}/{y}.png', {
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
        style: $.extend({}, wx.default_style)
    });
    wx.weather_alerts.map = new L.Map('map-container', {
        center: new L.LatLng(40, -100),
        zoom: 8,
        layers: [
            road_layer
        ]
    });
    wx.weather_alerts.alerts_layer = alerts_layer;
    wx.weather_alerts.map.addLayer(alerts_layer);
    L.control.layers({'Road': road_layer, 'Satellite': satellite_layer}, {'Alert Areas': alerts_layer}).addTo(wx.weather_alerts.map);
    for (key in wx.weather_alerts.alerts) {
        wx.weather_alerts.alerts_layer.addData(wx.weather_alerts.alerts[key].geojson);
    }
    wx.weather_alerts.map.fitBounds(wx.weather_alerts.alerts_layer.getBounds());

    $('.weather-alert').hover(
        function () {
            var $li = $(this),
                alert_id = $li.data('alert-id');
            setStyle(alert_id, true);
        },
        function () {
            var $li = $(this),
                alert_id = $li.data('alert-id');
            setStyle(alert_id, false);
        }
    );
});

function setStyle(alert_id, highlight) {
    var location_ids = wx.weather_alerts.alerts[alert_id].location_ids.split(' ');
    wx.weather_alerts.alerts_layer.eachLayer(function(layer) {
        if (location_ids.indexOf(layer.feature.id) > -1) {
            layer.setStyle($.extend({}, highlight ? wx.highlight_style : wx.default_style));
        }
    });
}
