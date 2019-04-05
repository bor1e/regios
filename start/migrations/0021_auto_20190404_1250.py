# Generated by Django 2.1.7 on 2019-04-04 10:50

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('start', '0020_auto_20190404_1035'),
    ]

    operations = [
        migrations.AddField(
            model_name='externalspider',
            name='status',
            field=models.TextField(max_length=80, null=True),
        ),
        migrations.AddField(
            model_name='infospider',
            name='name',
            field=models.TextField(max_length=80, null=True),
        ),
        migrations.AddField(
            model_name='infospider',
            name='status',
            field=models.TextField(max_length=80, null=True),
        ),
        migrations.AlterField(
            model_name='externalspider',
            name='unique_id',
            field=models.CharField(default=uuid.UUID('721cca02-56c7-11e9-a25b-8c85908458e4'), max_length=128, unique=True),
        ),
        migrations.AlterField(
            model_name='infospider',
            name='unique_id',
            field=models.CharField(default=uuid.UUID('721ce208-56c7-11e9-a25b-8c85908458e4'), max_length=128, unique=True),
        ),
    ]