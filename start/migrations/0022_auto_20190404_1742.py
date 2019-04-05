# Generated by Django 2.1.7 on 2019-04-04 15:42

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('start', '0021_auto_20190404_1250'),
    ]

    operations = [
        migrations.AlterField(
            model_name='externalspider',
            name='unique_id',
            field=models.CharField(default=uuid.UUID('3711b85e-56f0-11e9-8e02-8c85908458e4'), max_length=128, unique=True),
        ),
        migrations.AlterField(
            model_name='infospider',
            name='unique_id',
            field=models.CharField(default=uuid.UUID('3711d03c-56f0-11e9-8e02-8c85908458e4'), max_length=128, unique=True),
        ),
    ]