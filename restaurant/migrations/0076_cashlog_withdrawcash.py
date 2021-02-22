# Generated by Django 3.1.1 on 2021-02-22 16:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('restaurant', '0075_auto_20210217_1334'),
    ]

    operations = [
        migrations.CreateModel(
            name='CashLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('starting_time', models.DateTimeField(auto_now_add=True)),
                ('ending_time', models.DateTimeField(blank=True, null=True)),
                ('in_cash_while_opening', models.FloatField(blank=True, null=True)),
                ('in_cash_while_closing', models.FloatField(blank=True, null=True)),
                ('total_received_payment', models.FloatField(blank=True, null=True)),
                ('total_cash_received', models.FloatField(blank=True, null=True)),
                ('remarks', models.TextField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('restaurant', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='cash_logs', to='restaurant.restaurant')),
            ],
        ),
        migrations.CreateModel(
            name='WithdrawCash',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.FloatField(blank=True, null=True)),
                ('withdraw_at', models.DateTimeField(auto_now=True)),
                ('details', models.TextField(blank=True, null=True)),
                ('cash_log', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='withdraw_cashs', to='restaurant.cashlog')),
            ],
        ),
    ]