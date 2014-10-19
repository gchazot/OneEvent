# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Message'
        db.create_table(u'OneEvent_message', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('sender', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('category', self.gf('django.db.models.fields.CharField')(max_length=8)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('text', self.gf('django.db.models.fields.TextField')(max_length=2048)),
            ('thread_head', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='thread', null=True, to=orm['OneEvent.Message'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'OneEvent', ['Message'])


    def backwards(self, orm):
        # Deleting model 'Message'
        db.delete_table(u'OneEvent_message')


    models = {
        u'OneEvent.event': {
            'Meta': {'object_name': 'Event'},
            'booking_close': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'choices_close': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'contractors_groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'contractors_for_event+'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            'employees_groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'employees_for_event+'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            'end': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location_address': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'location_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'organisers': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.User']", 'symmetrical': 'False', 'blank': 'True'}),
            'price_currency': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'price_for_contractors': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '6', 'decimal_places': '2'}),
            'price_for_employees': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '6', 'decimal_places': '2'}),
            'start': ('django.db.models.fields.DateTimeField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'})
        },
        u'OneEvent.eventchoice': {
            'Meta': {'unique_together': "(('event', 'title'),)", 'object_name': 'EventChoice'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'choices'", 'to': u"orm['OneEvent.Event']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        u'OneEvent.eventchoiceoption': {
            'Meta': {'unique_together': "(('choice', 'title'),)", 'object_name': 'EventChoiceOption'},
            'choice': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'options'", 'to': u"orm['OneEvent.EventChoice']"}),
            'default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '256'})
        },
        u'OneEvent.message': {
            'Meta': {'object_name': 'Message'},
            'category': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'text': ('django.db.models.fields.TextField', [], {'max_length': '2048'}),
            'thread_head': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'thread'", 'null': 'True', 'to': u"orm['OneEvent.Message']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        u'OneEvent.participantbooking': {
            'Meta': {'unique_together': "(('event', 'person'),)", 'object_name': 'ParticipantBooking'},
            'cancelledBy': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'cancelled_bookings'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'cancelledOn': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'datePaid': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'bookings'", 'to': u"orm['OneEvent.Event']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'paidTo': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'received_payments'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'bookings'", 'to': u"orm['auth.User']"})
        },
        u'OneEvent.participantoption': {
            'Meta': {'unique_together': "(('booking', 'option'),)", 'object_name': 'ParticipantOption'},
            'booking': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'options'", 'to': u"orm['OneEvent.ParticipantBooking']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'option': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['OneEvent.EventChoiceOption']", 'null': 'True', 'blank': 'True'})
        },
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['OneEvent']