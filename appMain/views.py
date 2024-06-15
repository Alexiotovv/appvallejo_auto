from django.shortcuts import render,redirect
from appMetricas.views import obtener_datos_de_api
from django.db import connections
from django.db import connection

from .models import *
import MySQLdb
from datetime import datetime as dt
from django.http import JsonResponse
import pandas as pd
from django.http import HttpResponse


def cant_pagos_nivel(request):
    
    with connection.cursor() as cursor:
        cursor.callproc('GetPagosPorNivel')
    
        resultados = cursor.fetchall()

        datos=[]

        for row in resultados:
            datos.append({
                            'NIVEL':row[0],
                            'Cantidad':float(row[1])
            })
    
    return JsonResponse({'cant_pagos_nivel':datos})

def cant_pagos_mes(request):
    
    with connection.cursor() as cursor:
        cursor.callproc('GetPagosPorMes')
    
        resultados = cursor.fetchall()

        datos=[]

        for row in resultados:
            datos.append({
                            'Mes':row[1],
                            'Cantidad':float(row[2])
            })
    
    return JsonResponse({'cant_pagos_mes':datos})


def index(request):
    meses=[{'mes':'MARZO'},{'mes':'ABRIL'},{'mes':'MAYO'},{'mes':'JUNIO'},{'mes':'JULIO'},{'mes':'AGOSTO'},{'mes':'SETIEMBRE'},{'mes':'OCTUBRE'},{'mes':'NOVIEMBRE'},{'mes':'DICIEMBRE'}]
    return render(request,'homes/home.html',{'meses':meses})

def refrescar_datos(request):
    connection = connections['facturacion']
    connection.ensure_connection()

    cursor = connection.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM view_pagos vp")
    pagos = cursor.fetchall()

    url = "https://colcoopcv.com/listar/matriculados/2024"
    alumnos = obtener_datos_de_api(url)
    campo_no_deseado = 'Id'

    for alumno in alumnos:
        alumno.pop(campo_no_deseado, None)    

    AlumnosTableApi.objects.all().delete()
    ViewPagosTable.objects.all().delete()

    for pago in pagos:
        ViewPagosTable.objects.create(**pago)
    
    for alumno in alumnos:
        AlumnosTableApi.objects.create(**alumno)

    return redirect('home')

def descargar_deudores(request):
    data=generar_pagos()
    df=generar_deudores(data)
    df = df.rename(columns={'Mes': 'MesesPagados'})
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=alumnos.xlsx'

    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)

    return response

def generar_deudores(data):
    vcmtos = {3:27, 4:30, 5:31, 6:28, 7:31, 8:29, 9:30, 10:31, 11:28, 12:20}    
    fecha_actual = dt.now().date()
    mes_actual = dt.now().month
    fecha_vcmto = fecha_actual.replace(day=vcmtos[mes_actual])
    if fecha_actual < fecha_vcmto:
        mes_ultimo_vcmto = mes_actual - 1
    else:
        mes_ultimo_vcmto = mes_actual

    df = pd.DataFrame(data)
    todos_los_meses = ['MARZO', 'ABRIL', 'MAYO', 'JUNIO', 'JULIO', 'AGOSTO', 'SETIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE']
    
    meses_hasta_ultimo_vencimiento = todos_los_meses[:mes_ultimo_vcmto - 2]  # -2 porque MARZO es el índice 0 y necesitamos hasta el mes anterior al último vencimiento
    
    def obtener_meses_debe(meses_pagados):
        return [mes for mes in meses_hasta_ultimo_vencimiento if mes not in meses_pagados]

    df['MesesDebe'] = df['Mes'].apply(obtener_meses_debe)
    
    df = df[df['MesesDebe'].apply(len) > 0]

    return df

def generar_pagos():
    resultados=[]
    connection = connections['facturacion']
    connection.ensure_connection()

    cursor1 = connection.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor1.execute("SELECT person.numero_documento as 'Dni', person.email1 as 'Apoderado' FROM person where person.email1 != '' ")
    apoderados = cursor1.fetchall()

    cursor2 = connection.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor2.execute("SELECT person.numero_documento as 'Dni', person.address1 as 'Direccion' FROM person where person.address1 != '' ")
    direcciones = cursor2.fetchall()

    pagos= ViewPagosTable.objects.all()
    alumnos=AlumnosTableApi.objects.all() 

    apoderados_dict={str(apo['Dni']).strip():apo for apo in apoderados}
    direcciones_dic={str(dire['Dni']).strip():dire for dire in direcciones}

    for alumno in alumnos:
        dni = (alumno.Dni).strip()
        apoderados=apoderados_dict.get(dni,{})
        direcciones=direcciones_dic.get(dni,{})
        combinado = {
            # 'id': alumno.Id_alumno,
            'DNI': alumno.Dni,
            'ApellidoPaterno': alumno.ApellidoPaterno,
            'ApellidoMaterno': alumno.ApellidoMaterno,
            'Nombres': alumno.Nombres,
            'TelefonoTutor': alumno.TelefonoTutor,
            'Grado': alumno.Grado,
            'Seccion': alumno.Seccion,
            'Mes': [(p.Mes).upper() for p in pagos if p.Dni == dni],
            'Apoderado': apoderados.get('Apoderado'),
            'Direccion': direcciones.get('Direccion'),

        }
        resultados.append(combinado)
    cursor1.close()
    cursor2.close()

    return resultados

    




