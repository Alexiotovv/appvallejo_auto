from django.db import models

class settingsCartas(models.Model):
    
    Dia = models.CharField(max_length=20,null=True, blank=True)
    Mes = models.CharField(max_length=50,null=True, blank=True)
    Ano = models.CharField(max_length=255,null=True, blank=True)
    Estado = models.BooleanField(default=True)  # Valor por defecto
