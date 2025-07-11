# Generated by Django 5.2.2 on 2025-06-15 14:43

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_sample_qc_flag_referencerange'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='batch',
            name='samples',
        ),
        migrations.RemoveField(
            model_name='testresult',
            name='method',
        ),
        migrations.AddField(
            model_name='sample',
            name='batch',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='samples', to='core.batch'),
        ),
        migrations.AlterField(
            model_name='testresult',
            name='unit',
            field=models.CharField(default='%', max_length=20),
        ),
    ]
