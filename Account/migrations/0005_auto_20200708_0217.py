# Generated by Django 3.0.6 on 2020-07-08 01:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Account', '0004_auto_20200705_2223'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='secret',
            field=models.BinaryField(default=b'01TXPuBq7hinB8itl_kBvL3nYiMLn9Q2QZL77US6VM0='),
        ),
    ]
