# Generated by Django 5.0 on 2024-10-09 08:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('FutureStar_App', '0002_alter_cms_advertise_partnership_dynamic_field_table'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True, unique=True),
        ),
    ]