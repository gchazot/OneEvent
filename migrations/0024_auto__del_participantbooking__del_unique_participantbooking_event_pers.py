# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        #  Rename model ParticipantBooking into Booking
        db.rename_table(u'OneEvent_participantbooking', u'OneEvent_booking')

        # Rename model EventChoiceOption into Option
        db.rename_table(u'OneEvent_eventchoiceoption', u'OneEvent_option')

        # Rename model EventChoice into Choice
        db.rename_table(u'OneEvent_eventchoice', u'OneEvent_choice')

        # Rename model ParticipantOption into BookingOption
        db.rename_table(u'OneEvent_participantoption', u'OneEvent_bookingoption')


    def backwards(self, orm):
        #  Rename model ParticipantBooking into Booking
        db.rename_table(u'OneEvent_booking', u'OneEvent_participantbooking')

        # Rename model EventChoiceOption into Option
        db.rename_table(u'OneEvent_option', u'OneEvent_eventchoiceoption')

        # Rename model EventChoice into Choice
        db.rename_table(u'OneEvent_choice', u'OneEvent_eventchoice')

        # Rename model ParticipantOption into BookingOption
        db.rename_table(u'OneEvent_bookingoption', u'OneEvent_participantoption')


    models = {
        u'OneEvent.booking': {
            'Meta': {'ordering': "['id']", 'unique_together': "(('event', 'person'),)", 'object_name': 'Booking'},
            'cancelledBy': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'cancelled_bookings'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'cancelledOn': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'confirmedOn': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'datePaid': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'bookings'", 'to': u"orm['OneEvent.Event']"}),
            'exempt_of_payment': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'paidTo': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'received_payments'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'bookings'", 'to': u"orm['auth.User']"})
        },
        u'OneEvent.bookingoption': {
            'Meta': {'ordering': "['option__choice__id', 'option__id', 'id']", 'unique_together': "(('booking', 'option'),)", 'object_name': 'BookingOption'},
            'booking': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'options'", 'to': u"orm['OneEvent.Booking']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'option': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['OneEvent.Option']", 'null': 'True', 'blank': 'True'})
        },
        u'OneEvent.choice': {
            'Meta': {'ordering': "['id']", 'unique_together': "(('event', 'title'),)", 'object_name': 'Choice'},
            'event': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'choices'", 'to': u"orm['OneEvent.Event']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        u'OneEvent.event': {
            'Meta': {'object_name': 'Event'},
            'booking_close': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'choices_close': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'contractors_groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'contractors_for_event+'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'employees_groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'employees_for_event+'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            'end': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location_address': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'location_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'organisers': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'events_organised'", 'blank': 'True', 'to': u"orm['auth.User']"}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'events_owned'", 'to': u"orm['auth.User']"}),
            'price_currency': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'price_for_contractors': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '6', 'decimal_places': '2'}),
            'price_for_employees': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '6', 'decimal_places': '2'}),
            'pub_status': ('django.db.models.fields.CharField', [], {'default': "'UNPUB'", 'max_length': '8'}),
            'start': ('django.db.models.fields.DateTimeField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'})
        },
        u'OneEvent.message': {
            'Meta': {'ordering': "['-created']", 'object_name': 'Message'},
            'category': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'safe_content': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'text': ('django.db.models.fields.TextField', [], {'max_length': '2048'}),
            'thread_head': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'thread'", 'null': 'True', 'to': u"orm['OneEvent.Message']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        u'OneEvent.option': {
            'Meta': {'ordering': "['choice__id', 'id']", 'unique_together': "(('choice', 'title'),)", 'object_name': 'Option'},
            'choice': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'options'", 'to': u"orm['OneEvent.Choice']"}),
            'default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '256'})
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