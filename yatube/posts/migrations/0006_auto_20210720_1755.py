# Generated by Django 2.2.9 on 2021-07-20 14:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0005_auto_20210720_1748'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='post',
            options={'ordering': ['-pub_date'], 'verbose_name_plural': 'Posts'},
        ),
    ]
