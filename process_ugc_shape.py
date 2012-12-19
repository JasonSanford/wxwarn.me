import os
import json

file = open('/Users/jasonsanford/Desktop/ugc.geojson', 'r')

output = open('/Users/jasonsanford/code/wxwarn.me/wxwarn/fixtures/initial_ugc.json', 'w')

s = file.read()

geojson = json.loads(s)

initial_data = []

for feature in geojson['features']:
    if feature['properties']['STATE'] and feature['properties']['ZONE'] and feature['properties']['NAME'] and feature['properties']['TIME_ZONE']:
        row = {
            'pk': '%sZ%s' % (feature['properties']['STATE'], feature['properties']['ZONE']),
            'model': 'wxwarn.ugc',
            'fields': {
                'name': feature['properties']['NAME'],
                'time_zone': feature['properties']['TIME_ZONE'],
                'geometry': json.dumps(feature['geometry'])
            }
        }
        initial_data.append(row)

final_initial_data = initial_data[:]

output.write(json.dumps(final_initial_data))
output.close()

print 'Dumped %s features' % len(final_initial_data)