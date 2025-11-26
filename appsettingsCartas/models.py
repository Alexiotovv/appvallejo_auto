from django.db import models

class settingsCartas(models.Model):
    
    Dia = models.CharField(max_length=20,null=True, blank=True)
    Mes = models.CharField(max_length=50,null=True, blank=True)
    Ano = models.CharField(max_length=255,null=True, blank=True)
    Estado = models.BooleanField(default=True)  # Valor por defecto

class settingsDatos(models.Model):
    url = models.CharField(max_length=400,null=True, blank=True)
    ano_actual = models.CharField(max_length=4,null=True, blank=True)
    url_meses_no_paga = models.CharField(max_length=400,null=True, blank=True)
    monto_pago = models.DecimalField(max_digits=10, decimal_places=2, null=True,blank=True)

class SettingsVentaSincronizada(models.Model):
    url = models.CharField(max_length=400, null=True, blank=True)
    token = models.CharField(max_length=400, null=True, blank=True)

    def __str__(self):
        return f"Sync Settings (URL: {self.url})"

