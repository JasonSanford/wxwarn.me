# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'County'
        db.create_table('wxwarn_county', (
            ('id', self.gf('django.db.models.fields.CharField')(max_length=6, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('state_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('state_fips', self.gf('django.db.models.fields.CharField')(max_length=6)),
            ('county_fips', self.gf('django.db.models.fields.CharField')(max_length=6)),
            ('geometry', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('wxwarn', ['County'])

        # Adding model 'UGC'
        db.create_table('wxwarn_ugc', (
            ('id', self.gf('django.db.models.fields.CharField')(max_length=6, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=1000)),
            ('time_zone', self.gf('django.db.models.fields.CharField')(max_length=3)),
            ('fe_area', self.gf('django.db.models.fields.CharField')(max_length=3)),
            ('geometry', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('wxwarn', ['UGC'])

        # Adding model 'WeatherAlert'
        db.create_table('wxwarn_weatheralert', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('nws_id', self.gf('django.db.models.fields.CharField')(unique=True, max_length=1000)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('source_created', self.gf('django.db.models.fields.DateTimeField')()),
            ('source_updated', self.gf('django.db.models.fields.DateTimeField')()),
            ('effective', self.gf('django.db.models.fields.DateTimeField')()),
            ('expires', self.gf('django.db.models.fields.DateTimeField')()),
            ('event', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('summary', self.gf('django.db.models.fields.TextField')()),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=1028)),
            ('fips', self.gf('django.db.models.fields.TextField')()),
            ('ugc', self.gf('django.db.models.fields.TextField')()),
            ('fake', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('wxwarn', ['WeatherAlert'])

        # Adding model 'UserProfile'
        db.create_table('wxwarn_userprofile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('premium', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('sms_number', self.gf('django.db.models.fields.CharField')(max_length=50, null=True)),
            ('send_sms_alerts', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('send_email_alerts', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('wxwarn', ['UserProfile'])

        # Adding model 'LocationSource'
        db.create_table('wxwarn_locationsource', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('wxwarn', ['LocationSource'])

        # Adding model 'UserLocation'
        db.create_table('wxwarn_userlocation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['wxwarn.LocationSource'])),
            ('latitude', self.gf('django.db.models.fields.FloatField')()),
            ('longitude', self.gf('django.db.models.fields.FloatField')()),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('source_created', self.gf('django.db.models.fields.DateTimeField')()),
            ('source_data', self.gf('jsonfield.fields.JSONField')(default={})),
        ))
        db.send_create_signal('wxwarn', ['UserLocation'])

        # Adding model 'UserWeatherAlert'
        db.create_table('wxwarn_userweatheralert', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('user_location', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['wxwarn.UserLocation'])),
            ('weather_alert', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['wxwarn.WeatherAlert'])),
            ('weather_alert_ugc', self.gf('django.db.models.fields.CharField')(max_length=6)),
        ))
        db.send_create_signal('wxwarn', ['UserWeatherAlert'])


    def backwards(self, orm):
        # Deleting model 'County'
        db.delete_table('wxwarn_county')

        # Deleting model 'UGC'
        db.delete_table('wxwarn_ugc')

        # Deleting model 'WeatherAlert'
        db.delete_table('wxwarn_weatheralert')

        # Deleting model 'UserProfile'
        db.delete_table('wxwarn_userprofile')

        # Deleting model 'LocationSource'
        db.delete_table('wxwarn_locationsource')

        # Deleting model 'UserLocation'
        db.delete_table('wxwarn_userlocation')

        # Deleting model 'UserWeatherAlert'
        db.delete_table('wxwarn_userweatheralert')


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
            'url': ('django.db.models.fields.CharField', [], {'max_length': '1028'})
        }
    }

    complete_apps = ['wxwarn']