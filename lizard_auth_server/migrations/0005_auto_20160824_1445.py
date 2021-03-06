# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-08-24 12:45
from django.db import migrations


def add_missing_profiles(apps, schema_editor):
    UserProfile = apps.get_model("lizard_auth_server", "UserProfile")
    Profile = apps.get_model("lizard_auth_server", "Profile")
    for old_profile in UserProfile.objects.filter(user__profile__isnull=True):
        new_profile = Profile.objects.create(user=old_profile.user)
        new_profile.save()
        new_profile.created_at = old_profile.created_at
        new_profile.save()
        print("Created new profile for %s" % old_profile.user)


class Migration(migrations.Migration):

    dependencies = [
        ("lizard_auth_server", "0004_auto_20160818_1641"),
    ]

    operations = [
        migrations.RunPython(add_missing_profiles),
    ]
