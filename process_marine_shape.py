import os
import json

file = open('/Users/jasonsanford/Desktop/marine.geojson', 'r')

output = open('/Users/jasonsanford/code/wxwarn.me/wxwarn/fixtures/initial_marine.json', 'w')

s = file.read()

geojson = json.loads(s)

initial_data = []

for feature in geojson['features']:
    row = {
        'pk': feature['properties']['ID'],
        'model': 'wxwarn.marine',
        'fields': {
            'name': feature['properties']['NAME'],
            'wfo': feature['properties']['WFO'],
            'geometry': json.dumps(feature['geometry'])
        }
    }
    initial_data.append(row)

final_initial_data = initial_data[:]

output.write(json.dumps(final_initial_data))
output.close()

print 'Dumped %s features' % len(final_initial_data)