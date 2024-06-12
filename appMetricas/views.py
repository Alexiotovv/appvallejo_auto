from django.shortcuts import render
from django.db import connections
from django.db.utils import ConnectionDoesNotExist
from django.http import JsonResponse
import MySQLdb
import requests
from datetime import datetime as dt
import pandas as pd
import os
from appMain.models import *
from PIL import Image, ImageDraw, ImageFont
import platform

def index(request):
    return render(request, 'metricas/index.html')

def obtener_deudores(request):        

    vcmtos = {3:27, 4:30, 5:31, 6:28, 7:31, 8:29, 9:30, 10:31, 11:28, 12:20}
    #meses = {'MATRICULA': 0, 'MARZO': 3, 'ABRIL': 4, 'MAYO': 5, 'JUNIO': 6, 'JULIO': 7, 'AGOSTO': 8, 'SETIEMBRE': 9, 'OCTUBRE': 10, 'NOVIEMBRE': 11, 'DICIEMBRE': 12}
    
    fecha_actual = dt.now().date()
    mes_actual = dt.now().month

    fecha_vcmto = fecha_actual.replace(day=vcmtos[mes_actual])

    if fecha_actual < fecha_vcmto:
        mes_ultimo_vcmto = mes_actual - 1
    else:
        mes_ultimo_vcmto = mes_actual

    data = union_alumnos_pagos()
    ###########este bloque se repite en la otra función es para optimizar
    df = pd.DataFrame(data)
    
    # Lista de todos los meses de marzo a diciembre
    todos_los_meses = ['MARZO', 'ABRIL', 'MAYO', 'JUNIO', 'JULIO', 'AGOSTO', 'SETIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE']
    
    # Filtrar los meses hasta el último mes de vencimiento
    meses_hasta_ultimo_vencimiento = todos_los_meses[:mes_ultimo_vcmto - 2]  # -2 porque MARZO es el índice 0 y necesitamos hasta el mes anterior al último vencimiento

    # Función para obtener los meses que debe un alumno
    def obtener_meses_debe(meses_pagados,montos_pagados):
        # return [mes for mes in meses_hasta_ultimo_vencimiento if mes not in meses_pagados]
        meses_debe = []
        montos_debe = []
        for mes in meses_hasta_ultimo_vencimiento:
            if mes in meses_pagados:
                idx = meses_pagados.index(mes)
                monto_pagado = montos_pagados[idx]
                if monto_pagado < 250:
                    meses_debe.append(mes)
                    montos_debe.append(250 - monto_pagado)
            else:
                meses_debe.append(mes)
                montos_debe.append(250)
        return meses_debe, montos_debe
    
    # Aplicar la función a cada fila
    # df['MesesDebe'] = df['Mes'].apply(obtener_meses_debe) 
    df[['MesesDebe', 'MontosDebe']] = df.apply(lambda row: pd.Series(obtener_meses_debe(row['Mes'], row['Monto'])), axis=1)


    df = df[df['MesesDebe'].apply(len) > 0] #filtra solamente a los deudores que se quedan los que tienen meses

    ############cierre del bloque que se repite##########333
    
    generar_imagenes_cobranzas(df)

    df.to_excel('cobranzas/lista_deben.xlsx')

    resultado={'data':'success','message':'ok'}
    return JsonResponse(resultado,safe=False)


def generar_imagenes_cobranzas(df):

    fecha_actual = dt.now().strftime('%Y-%m-%d_%H-%M-%S')
    
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

    
    if platform.system() == 'Windows':
        # Rutas para Windows
        font_path = "C:/Windows/Fonts/DejaVuSans-Bold.ttf"
        font_path_numero = "C:/Windows/Fonts/DejaVuSans.ttf"
    else:
        # Rutas para Linux
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        font_path_numero = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

    # font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    # font_path_numero = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    print("fooooooooooooooooooooooooooont"....+str(font_path))
    font = ImageFont.truetype(font_path, 20)
    font_carta=ImageFont.truetype(font_path_numero, 38)

    cartasenviadas=CartasEnviadas.objects.all()

    cartasenviadas_dict={cartas.dni_alumno:cartas.numero_carta for cartas in cartasenviadas}

    
    for index, row in df.iterrows():
        #usamos la imagen
        imagen = Image.open('cobranzas/plantilla_cobranza_2024.jpg')
        d = ImageDraw.Draw(imagen)

        alumno_papel= f"{row['ApellidoPaterno']} {row['ApellidoMaterno']}, {row['Nombres']}"
        dni_alumno= f"{row['DNI']}"
        
        numero_carta_obtenida = cartasenviadas_dict.get(dni_alumno, 0)
         
        grado_papel=f"{row['Grado']}"
        seccion_papel =f"{row['Seccion']}"
        meses_debe_papel= f"{', '.join(row['MesesDebe'])}"
        # print(dni_alumno)
        # print(str(row['MontosDebe']))
        # print(str(row['MesesDebe']))
        # montos_debe_papel= f"{', '.join(str(row['MontosDebe']))}"
        cantidad_meses=meses_debe_papel.split(",")
        cantidad_meses=len(cantidad_meses)
        
        total_deuda=cantidad_meses*250
        direccion=f"{row['Direccion']}"
        
        padres_papel= f"{row['Apoderado']}"
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

        cadena_mal_codificada = padres_papel
        cadena_mal_codificada_dire = direccion

        padres_cadena_corregida = cadena_mal_codificada
        for mal_codificado, correctamente_codificado in mapeo_caracteres.items():
            padres_cadena_corregida = padres_cadena_corregida.replace(mal_codificado, correctamente_codificado)

        direccion_cadena_corregida = cadena_mal_codificada_dire
        for mal_codificado, correctamente_codificado in mapeo_caracteres.items():
            direccion_cadena_corregida = direccion_cadena_corregida.replace(mal_codificado, correctamente_codificado)


        meses={1:'Enero',2:'Febrero',3:'Marzo',4:'Abril',5:'Mayo',6:'Junio',7:'Julio',8:'Agosto',9:'Setiembre',10:'Octubre',11:'Noviembre',12:'Diciembre'}
        dia_papel=dt.now().day
        mes_papel=meses.get(dt.now().month)
        anhio_papel=dt.now().year
        fecha_actual_largo=str(dia_papel)+" de "+ str(mes_papel) + " del "+ str(anhio_papel)

        d.text((900,298), "N° "+ str(int(numero_carta_obtenida+1)), font=font_carta, fill=(0, 0, 0))
        d.text((230,425), padres_cadena_corregida, font=font, fill=(0, 0, 0))
        d.text((290,475), alumno_papel, font=font, fill=(0, 0, 0))
        d.text((430,528), grado_papel,font=font, fill=(0, 0, 0))
        d.text((520,528), "'"+seccion_papel+"'",font=font, fill=(0, 0, 0))
        d.text((330,635), meses_debe_papel+"  S/ "+ str(total_deuda)+".00  ",font=font, fill=(0, 0, 0))
        d.text((800,1225), fecha_actual_largo,font=font, fill=(0, 0, 0))
        d.text((305,580), direccion_cadena_corregida,font=font, fill=(0, 0, 0))

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

        cursor3 = connection.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor3.execute("SELECT person.numero_documento as 'Dni', person.address1 as 'Direccion' FROM person where person.address1 != '' ")
        direcciones = cursor3.fetchall()
        
        # #consumiendo la api del sistema de notas
        url = "https://colcoopcv.com/listar/matriculados/2024"
        alumnos = obtener_datos_de_api(url)
        print('datos obtenidos del sistema de notas.......................')
        if alumnos is None:
            return JsonResponse({"error": "No se pudieron obtener los datos de la API."}, status=500)

        
        apoderados_dict={str(apo['Dni']).strip(): apo for apo in apoderados}
        direcciones_dic={str(dire['Dni']).strip():dire for dire in direcciones}

        for alumno in alumnos:
            dni = str(alumno.get('Dni')).strip()
            apoderados=apoderados_dict.get(dni,{})
            direcciones=direcciones_dic.get(dni,{})
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
                'Mes': [p['Mes'] for p in pagos if p['Dni'] == dni],
                'Monto': [p['Monto'] for p in pagos if p['Dni'] == dni],
                # 'TipoIngreso': pago.get('TipoIngreso'),
                # 'ConceptoNumeroMes': pago.get('ConceptoNumeroMes'),
                # 'FechaVencimiento': pago.get('FechaVencimiento'),
                # 'LetraMesPago': pago.get('LetraMesPago'),
                # 'Atrasado': pago.get('Atrasado'),
                # 'DiasAtraso': pago.get('DiasAtraso'),
                # 'MesesAtraso': pago.get('MesesAtraso'),
                'Apoderado': apoderados.get('Apoderado'),
                'Direccion': direcciones.get('Direccion'),
            }

            resultados.append(combinado)
        print('union local con datos obtenidor terminada.........................')
        return resultados
        
    except ConnectionDoesNotExist:
        data = []
    finally:
        cursor.close()
        cursor2.close()
        cursor3.close()
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



def guardar_numeros_cartas(request):
    
    vcmtos = {3:27, 4:30, 5:31, 6:28, 7:31, 8:29, 9:30, 10:31, 11:28, 12:20}
    
    fecha_actual = dt.now().date()
    mes_actual = dt.now().month

    fecha_vcmto = fecha_actual.replace(day=vcmtos[mes_actual])

    if fecha_actual < fecha_vcmto:
        mes_ultimo_vcmto = mes_actual - 1
    else:
        mes_ultimo_vcmto = mes_actual

    data = union_alumnos_pagos()

    df = pd.DataFrame(data)
    todos_los_meses = ['MARZO', 'ABRIL', 'MAYO', 'JUNIO', 'JULIO', 'AGOSTO', 'SETIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE']
    
    meses_hasta_ultimo_vencimiento = todos_los_meses[:mes_ultimo_vcmto - 2]  # -2 porque MARZO es el índice 0 y necesitamos hasta el mes anterior al último vencimiento

    def obtener_meses_debe(meses_pagados):
        return [mes for mes in meses_hasta_ultimo_vencimiento if mes not in meses_pagados]

    df['MesesDebe'] = df['Mes'].apply(obtener_meses_debe)

    df = df[df['MesesDebe'].apply(len) > 0]
    lista_dnies = list(df['DNI'])

    cartas_a_actualizar = CartasEnviadas.objects.filter(dni_alumno__in=lista_dnies)

    for carta in cartas_a_actualizar:
        carta.numero_carta += 1
        carta.save()
    
    resultado={'data':'success','message':'ok'}
    return JsonResponse(resultado,safe=False)
