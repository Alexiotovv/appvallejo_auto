# Generated by Django 4.1 on 2024-06-14 20:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appMain', '0006_alter_viewpagostable_mesesatraso'),
    ]

    operations = [
        migrations.AlterField(
            model_name='viewpagostable',
            name='Dni',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
