from django import template
register = template.Library()


@register.simple_tag
def user_weather_alert_thumbnail(user_weather_alert, width=100, height=100, zoom=10):
    return user_weather_alert.static_map_url(width=width, height=height, zoom=zoom)
