from django.core.management.base import BaseCommand
from django.db import connections,models
from datetime import datetime,date
from appMain.models import VentaSincronizada
from appsettingsCartas.models import SettingsVentaSincronizada
import requests

class Command(BaseCommand):
    help = 'Sincroniza ventas desde la vista local a la nube por API'

    def handle(self, *args, **options):
        # 🔹 Leer configuración UNA SOLA VEZ
        config = SettingsVentaSincronizada.objects.only('url', 'token').first()
        
        if not config:
            self.stdout.write(self.style.ERROR("⚠️ No se encontró la configuración de sincronización (URL y TOKEN)"))
            return

        API_URL = config.url
        API_TOKEN = config.token

        # 🔹 Obtener el último ID sincronizado
        ultimo_id = VentaSincronizada.objects.aggregate(models.Max('id_operation'))['id_operation__max'] or 0

        # 🔹 Consultar la vista de ventas con filtro
        with connections['facturacion'].cursor() as cursor:
            cursor.execute("SELECT * FROM view_pagos WHERE id_operation > %s", [ultimo_id])
            columns = [col[0] for col in cursor.description]
            ventas = [dict(zip(columns, row)) for row in cursor.fetchall()]

        nuevas_ventas = 0

        for venta in ventas:
            data = {
                'id_operation': venta['id_operation'],
                'id_persona': venta['id_persona'],
                'descripcion': venta['descripcion'],
                'Dni': venta['Dni'],
                'NombreCompleto': venta['NombreCompleto'],
                'Nivel': venta['Nivel'],
                'Grado': venta['Grado'],
                'Seccion': venta['Seccion'],
                'Concepto': venta['Concepto'],
                'Mes': venta['Mes'],
                'TipoIngreso': venta['TipoIngreso'],
                'ConceptoNumeroMes': venta['ConceptoNumeroMes'],
                'FechaVencimiento': venta['FechaVencimiento'],
                'Monto': venta['Monto'],
                'FechaPago': venta['FechaPago'],
                'NumeroMesPago': venta['NumeroMesPago'],
                'LetraMesPago': venta['LetraMesPago'],
                'Atrasado': venta['Atrasado'],
                'DiasAtraso': venta['DiasAtraso'],
                'MesesAtraso': venta['MesesAtraso'],
                'Apoderado': venta['Apoderado'],
                'Padre': venta['Padre'],
                'Madre': venta['Madre'],
                'Direccion': venta['Direccion'],
            }
            data = convertir_valores(data)

            try:
                response = requests.post(API_URL, json=data, headers={
                    'Authorization': f'Token {API_TOKEN}',
                    'Content-Type': 'application/json'
                })

                if response.status_code == 201:
                    VentaSincronizada.objects.create(
                        id_operation=venta['id_operation'],
                        fecha_envio=datetime.now(),
                        estado='sincronizado'
                    )
                    self.stdout.write(self.style.SUCCESS(f"✔️ Venta {venta['id_operation']} sincronizada"))
                    nuevas_ventas += 1
                else:
                    self.stdout.write(self.style.ERROR(f"❌ Error al sincronizar {venta['id_operation']}: {response.text}"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"🔥 Excepción con venta {venta['id_operation']}: {str(e)}"))

        self.stdout.write(self.style.SUCCESS(f"🔁 Total nuevas ventas sincronizadas: {nuevas_ventas}"))

from decimal import Decimal

def convertir_valores(obj):
    if isinstance(obj, dict):
        return {k: convertir_valores(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convertir_valores(elem) for elem in obj]
    elif isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, (datetime, date)):
        return obj.strftime('%Y-%m-%d')
    else:
        return obj