# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2017-12-08 14:46
from django.conf import settings
from django.db import migrations
from django.db import models

import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("lizard_auth_server", "0015_auto_20161005_0854"),
    ]

    operations = [
        migrations.AlterField(
            model_name="token",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="user_tokens",
                to=settings.AUTH_USER_MODEL,
                verbose_name="user",
            ),
        ),
    ]
