# Generated by Django 5.0 on 2024-09-30 13:01

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('FutureStarAPI', '0006_alter_field_additional_information'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Tournament',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tournament_starting_date', models.DateField(blank=True, null=True)),
                ('tournament_final_date', models.DateField(blank=True, null=True)),
                ('number_of_team', models.CharField(blank=True, max_length=255, null=True)),
                ('tournament_name', models.CharField(blank=True, max_length=255, null=True)),
                ('age_group', models.CharField(blank=True, max_length=255, null=True)),
                ('country', models.CharField(blank=True, max_length=255, null=True)),
                ('city', models.CharField(blank=True, max_length=255, null=True)),
                ('logo', models.ImageField(blank=True, null=True, upload_to='tournament_logo/')),
                ('tournament_joining_cost', models.CharField(blank=True, max_length=255, null=True)),
                ('tournament_fields', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='FutureStarAPI.field')),
                ('user_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'futurestar_app_tournament',
            },
        ),
    ]