(function() {
    /*
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
    */

    $('#user-profile-update').on('click', function (event) {
        event.preventDefault();
        //alert('submit I say!');
        $.ajax({
            url: '/user_profile/',
            type: 'POST',
            data: $('#user-profile-form').serialize(),
            dataType: 'json',
            success: function (data) {
                $('#profile-update-success').slideDown();
                setTimeout(function () {
                    $('#profile-update-success').slideUp();
                }, 3000);
            },
            error: function (jqXHR) {
                var data = JSON.parse(jqXHR.responseText),
                    message = data.message;
                $('#profile-update-error').find('.message').text(message);
                $('#profile-update-error').slideDown();
                setTimeout(function () {
                    $('#profile-update-error').slideUp();
                }, 5000);
            }
        });
    });

    $('#weather-alert-update').on('click', function (event) {
        event.preventDefault();

        var params = {};

        $('.weather-alert-check').each(function (i, o) {
            var $checkbox = $(o);
            params[$checkbox.attr('name')] = {
                value: $checkbox.is(':checked')
            };
        });

        $.ajax({
            url: '/user_weather_alert_type_exclusions/',
            type: 'POST',
            data: JSON.stringify(params),
            dataType: 'json',
            success: function (data) {
                $('#weather-alert-type-update-success').slideDown();
                setTimeout(function () {
                    $('#weather-alert-type-update-success').slideUp();
                }, 3000);
            },
            error: function (jqXHR) {
                var data = JSON.parse(jqXHR.responseText),
                    message = data.message;
                $('#weather-alert-type-update-error').find('.message').text(message);
                $('#weather-alert-type-update-error').slideDown();
                setTimeout(function () {
                    $('#weather-alert-type-update-error').slideUp();
                }, 5000);
            }
        });
    });
}())