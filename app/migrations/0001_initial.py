# Generated by Django 5.1.2 on 2024-10-21 08:58

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ExcelData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('serial_number', models.CharField(max_length=100, unique=True)),
                ('imei_number', models.CharField(max_length=100)),
                ('unique_number', models.CharField(max_length=100)),
                ('is_printed', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Label',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('barcode', models.CharField(max_length=100, unique=True)),
                ('stage', models.CharField(choices=[('first', 'First Stage'), ('second', 'Second Stage')], max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('printed_at', models.DateTimeField(blank=True, null=True)),
                ('is_printed', models.BooleanField(default=False)),
                ('serial_number', models.CharField(blank=True, max_length=100, null=True)),
                ('imei_number', models.CharField(blank=True, max_length=100, null=True)),
                ('unique_number', models.CharField(blank=True, max_length=100, null=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
