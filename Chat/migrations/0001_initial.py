# Generated by Django 3.0.6 on 2020-07-21 06:54

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ChatThread',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('show_first', models.BooleanField(default=True)),
                ('show_second', models.BooleanField(default=True)),
                ('date_created', models.DateTimeField()),
                ('date_first', models.NullBooleanField(default=None)),
                ('date_second', models.NullBooleanField(default=None)),
                ('show_details', models.BooleanField(default=False)),
                ('first_deleted', models.TextField(default='[]')),
                ('second_deleted', models.TextField(default='[]')),
                ('secret', models.BinaryField()),
                ('expiry_date', models.DateTimeField(default=None)),
                ('last_message_date', models.DateTimeField(default=None, null=True)),
                ('first_user', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='chatter1', to=settings.AUTH_USER_MODEL)),
                ('second_user', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='chatter2', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ChatMessage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.BinaryField()),
                ('datetime', models.DateTimeField()),
                ('send_status', models.CharField(choices=[('sent', 'sent'), ('delivered', 'delivered')], max_length=20)),
                ('chat', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Chat.ChatThread')),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
