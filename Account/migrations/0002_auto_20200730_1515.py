# Generated by Django 3.0.6 on 2020-07-30 14:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Account', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='secret',
            field=models.BinaryField(default=b'odKS_cin7tfPsvtgnHK2A_1Auf7BENsm86GouX_I-Fs='),
        ),
    ]
