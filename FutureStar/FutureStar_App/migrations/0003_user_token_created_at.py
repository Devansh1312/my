# Generated by Django 5.0 on 2024-09-10 05:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('FutureStar_App', '0002_user_email_verified_at_user_remember_token'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='token_created_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]