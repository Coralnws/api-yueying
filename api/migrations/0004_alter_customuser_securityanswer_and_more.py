# Generated by Django 4.0.3 on 2022-05-15 06:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_rename_groupadminapply_groupadminrequest_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='securityAnswer',
            field=models.CharField(max_length=500),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='securityQuestion',
            field=models.IntegerField(choices=[(1, '您最喜欢的颜色是'), (2, '您最讨厌的食物'), (3, '您的最要好闺蜜/兄弟是'), (4, '您的爱好是'), (5, '您的初恋是')], default=1),
        ),
    ]
