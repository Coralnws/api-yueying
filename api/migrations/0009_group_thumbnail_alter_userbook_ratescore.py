# Generated by Django 4.0.3 on 2022-05-28 04:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0008_alter_userbook_ratescore'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='thumbnail',
            field=models.ImageField(blank=True, upload_to='uploads/groups'),
        ),
        migrations.AlterField(
            model_name='userbook',
            name='rateScore',
            field=models.IntegerField(default=-1),
        ),
    ]
