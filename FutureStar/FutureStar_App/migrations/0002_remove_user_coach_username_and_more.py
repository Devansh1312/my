# Generated by Django 5.0 on 2024-10-15 04:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('FutureStar_App', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='coach_username',
        ),
        migrations.RemoveField(
            model_name='user',
            name='referee_username',
        ),
    ]
