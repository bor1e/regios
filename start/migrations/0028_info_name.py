# Generated by Django 2.1.7 on 2019-04-04 17:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('start', '0027_auto_20190404_1934'),
    ]

    operations = [
        migrations.AddField(
            model_name='info',
            name='name',
            field=models.TextField(max_length=200, null=True),
        ),
    ]
