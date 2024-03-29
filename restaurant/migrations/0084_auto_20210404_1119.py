# Generated by Django 3.1.4 on 2021-04-04 11:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restaurant', '0083_auto_20210323_1343'),
    ]

    operations = [
        migrations.CreateModel(
            name='TakewayOrderType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('image', models.ImageField(upload_to='')),
            ],
        ),
        migrations.AddField(
            model_name='food',
            name='code',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='takeway_order_type',
            field=models.ManyToManyField(blank=True, to='restaurant.TakewayOrderType'),
        ),
    ]
