# Generated by Django 3.0.6 on 2020-07-01 09:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Account', '0003_auto_20200630_2100'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='secret',
            field=models.BinaryField(default=b'BmcSlByozogeIoDDZcqWcAeu86CTRAr2647dXT0uEDs='),
        ),
    ]