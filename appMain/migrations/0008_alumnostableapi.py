# Generated by Django 4.1 on 2024-06-15 02:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appMain', '0007_alter_viewpagostable_dni'),
    ]

    operations = [
        migrations.CreateModel(
            name='AlumnosTableApi',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Grado', models.CharField(blank=True, max_length=10, null=True)),
                ('Seccion', models.CharField(blank=True, max_length=2, null=True)),
                ('Id_alumno', models.BigIntegerField(blank=True, null=True)),
                ('Dni', models.CharField(blank=True, max_length=10, null=True)),
                ('ApellidoPaterno', models.CharField(blank=True, max_length=250, null=True)),
                ('ApellidoMaterno', models.CharField(blank=True, max_length=250, null=True)),
                ('Nombres', models.CharField(blank=True, max_length=250, null=True)),
                ('TelefonoTutor', models.CharField(blank=True, max_length=100, null=True)),
                ('FirstNameTutor', models.CharField(blank=True, max_length=250, null=True)),
                ('LastNameTutor', models.CharField(blank=True, max_length=250, null=True)),
            ],
        ),
    ]
