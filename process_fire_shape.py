import json

from shapely.geometry import asShape

file = open('/Users/jasonsanford/Desktop/fire.geojson', 'r')

output = open('/Users/jasonsanford/code/wxwarn.me/initial_fire.json', 'w')

s = file.read()

geojson = json.loads(s)

initial_data = []

for feature in geojson['features']:
    if feature['properties']['STATE'] and feature['properties']['ZONE'] and feature['properties']['NAME'] and feature['properties']['TIME_ZONE']:
        geometry_shape = asShape(feature['geometry'])
        bounds = geometry_shape.bounds
        min_x, min_y, max_x, max_y = bounds
        bounds_polygon = {'type': 'Polygon', 'coordinates': [[
            (min_x, min_y),
            (min_x, max_y),
            (max_x, max_y),
            (max_x, min_y),
            (min_x, min_y),
        ]]}
        row = {
            'pk': '%sZ%s' % (feature['properties']['STATE'], feature['properties']['ZONE']),
            'model': 'wxwarn.fire',
            'fields': {
                'name': feature['properties']['NAME'],
                'time_zone': feature['properties']['TIME_ZONE'],
                'geometry': json.dumps(feature['geometry']),
                'geometry_bbox': json.dumps(bounds_polygon),
            }
        }
        initial_data.append(row)

final_initial_data = initial_data[:]

output.write(json.dumps(final_initial_data))
output.close()

print 'Dumped %s features' % len(final_initial_data)
