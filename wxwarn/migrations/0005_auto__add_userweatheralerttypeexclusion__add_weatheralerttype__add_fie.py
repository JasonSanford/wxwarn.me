# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'UserWeatherAlertTypeExclusion'
        db.create_table('wxwarn_userweatheralerttypeexclusion', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('weather_alert_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['wxwarn.WeatherAlertType'])),
        ))
        db.send_create_signal('wxwarn', ['UserWeatherAlertTypeExclusion'])

        # Adding model 'WeatherAlertType'
        db.create_table('wxwarn_weatheralerttype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('wxwarn', ['WeatherAlertType'])

        # Adding field 'WeatherAlert.weather_alert_type'
        db.add_column('wxwarn_weatheralert', 'weather_alert_type',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['wxwarn.WeatherAlertType']),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting model 'UserWeatherAlertTypeExclusion'
        db.delete_table('wxwarn_userweatheralerttypeexclusion')

        # Deleting model 'WeatherAlertType'
        db.delete_table('wxwarn_weatheralerttype')

        # Deleting field 'WeatherAlert.weather_alert_type'
        db.delete_column('wxwarn_weatheralert', 'weather_alert_type_id')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'wxwarn.county': {
            'Meta': {'object_name': 'County'},
            'county_fips': ('django.db.models.fields.CharField', [], {'max_length': '6'}),
            'geometry': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '6', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'state_fips': ('django.db.models.fields.CharField', [], {'max_length': '6'}),
            'state_name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'wxwarn.locationsource': {
            'Meta': {'object_name': 'LocationSource'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'wxwarn.state': {
            'Meta': {'object_name': 'State'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'wxwarn.timezone': {
            'Meta': {'object_name': 'Timezone'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'wxwarn.ugc': {
            'Meta': {'object_name': 'UGC'},
            'fe_area': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'geometry': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '6', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'time_zone': ('django.db.models.fields.CharField', [], {'max_length': '3'})
        },
        'wxwarn.userlocation': {
            'Meta': {'object_name': 'UserLocation'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latitude': ('django.db.models.fields.FloatField', [], {}),
            'longitude': ('django.db.models.fields.FloatField', [], {}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wxwarn.LocationSource']"}),
            'source_created': ('django.db.models.fields.DateTimeField', [], {}),
            'source_data': ('jsonfield.fields.JSONField', [], {'default': '{}'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'wxwarn.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'premium': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'send_email_alerts': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'send_sms_alerts': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'sms_number': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'timezone': ('django.db.models.fields.related.ForeignKey', [], {'default': '18', 'to': "orm['wxwarn.Timezone']"}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'wxwarn.userweatheralert': {
            'Meta': {'object_name': 'UserWeatherAlert'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'user_location': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wxwarn.UserLocation']"}),
            'weather_alert': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wxwarn.WeatherAlert']"}),
            'weather_alert_ugc': ('django.db.models.fields.CharField', [], {'max_length': '6'})
        },
        'wxwarn.userweatheralerttypeexclusion': {
            'Meta': {'object_name': 'UserWeatherAlertTypeExclusion'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'weather_alert_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wxwarn.WeatherAlertType']"})
        },
        'wxwarn.weatheralert': {
            'Meta': {'object_name': 'WeatherAlert'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'effective': ('django.db.models.fields.DateTimeField', [], {}),
            'event': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'expires': ('django.db.models.fields.DateTimeField', [], {}),
            'fake': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'fips': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nws_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '1000'}),
            'source_created': ('django.db.models.fields.DateTimeField', [], {}),
            'source_updated': ('django.db.models.fields.DateTimeField', [], {}),
            'summary': ('django.db.models.fields.TextField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'ugc': ('django.db.models.fields.TextField', [], {}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '1028'}),
            'weather_alert_type': ('django.db.models.fields.related.ForeignKey', [], {'default': '1', 'to': "orm['wxwarn.WeatherAlertType']"})
        },
        'wxwarn.weatheralerttype': {
            'Meta': {'object_name': 'WeatherAlertType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['wxwarn']