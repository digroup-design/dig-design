# Generated by Django 2.1.15 on 2020-02-28 00:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dig', '0002_auto_20200227_1501'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sandiego_zone',
            name='imp_date',
            field=models.CharField(max_length=20),
        ),
        migrations.AlterField(
            model_name='sandiego_zone',
            name='name',
            field=models.CharField(max_length=30),
        ),
    ]