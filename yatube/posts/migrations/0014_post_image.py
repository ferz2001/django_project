# Generated by Django 2.2.9 on 2021-08-29 09:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0013_remove_post_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='image',
            field=models.ImageField(blank=True, upload_to='posts/', verbose_name='Картинка'),
        ),
    ]