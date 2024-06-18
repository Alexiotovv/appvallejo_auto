# Generated by Django 4.1 on 2024-06-14 20:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appMain', '0004_alter_viewpagostable_fechavencimiento'),
    ]

    operations = [
        migrations.AlterField(
            model_name='viewpagostable',
            name='Apellido',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='viewpagostable',
            name='Apoderado',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name='viewpagostable',
            name='Concepto',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='viewpagostable',
            name='ConceptoNumeroMes',
            field=models.CharField(blank=True, max_length=2, null=True),
        ),
        migrations.AlterField(
            model_name='viewpagostable',
            name='DiasAtraso',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='viewpagostable',
            name='Direccion',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name='viewpagostable',
            name='Dni',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='viewpagostable',
            name='Grado',
            field=models.CharField(blank=True, max_length=101, null=True),
        ),
        migrations.AlterField(
            model_name='viewpagostable',
            name='Madre',
            field=models.CharField(blank=True, max_length=550, null=True),
        ),
        migrations.AlterField(
            model_name='viewpagostable',
            name='Mes',
            field=models.CharField(blank=True, max_length=12, null=True),
        ),
        migrations.AlterField(
            model_name='viewpagostable',
            name='Nivel',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='viewpagostable',
            name='Nombre',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='viewpagostable',
            name='NombreCompleto',
            field=models.CharField(blank=True, max_length=306, null=True),
        ),
        migrations.AlterField(
            model_name='viewpagostable',
            name='Padre',
            field=models.CharField(blank=True, max_length=550, null=True),
        ),
        migrations.AlterField(
            model_name='viewpagostable',
            name='Seccion',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='viewpagostable',
            name='TipoIngreso',
            field=models.CharField(blank=True, max_length=13, null=True),
        ),
        migrations.AlterField(
            model_name='viewpagostable',
            name='descripcion',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
    ]