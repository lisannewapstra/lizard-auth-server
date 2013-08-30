# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'UserProfile.organisation'
        db.delete_column('lizard_auth_server_userprofile', 'organisation')


    def backwards(self, orm):
        # Adding field 'UserProfile.organisation'
        db.add_column('lizard_auth_server_userprofile', 'organisation',
                      self.gf('django.db.models.fields.CharField')(default=u'', max_length=255, null=True, blank=True),
                      keep_default=False)


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
        'lizard_auth_server.invitation': {
            'Meta': {'object_name': 'Invitation'},
            'activated_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'activation_key': ('django.db.models.fields.CharField', [], {'max_length': '64', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'activation_key_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_activated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'organisation': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'portals': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['lizard_auth_server.Portal']", 'symmetrical': 'False', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'})
        },
        'lizard_auth_server.organisation': {
            'Meta': {'object_name': 'Organisation'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'roles': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['lizard_auth_server.Role']", 'symmetrical': 'False', 'through': "orm['lizard_auth_server.OrganisationRole']", 'blank': 'True'}),
            'unique_id': ('django.db.models.fields.CharField', [], {'default': "'637f855329e446fda339936df05407a8'", 'unique': 'True', 'max_length': '32'})
        },
        'lizard_auth_server.organisationrole': {
            'Meta': {'unique_together': "((u'organisation', u'role'),)", 'object_name': 'OrganisationRole'},
            'for_all_users': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'organisation': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lizard_auth_server.Organisation']"}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lizard_auth_server.Role']"})
        },
        'lizard_auth_server.portal': {
            'Meta': {'ordering': "(u'name',)", 'object_name': 'Portal'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'redirect_url': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'sso_key': ('django.db.models.fields.CharField', [], {'default': "u'ZBuGcS0SYmPJ5HWMjvK5M7LV3IsmIOjaUifHghxiKfpgebqUQtwcxT91XPxZI24y'", 'unique': 'True', 'max_length': '64'}),
            'sso_secret': ('django.db.models.fields.CharField', [], {'default': "u'kGZjRoWdyLZqiFOQrEN7Mo2VoAPElY1NvtWb7hUk3KeIgXrC692oQGqUVzgbIBUP'", 'unique': 'True', 'max_length': '64'}),
            'visit_url': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'lizard_auth_server.role': {
            'Meta': {'unique_together': "((u'name', u'portal'),)", 'object_name': 'Role'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'external_description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'internal_description': ('django.db.models.fields.TextField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'portal': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lizard_auth_server.Portal']"}),
            'unique_id': ('django.db.models.fields.CharField', [], {'default': "'334bf3ce83914ab8839a7b7bfef9d344'", 'unique': 'True', 'max_length': '32'})
        },
        'lizard_auth_server.token': {
            'Meta': {'object_name': 'Token'},
            'auth_token': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 8, 29, 0, 0)'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'portal': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lizard_auth_server.Portal']"}),
            'request_token': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'})
        },
        'lizard_auth_server.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mobile_phone_number': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'organisations': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['lizard_auth_server.Organisation']", 'null': 'True', 'blank': 'True'}),
            'phone_number': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'portals': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['lizard_auth_server.Portal']", 'symmetrical': 'False', 'blank': 'True'}),
            'postal_code': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'roles': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['lizard_auth_server.OrganisationRole']", 'null': 'True', 'blank': 'True'}),
            'street': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'town': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'})
        }
    }

    complete_apps = ['lizard_auth_server']