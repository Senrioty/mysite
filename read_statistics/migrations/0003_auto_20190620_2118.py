# Generated by Django 2.0.13 on 2019-06-20 13:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('read_statistics', '0002_readdetail'),
    ]

    operations = [
        migrations.RenameField(
            model_name='readdetail',
            old_name='read_now',
            new_name='read_num',
        ),
    ]
