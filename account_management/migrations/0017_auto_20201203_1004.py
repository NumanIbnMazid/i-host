# Generated by Django 3.1.1 on 2020-12-03 10:04

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account_management', '0016_auto_20201203_0843'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customerinfo',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]