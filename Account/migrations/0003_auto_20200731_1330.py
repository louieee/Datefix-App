# Generated by Django 3.0.6 on 2020-07-31 12:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Account', '0002_auto_20200730_1515'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='secret',
            field=models.BinaryField(default=b'i6P67V4FwF47er1FMJ9onMKnG51EBqtaUxxqZShs-4o='),
        ),
    ]
