# Generated by Django 3.1.7 on 2021-03-09 18:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('movie', '0002_auto_20210309_2327'),
    ]

    operations = [
        migrations.AlterField(
            model_name='movie',
            name='image',
            field=models.ImageField(default='', upload_to='media/images'),
        ),
    ]