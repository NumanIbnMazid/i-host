# Generated by Django 3.1.1 on 2020-11-05 05:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account_management', '0005_useraccount_date_of_birth'),
    ]

    operations = [
        migrations.AddField(
            model_name='hotelstaffinformation',
            name='image',
            field=models.FileField(blank=True, null=True, upload_to=''),
        ),
    ]