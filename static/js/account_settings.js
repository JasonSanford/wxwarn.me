(function () {

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