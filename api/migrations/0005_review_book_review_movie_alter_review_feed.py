# Generated by Django 4.0.3 on 2022-05-19 10:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_alter_customuser_securityanswer_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='review',
            name='book',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.book'),
        ),
        migrations.AddField(
            model_name='review',
            name='movie',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.movie'),
        ),
        migrations.AlterField(
            model_name='review',
            name='feed',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.feed'),
        ),
    ]