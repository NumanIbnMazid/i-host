# Generated by Django 3.1.1 on 2020-11-29 05:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account_management', '0014_useraccount_first_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='hotelstaffinformation',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
    ]