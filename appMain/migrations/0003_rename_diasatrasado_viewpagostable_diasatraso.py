# Generated by Django 4.1 on 2024-06-14 20:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('appMain', '0002_viewpagostable'),
    ]

    operations = [
        migrations.RenameField(
            model_name='viewpagostable',
            old_name='DiasAtrasado',
            new_name='DiasAtraso',
        ),
    ]
