# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Event'
        db.create_table(u'OneEvent_event', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=64)),
            ('start', self.gf('django.db.models.fields.DateTimeField')()),
            ('end', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'OneEvent', ['Event'])

        # Adding M2M table for field organisers on 'Event'
        db.create_table(u'OneEvent_event_organisers', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('event', models.ForeignKey(orm[u'OneEvent.event'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(u'OneEvent_event_organisers', ['event_id', 'user_id'])

        # Adding model 'EventChoice'
        db.create_table(u'OneEvent_eventchoice', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('event', self.gf('django.db.models.fields.related.ForeignKey')(related_name='choices', to=orm['OneEvent.Event'])),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal(u'OneEvent', ['EventChoice'])

        # Adding unique constraint on 'EventChoice', fields ['event', 'title']
        db.create_unique(u'OneEvent_eventchoice', ['event_id', 'title'])

        # Adding model 'EventChoiceOption'
        db.create_table(u'OneEvent_eventchoiceoption', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('choice', self.gf('django.db.models.fields.related.ForeignKey')(related_name='options', to=orm['OneEvent.EventChoice'])),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('default', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'OneEvent', ['EventChoiceOption'])

        # Adding unique constraint on 'EventChoiceOption', fields ['choice', 'title']
        db.create_unique(u'OneEvent_eventchoiceoption', ['choice_id', 'title'])

        # Adding model 'ParticipantBooking'
        db.create_table(u'OneEvent_participantbooking', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('event', self.gf('django.db.models.fields.related.ForeignKey')(related_name='bookings', to=orm['OneEvent.Event'])),
            ('person', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('cancelled', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('mustPay', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('paidTo', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='received_payments', null=True, to=orm['auth.User'])),
            ('datePaid', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'OneEvent', ['ParticipantBooking'])

        # Adding unique constraint on 'ParticipantBooking', fields ['event', 'person']
        db.create_unique(u'OneEvent_participantbooking', ['event_id', 'person_id'])

        # Adding model 'ParticipantOption'
        db.create_table(u'OneEvent_participantoption', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('booking', self.gf('django.db.models.fields.related.ForeignKey')(related_name='options', to=orm['OneEvent.ParticipantBooking'])),
            ('option', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['OneEvent.EventChoiceOption'], null=True, blank=True)),
        ))
        db.send_create_signal(u'OneEvent', ['ParticipantOption'])

        # Adding unique constraint on 'ParticipantOption', fields ['booking', 'option']
        db.create_unique(u'OneEvent_participantoption', ['booking_id', 'option_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'ParticipantOption', fields ['booking', 'option']
        db.delete_unique(u'OneEvent_participantoption', ['booking_id', 'option_id'])

        # Removing unique constraint on 'ParticipantBooking', fields ['event', 'person']
        db.delete_unique(u'OneEvent_participantbooking', ['event_id', 'person_id'])

        # Removing unique constraint on 'EventChoiceOption', fields ['choice', 'title']
        db.delete_unique(u'OneEvent_eventchoiceoption', ['choice_id', 'title'])

        # Removing unique constraint on 'EventChoice', fields ['event', 'title']
        db.delete_unique(u'OneEvent_eventchoice', ['event_id', 'title'])

        # Deleting model 'Event'
        db.delete_table(u'OneEvent_event')

        # Removing M2M table for field organisers on 'Event'
        db.delete_table('OneEvent_event_organisers')

        # Deleting model 'EventChoice'
        db.delete_table(u'OneEvent_eventchoice')

        # Deleting model 'EventChoiceOption'
        db.delete_table(u'OneEvent_eventchoiceoption')

        # Deleting model 'ParticipantBooking'
        db.delete_table(u'OneEvent_participantbooking')

        # Deleting model 'ParticipantOption'
        db.delete_table(u'OneEvent_participantoption')


    models = {
        u'OneEvent.event': {
            'Meta': {'object_name': 'Event'},
            'end': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'organisers': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.User']", 'symmetrical': 'False', 'blank': 'True'}),
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
            'title': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        u'OneEvent.participantbooking': {
            'Meta': {'unique_together': "(('event', 'person'),)", 'object_name': 'ParticipantBooking'},
            'cancelled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'datePaid': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'bookings'", 'to': u"orm['OneEvent.Event']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mustPay': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'paidTo': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'received_payments'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
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