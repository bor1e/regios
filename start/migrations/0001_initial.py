# Generated by Django 2.1.2 on 2018-11-26 14:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Domains',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('domain', models.TextField(max_length=200, unique=True)),
                ('url', models.URLField()),
                ('status', models.CharField(default='started', max_length=10)),
                ('level', models.SmallIntegerField(default=0)),
                ('duration', models.DurationField(null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'get_latest_by': 'updated_at',
            },
        ),
        migrations.CreateModel(
            name='Externals',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.URLField()),
                ('domain', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='externals', to='start.Domains')),
            ],
            options={
                'ordering': ('url',),
            },
        ),
        migrations.CreateModel(
            name='Info',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('title', models.CharField(max_length=100)),
                ('source_url', models.URLField()),
                ('other', models.TextField(null=True)),
                ('domain', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='info', to='start.Domains')),
            ],
        ),
        migrations.CreateModel(
            name='Locals',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.URLField()),
                ('domain', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='locals', to='start.Domains')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='locals',
            unique_together={('url', 'domain')},
        ),
        migrations.AlterUniqueTogether(
            name='externals',
            unique_together={('url', 'domain')},
        ),
    ]