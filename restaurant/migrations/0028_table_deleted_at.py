# Generated by Django 3.1.1 on 2020-11-16 06:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restaurant', '0027_auto_20201115_1130'),
    ]

    operations = [
        migrations.AddField(
            model_name='table',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
