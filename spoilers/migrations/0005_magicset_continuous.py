# Generated by Django 3.0.7 on 2020-10-05 13:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('spoilers', '0004_auto_20200408_0642'),
    ]

    operations = [
        migrations.AddField(
            model_name='magicset',
            name='continuous',
            field=models.BooleanField(default=False),
        ),
    ]