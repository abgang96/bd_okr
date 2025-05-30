# Generated by Django 4.2.10 on 2025-05-09 11:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('teamsauth', '0003_teamsprofile_user_name'),
        ('okrapi', '0010_remove_okr_assigned_to'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='teams_profile',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='okr_user', to='teamsauth.teamsprofile'),
        ),
        migrations.AlterField(
            model_name='log',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='teamsauth.teamsprofile'),
        ),
        migrations.AlterField(
            model_name='okr',
            name='assigned_users',
            field=models.ManyToManyField(related_name='assigned_okrs_many', through='okrapi.OkrUserMapping', to='teamsauth.teamsprofile'),
        ),
        migrations.AlterField(
            model_name='okrusermapping',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='okr_mappings', to='teamsauth.teamsprofile'),
        ),
        migrations.AlterField(
            model_name='task',
            name='assigned_to',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assigned_tasks', to='teamsauth.teamsprofile'),
        ),
    ]
