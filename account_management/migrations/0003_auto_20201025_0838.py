# Generated by Django 3.1.1 on 2020-10-25 08:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account_management', '0002_auto_20201025_0805'),
    ]

    operations = [
        migrations.RenameField(
            model_name='useraccount',
            old_name='user_status',
            new_name='status',
        ),
    ]
