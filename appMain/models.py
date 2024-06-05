from django.db import models

class CartasEnviadas(models.Model):
    dni_alumno=models.CharField(max_length=10)
    numero_carta=models.IntegerField(default=0)
    
    def __str__(self):
        f"{self.dni_alumno}"

    