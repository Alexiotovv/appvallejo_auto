from django.db import models

class CartasEnviadas(models.Model):
    dni_alumno=models.CharField(max_length=10)
    numero_carta=models.IntegerField(default=0)
    
    def __str__(self):
        f"{self.dni_alumno}"

class ViewPagosTable(models.Model):
    id_operation = models.BigIntegerField()
    id_persona = models.BigIntegerField()
    descripcion = models.CharField(max_length=500,null=True, blank=True)
    Dni = models.CharField(max_length=20,null=True, blank=True)
    Nombre = models.CharField(max_length=50,null=True, blank=True)
    Apellido = models.CharField(max_length=255,null=True, blank=True)
    NombreCompleto = models.CharField(max_length=306,null=True, blank=True)
    Nivel = models.CharField(max_length=100,null=True, blank=True)
    Grado = models.CharField(max_length=101,null=True, blank=True)
    Seccion = models.CharField(max_length=100,null=True, blank=True)
    Concepto = models.CharField(max_length=50,null=True, blank=True)
    Mes = models.CharField(max_length=12,null=True, blank=True)
    TipoIngreso = models.CharField(max_length=13,null=True, blank=True)
    ConceptoNumeroMes = models.CharField(max_length=2,null=True, blank=True)
    FechaVencimiento = models.CharField(max_length=10,null=True, blank=True)
    Monto = models.DecimalField(max_digits=8, decimal_places=2)
    FechaPago = models.DateField()
    NumeroMesPago = models.BigIntegerField()
    LetraMesPago = models.CharField(max_length=12)
    Atrasado = models.CharField(max_length=2)
    DiasAtraso = models.IntegerField(null=True, blank=True)
    MesesAtraso = models.CharField(max_length=50,null=True, blank=True)
    Apoderado = models.CharField(max_length=250,null=True, blank=True)
    Padre = models.CharField(max_length=550,null=True, blank=True)
    Madre = models.CharField(max_length=550,null=True, blank=True)
    Direccion = models.CharField(max_length=250,null=True, blank=True)


class AlumnosTableApi(models.Model):
    Grado = models.CharField(max_length=10,null=True, blank=True)
    Seccion = models.CharField(max_length=2,null=True, blank=True)
    Dni = models.CharField(max_length=10,null=True, blank=True)
    ApellidoPaterno = models.CharField(max_length=250,null=True, blank=True)
    ApellidoMaterno = models.CharField(max_length=250,null=True, blank=True)
    Nombres = models.CharField(max_length=250,null=True, blank=True)
    TelefonoTutor = models.CharField(max_length=100,null=True, blank=True)
    FirstNameTutor = models.CharField(max_length=250,null=True, blank=True)
    LastNameTutor = models.CharField(max_length=250,null=True, blank=True)

class VentaSincronizada(models.Model):
    id_operation = models.BigIntegerField()
    fecha_envio = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, default='pendiente')

    def __str__(self):
        return f"Venta {self.id_operation} - {self.estado}"