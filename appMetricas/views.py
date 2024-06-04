from django.shortcuts import render
from django.db import connections
from django.db.utils import ConnectionDoesNotExist
from django.http import JsonResponse
import MySQLdb
import requests
from datetime import datetime as dt
import pandas as pd
import os
from PIL import Image, ImageDraw, ImageFont

def index(request):
    return render(request, 'metricas/index.html')

def obtener_deudores(request):        

    vcmtos = {3:27, 4:30, 5:31, 6:28, 7:31, 8:29, 9:30, 10:31, 11:28, 12:20}
    meses = {'MATRICULA': 0, 'MARZO': 3, 'ABRIL': 4, 'MAYO': 5, 'JUNIO': 6, 'JULIO': 7, 'AGOSTO': 8, 'SETIEMBRE': 9, 'OCTUBRE': 10, 'NOVIEMBRE': 11, 'DICIEMBRE': 12}
    
    fecha_actual = dt.now().date()
    mes_actual = dt.now().month

    fecha_vcmto = fecha_actual.replace(day=vcmtos[mes_actual])

    if fecha_actual < fecha_vcmto:
        mes_ultimo_vcmto = mes_actual - 1
    else:
        mes_ultimo_vcmto = mes_actual

    data = union_alumnos_pagos()
    df = pd.DataFrame(data)
    
    # Lista de todos los meses de marzo a diciembre
    todos_los_meses = ['MARZO', 'ABRIL', 'MAYO', 'JUNIO', 'JULIO', 'AGOSTO', 'SETIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE']
    
    # Filtrar los meses hasta el último mes de vencimiento
    meses_hasta_ultimo_vencimiento = todos_los_meses[:mes_ultimo_vcmto - 2]  # -2 porque MARZO es el índice 0 y necesitamos hasta el mes anterior al último vencimiento

    # Función para obtener los meses que debe un alumno
    def obtener_meses_debe(meses_pagados):
        return [mes for mes in meses_hasta_ultimo_vencimiento if mes not in meses_pagados]

    # Aplicar la función a cada fila
    df['MesesDebe'] = df['Mes'].apply(obtener_meses_debe)

    df = df[df['MesesDebe'].apply(len) > 0]

    print(df)
    generar_imagenes_cobranzas(df)

    resultado={'data':'success','message':'ok'}
    return JsonResponse(resultado,safe=False)


def generar_imagenes_cobranzas(df):
    
    fecha_actual = dt.now()
    
    if not os.path.exists('cobranzas/'+str(fecha_actual)+'/PRIMARIA/1°'):
        os.makedirs('cobranzas/'+str(fecha_actual)+'/PRIMARIA/1°')
    if not os.path.exists('cobranzas/'+str(fecha_actual)+'/PRIMARIA/2°'):
        os.makedirs('cobranzas/'+str(fecha_actual)+'/PRIMARIA/2°')
    if not os.path.exists('cobranzas/'+str(fecha_actual)+'/PRIMARIA/3°'):
        os.makedirs('cobranzas/'+str(fecha_actual)+'/PRIMARIA/3°')
    if not os.path.exists('cobranzas/'+str(fecha_actual)+'/PRIMARIA/4°'):
        os.makedirs('cobranzas/'+str(fecha_actual)+'/PRIMARIA/4°')
    if not os.path.exists('cobranzas/'+str(fecha_actual)+'/PRIMARIA/5°'):
        os.makedirs('cobranzas/'+str(fecha_actual)+'/PRIMARIA/5°')
    if not os.path.exists('cobranzas/'+str(fecha_actual)+'/PRIMARIA/6°'):
        os.makedirs('cobranzas/'+str(fecha_actual)+'/PRIMARIA/6°')
    
    if not os.path.exists('cobranzas/'+str(fecha_actual)+'/SECUNDARIA/1°'):
        os.makedirs('cobranzas/'+str(fecha_actual)+'/SECUNDARIA/1°')
    if not os.path.exists('cobranzas/'+str(fecha_actual)+'/SECUNDARIA/2°'):
        os.makedirs('cobranzas/'+str(fecha_actual)+'/SECUNDARIA/2°')
    if not os.path.exists('cobranzas/'+str(fecha_actual)+'/SECUNDARIA/3°'):
        os.makedirs('cobranzas/'+str(fecha_actual)+'/SECUNDARIA/3°')
    if not os.path.exists('cobranzas/'+str(fecha_actual)+'/SECUNDARIA/4°'):
        os.makedirs('cobranzas/'+str(fecha_actual)+'/SECUNDARIA/4°')
    if not os.path.exists('cobranzas/'+str(fecha_actual)+'/SECUNDARIA/5°'):
        os.makedirs('cobranzas/'+str(fecha_actual)+'/SECUNDARIA/5°')

    
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    #font_path = "C:/Windows/Fonts/arial.ttf"

    font = ImageFont.truetype(font_path, 20)


    for index, row in df.iterrows():
        #comentamos porque ya no dibujamos la imagen
        # imagen = Image.new('RGB', (1748, 2480), color=(255, 255, 255))
        # d = ImageDraw.Draw(imagen)

        #usamos la imagen
        imagen = Image.open('cobranzas/plantilla_cobranza_2024.jpg')
        d = ImageDraw.Draw(imagen)

        alumno_papel= f"{row['ApellidoPaterno']} {row['ApellidoMaterno']}, {row['Nombres']}"
        # DNI: {row['DNI']}
        grado_papel=f"{row['Grado']}"
        seccion_papel =f"{row['Seccion']}"
        meses_debe_papel= f"{', '.join(row['MesesDebe'])}"
            
        padres_papel= f"{row['Apoderado']}"
        
            

        d.text((230,425), padres_papel, font=font, fill=(0, 0, 0))
        d.text((290,475), alumno_papel, font=font, fill=(0, 0, 0))
        d.text((430,528), grado_papel,font=font, fill=(0, 0, 0))
        d.text((520,528), "'"+seccion_papel+"'",font=font, fill=(0, 0, 0))
        d.text((330,635), meses_debe_papel,font=font, fill=(0, 0, 0))


        nombre_alumno=(f"{row['ApellidoPaterno']} {row['ApellidoMaterno']}, {row['Nombres']}").strip()
        grado=row['Grado'][:1]+"°"
        seccion=row['Seccion']
        

        if row['Grado'][1:5]=='PRIM':
            if not os.path.exists('cobranzas/'+str(fecha_actual)+'/PRIMARIA/'+grado+'/'+seccion):
                os.makedirs('cobranzas/'+str(fecha_actual)+'/PRIMARIA/'+grado+'/'+seccion)

            image_path = f"cobranzas/{fecha_actual}/PRIMARIA/{grado}/{seccion}/{row['DNI']}_{nombre_alumno}.jpg"

        elif row['Grado'][1:4]=='SEC':
            if not os.path.exists('cobranzas/'+str(fecha_actual)+'/SECUNDARIA/'+grado+'/'+seccion):
                os.makedirs('cobranzas/'+str(fecha_actual)+'/SECUNDARIA/'+grado+'/'+seccion)

            image_path = f"cobranzas/{fecha_actual}/SECUNDARIA/{grado}/{seccion}/{row['DNI']}_{nombre_alumno}.jpg"

        imagen.save(image_path)

        # for num in numeros_telefonos:
        #     enviar_imagen_whatsapp(num[index], image_path)





def union_alumnos_pagos():
    resultados = []
    try:
        #conectandonos a la base de facturacion
        connection = connections['facturacion']
        connection.ensure_connection()
        cursor = connection.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM view_pagos vp")
        pagos = cursor.fetchall()

        cursor2 = connection.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor2.execute("SELECT person.numero_documento as 'Dni', person.email1 as 'Apoderado' FROM person where person.email1 != '' ")
        apoderados = cursor2.fetchall()
        
        # #consumiendo la api del sistema de notas
        url = "https://colcoopcv.com/listar/matriculados/2024"
        alumnos = obtener_datos_de_api(url)
        print('datos obtenidos del sistema de notas.......................')
        if alumnos is None:
            return JsonResponse({"error": "No se pudieron obtener los datos de la API."}, status=500)

        
        # #aqui codigo para mostrar solo registros
        # # Convertir los pagos en un diccionario con el DNI como clave para facilitar la búsqueda
        
        # Crear la lista combinada de alumnos con datos de pagos
        # pagos_dict = {str(pago['Dni']).strip(): pago for pago in pagos}
        apoderados_dict={str(apo['Dni']).strip(): apo for apo in apoderados}
        
        for alumno in alumnos:
            dni = str(alumno.get('Dni')).strip()
            apoderados=apoderados_dict.get(dni,{})
            # Combinar los datos de alumno y pago
            combinado = {
                'id': alumno.get('Id'),
                'DNI': alumno.get('Dni'),
                'ApellidoPaterno': alumno.get('ApellidoPaterno'),
                'ApellidoMaterno': alumno.get('ApellidoMaterno'),
                'Nombres': alumno.get('Nombres'),
                'TelefonoTutor': alumno.get('TelefonoTutor'),
                'Grado': alumno.get('Grado'),
                'Seccion': alumno.get('Seccion'),
                # Añadir campos de pagos (pueden ser nulos si no existen)
                # 'id_operacion': pago.get('id_operacion'),
                # 'id_persona': pago.get('id_persona'),
                # 'Monto': pago.get('Monto'),
                # 'FechaPago': pago.get('FechaPago'),
                # 'descripcion': pago.get('descripcion'),
                # 'Nivel': pago.get('Nivel'),
                # 'Grado': pago.get('Grado'),
                # 'Seccion': pago.get('Seccion'),
                # 'Concepto': pago.get('Concepto'),
                'Mes': [p['Mes'].upper() for p in pagos if p['Dni'] == dni] ,
                # 'TipoIngreso': pazgo.get('TipoIngreso'),
                # 'ConceptoNumeroMes': pago.get('ConceptoNumeroMes'),
                # 'FechaVencimiento': pago.get('FechaVencimiento'),
                # 'LetraMesPago': pago.get('LetraMesPago'),
                # 'Atrasado': pago.get('Atrasado'),
                # 'DiasAtraso': pago.get('DiasAtraso'),
                # 'MesesAtraso': pago.get('MesesAtraso'),
                'Apoderado': apoderados.get('Apoderado'),
            }

            resultados.append(combinado)
        print('union local con datos obtenidor terminada.........................')
        return resultados
        
    except ConnectionDoesNotExist:
        data = []
    finally:
        cursor.close()
        cursor2.close()
        connection.close()

def obtener_datos_de_api(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Esto generará una excepción si la solicitud no fue exitosa
        datos = response.json()  # Asumiendo que la respuesta es JSON
        return datos
    except requests.exceptions.HTTPError as errh:
        print("HTTP Error:", errh)
    except requests.exceptions.ConnectionError as errc:
        print("Error Connecting:", errc)
    except requests.exceptions.Timeout as errt:
        print("Timeout Error:", errt)
    except requests.exceptions.RequestException as err:
        print("Something went wrong:", err)
    return None        



