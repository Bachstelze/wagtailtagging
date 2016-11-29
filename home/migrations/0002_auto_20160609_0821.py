# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-06-09 08:21
from __future__ import unicode_literals

from django.db import migrations, models
import wagtail.wagtailimages.models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='croppedrendition',
            name='file',
            field=models.ImageField(height_field='height', upload_to=wagtail.wagtailimages.models.get_rendition_upload_to, width_field='width'),
        ),
        migrations.AlterField(
            model_name='customrendition',
            name='file',
            field=models.ImageField(height_field='height', upload_to=wagtail.wagtailimages.models.get_rendition_upload_to, width_field='width'),
        ),
    ]
