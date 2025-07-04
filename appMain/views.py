from django.shortcuts import render,redirect, get_object_or_404
from appMetricas.views import obtener_datos_de_api
from django.db import connections
from django.db import connection

from .models import *
import MySQLdb
from datetime import datetime as dt
from django.http import JsonResponse
import pandas as pd
from django.http import HttpResponse
from django.core.serializers import serialize
from datetime import datetime
from appsettingsCartas.models import settingsDatos
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from utils.text_utils import reemplazar_caracteres  # ajusta esta importación según tu estructura real

@require_POST
@csrf_exempt
def actualizar_cartas_enviadas(request):
    carta_id = request.POST.get('id')
    numero_carta = request.POST.get('numero_carta')

    if carta_id:
        try:
            carta = CartasEnviadas.objects.get(pk=carta_id)
            carta.numero_carta = numero_carta
            carta.save()
            return JsonResponse({'success': True})
        except CartasEnviadas.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'La carta con ese ID no existe.'}, status=404)
    else:
        return JsonResponse({'success': False, 'error': 'ID no proporcionado.'}, status=400)
    

def index_cartas_enviadas(request):

    data = []
    for carta in CartasEnviadas.objects.all():
        alumno = AlumnosTableApi.objects.filter(Dni=carta.dni_alumno).first()
        if alumno:
            data.append({
                'id': carta.id,
                'dni': alumno.Dni,
                'apellido_paterno': alumno.ApellidoPaterno,
                'apellido_materno': alumno.ApellidoMaterno,
                'nombres': alumno.Nombres,
                'numero_carta': carta.numero_carta,
                'grado': f'{alumno.Grado}-{alumno.Seccion}',
            })

    return render(request,'cartasenviadas/index_cartasenviadas.html', {'data': data})

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
    datos_url=""

    datos= settingsDatos.objects.first()
    if datos:
        datos_url = datos.url
    else:
        datos_url="https://colcoopcv.com/listar/matriculados/2025",

    #Aquí sería obtener view_pagos de la base de datos de colcoopcv postgre
    connection = connections['facturacion']
    connection.ensure_connection()

    cursor = connection.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM view_pagos vp")
    pagos = cursor.fetchall()
    #Hasta aquí
    
    url = datos_url
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

def convertir_decimals(lista):
    # Convertir cada Decimal en float y luego en str
    return [str(float(x)) for x in lista]

def descargar_deudores(request):
    data=generar_pagos()
    df=generar_deudores(data)
    df['Monto'] = df['Monto'].apply(convertir_decimals)
    df['Mes'] = df['Mes'].apply(lambda x: ', '.join(x))
    df['Monto'] = df['Monto'].apply(lambda x: ', '.join(x))
    df['MesesDebe'] = df['MesesDebe'].apply(lambda x: ', '.join(x))
    df = df.rename(columns={'Mes': 'MesesPagados'})
    df = df.rename(columns={'Monto': 'MontoPagados'})

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=alumnos.xlsx'

    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)

    return response

def generar_deudores(data):
    vcmtos = {3:31, 4:30, 5:31, 6:30, 7:31, 8:30, 9:30, 10:31, 11:29, 12:22}
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
    


    datos_monto_pago=0
    datos= settingsDatos.objects.first()
    if datos:
        datos_monto_pago = datos.monto_pago
    else:
        datos_monto_pago = 270


    def obtener_meses_debe(meses_pagados, montos_pagados, descripcion):
        meses_debe = []
        deuda_total = 0
        for mes in meses_hasta_ultimo_vencimiento:
            total_monto_pagado = 0
            for i, mes_pagado in enumerate(meses_pagados):
                if mes_pagado == mes:
                    if montos_pagados[i] >= datos_monto_pago or 'BECA' in descripcion[i]:
                        total_monto_pagado = datos_monto_pago  # Esto asegura que el mes se considere pagado
                        break
                    elif 'CUENTA' in descripcion[i] or montos_pagados[i] < datos_monto_pago:
                        total_monto_pagado += montos_pagados[i]

            if total_monto_pagado < datos_monto_pago:
                meses_debe.append(mes)
                deuda_total += datos_monto_pago - total_monto_pagado

        meses_debe.append(f'S/Total: {deuda_total}')
        return meses_debe

    df['MesesDebe'] = df.apply(lambda row: obtener_meses_debe(row['Mes'], row['Monto'], row['Descripcion']), axis=1)
    
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
        apoderado_limpio = reemplazar_caracteres(apoderados.get('Apoderado'))
        direccion_limpia = reemplazar_caracteres(direcciones.get('Direccion'))
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
            'Apoderado': apoderado_limpio,
            'Direccion': direccion_limpia,
            'Monto': [p.Monto for p in pagos if p.Dni == dni],
            'Descripcion': [p.descripcion for p in pagos if p.Dni == dni],
        }
        resultados.append(combinado)
    cursor1.close()
    cursor2.close()

    return resultados


"""En esta función solo obtiene del sistema de facturación porque solo importa los matriculados"""
def obtener_matriculados(fecha1,fecha2):
    try:
        cursor, connection= conexion_cursor()
        cursor.execute(
            """
            SELECT 
                vpm.Dni as 'Dni',
                CONCAT(vpm.apellido, ' ', vpm.nombre) as 'Alumno',
                vpm.Grado as 'Grado',
                vpm.Seccion as 'Seccion',
                vpm.Nivel as 'Nivel',
                vpm.Apoderado as 'Apoderado',
                vpm.Direccion as 'Direccion',
                vpm.Telefono as 'Telefono',
                vpm.FechaPago as 'FechaPago'
            FROM view_pagos_matriculas as vpm 
            WHERE vpm.Concepto = 'MATRICULA'
            AND vpm.FechaPago BETWEEN %s AND %s
            """,
            [fecha1, fecha2]  # Pasar las fechas como parámetros
        )
        matriculados = cursor.fetchall()  # Obtener los resultados
        return matriculados
    except Exception as e:
        print(f"Error al obtener matriculados: {e}")
        return []
    finally:
        # Asegurarse de cerrar el cursor y la conexión
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def conexion_cursor():
    resultados=[]
    connection = connections['facturacion']
    connection.ensure_connection()
    cursor = connection.connection.cursor(MySQLdb.cursors.DictCursor)

    return cursor,connection


def matriculados_index(request):
    return render(request,'matriculados/index.html')

def matriculados_filtro(request,fecha1,fecha2):
    try:
        # Validar formato de fecha
        fecha1 = datetime.strptime(fecha1, "%Y-%m-%d").date()
        fecha2 = datetime.strptime(fecha2, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({"error": "Formato de fecha inválido"}, status=400)

    # Obtener los matriculados con las fechas filtradas
    datos = obtener_matriculados(fecha1, fecha2)
    
    # Serializar los datos a JSON
    datos_corregidos=correccion_caracteres(datos)
    return JsonResponse(datos_corregidos, safe=False)

def correccion_caracteres(datos):
    mapeo_caracteres = {
            "Ã": "Á",
            "Ã‰": "É",
            "Ã": "Í",
            "Ã“": "Ó",
            "Ãš": "Ú",
            "Ã±": "ñ",
            "Ã‘": "Ñ",
            "Âª":"°",
            "Â°":"°"
    }

    datos_corregidos = []
    
    # Iterar sobre los datos y corregir los caracteres especiales solo en las columnas específicas
    for registro in datos:
        registro_corregido = registro.copy()  # Hacer una copia del registro original
        for columna in ["Alumno", "Apoderado", "Direccion"]:
            if columna in registro:
                valor = registro[columna]
                for clave, reemplazo in mapeo_caracteres.items():
                    valor = valor.replace(clave, reemplazo)
                registro_corregido[columna] = valor  # Actualizar solo el campo corregido
        datos_corregidos.append(registro_corregido)

    return datos_corregidos



def reset_numero_cartas(request):
    try:
        CartasEnviadas.objects.all().update(numero_carta=0)
        return JsonResponse({'success': True, 'message': 'Números reseteados correctamente'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})