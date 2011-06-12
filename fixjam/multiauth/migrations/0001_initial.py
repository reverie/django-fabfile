# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'FacebookUser'
        db.create_table('multiauth_facebookuser', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('notes', self.gf('django.db.models.fields.TextField')()),
            ('data_cache', self.gf('picklefield.fields.PickledObjectField')(null=True)),
            ('remote_id', self.gf('django.db.models.fields.BigIntegerField')(unique=True)),
            ('user_info', self.gf('picklefield.fields.PickledObjectField')(null=True)),
        ))
        db.send_create_signal('multiauth', ['FacebookUser'])

        # Adding model 'TwitterUser'
        db.create_table('multiauth_twitteruser', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('notes', self.gf('django.db.models.fields.TextField')()),
            ('data_cache', self.gf('picklefield.fields.PickledObjectField')(null=True)),
            ('screen_name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=20)),
            ('oauth_token', self.gf('django.db.models.fields.TextField')()),
            ('oauth_secret', self.gf('django.db.models.fields.TextField')()),
            ('user_info', self.gf('picklefield.fields.PickledObjectField')(null=True)),
        ))
        db.send_create_signal('multiauth', ['TwitterUser'])

        # Adding model 'MultiUser'
        db.create_table('multiauth_multiuser', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('notes', self.gf('django.db.models.fields.TextField')()),
            ('auth_user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], unique=True, null=True)),
            ('fb_user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['multiauth.FacebookUser'], unique=True, null=True)),
            ('twitter_user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['multiauth.TwitterUser'], unique=True, null=True)),
            ('location', self.gf('picklefield.fields.PickledObjectField')(null=True)),
            ('is_banned', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('admin_notes', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
        ))
        db.send_create_signal('multiauth', ['MultiUser'])

        # Adding model 'Location'
        db.create_table('multiauth_location', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('notes', self.gf('django.db.models.fields.TextField')()),
            ('name', self.gf('django.db.models.fields.TextField')(db_index=True)),
            ('lat', self.gf('django.db.models.fields.FloatField')()),
            ('long', self.gf('django.db.models.fields.FloatField')()),
            ('fb_location_id', self.gf('django.db.models.fields.BigIntegerField')(unique=True, null=True)),
        ))
        db.send_create_signal('multiauth', ['Location'])


    def backwards(self, orm):
        
        # Deleting model 'FacebookUser'
        db.delete_table('multiauth_facebookuser')

        # Deleting model 'TwitterUser'
        db.delete_table('multiauth_twitteruser')

        # Deleting model 'MultiUser'
        db.delete_table('multiauth_multiuser')

        # Deleting model 'Location'
        db.delete_table('multiauth_location')


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
        'multiauth.facebookuser': {
            'Meta': {'object_name': 'FacebookUser'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data_cache': ('picklefield.fields.PickledObjectField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {}),
            'remote_id': ('django.db.models.fields.BigIntegerField', [], {'unique': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user_info': ('picklefield.fields.PickledObjectField', [], {'null': 'True'})
        },
        'multiauth.location': {
            'Meta': {'object_name': 'Location'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'fb_location_id': ('django.db.models.fields.BigIntegerField', [], {'unique': 'True', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lat': ('django.db.models.fields.FloatField', [], {}),
            'long': ('django.db.models.fields.FloatField', [], {}),
            'name': ('django.db.models.fields.TextField', [], {'db_index': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'multiauth.multiuser': {
            'Meta': {'object_name': 'MultiUser'},
            'admin_notes': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'auth_user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True', 'null': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'fb_user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['multiauth.FacebookUser']", 'unique': 'True', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_banned': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'location': ('picklefield.fields.PickledObjectField', [], {'null': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {}),
            'twitter_user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['multiauth.TwitterUser']", 'unique': 'True', 'null': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'multiauth.twitteruser': {
            'Meta': {'object_name': 'TwitterUser'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data_cache': ('picklefield.fields.PickledObjectField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {}),
            'oauth_secret': ('django.db.models.fields.TextField', [], {}),
            'oauth_token': ('django.db.models.fields.TextField', [], {}),
            'screen_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user_info': ('picklefield.fields.PickledObjectField', [], {'null': 'True'})
        }
    }

    complete_apps = ['multiauth']
