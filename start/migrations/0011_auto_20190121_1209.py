# Generated by Django 2.1.2 on 2019-01-21 11:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('start', '0010_auto_20190112_2255'),
    ]

    operations = [
        migrations.RenameField(
            model_name='localignore',
            old_name='local_ignore',
            new_name='ignore',
        ),
        migrations.AlterUniqueTogether(
            name='localignore',
            unique_together={('ignore', 'domain')},
        ),
    ]
