# Generated by Django 3.1.1 on 2020-11-24 12:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('restaurant', '0031_auto_20201124_1231'),
    ]

    operations = [
        migrations.AlterField(
            model_name='food',
            name='discount',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='foods', to='restaurant.discount'),
        ),
    ]
