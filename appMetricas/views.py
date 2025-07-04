from django.shortcuts import render, redirect
from django.db import connections
from django.db.utils import ConnectionDoesNotExist
from django.http import JsonResponse,HttpResponse, FileResponse
import MySQLdb
import requests
from datetime import datetime as dt
import pandas as pd
import os
from appMain.models import *
from PIL import Image, ImageDraw, ImageFont
import platform
from django.conf import settings
import shutil
import datetime
from appsettingsCartas.models import settingsCartas, settingsDatos
from utils.text_utils import reemplazar_caracteres

datos_url=""
datos_ano_actual=""
datos_monto_pago=0

datos= settingsDatos.objects.first()
if datos:
    datos_url = datos.url
    datos_ano_actual = datos.ano_actual
    datos_monto_pago = datos.monto_pago
else:
    datos_url="https://colcoopcv.com/listar/matriculados/2025",
    datos_ano_actual = datetime.date.today().year,
    datos_monto_pago = 270


def index(request):
    return render(request, 'metricas/index.html')

def descargar_lista_deben(request):
    nombre_archivo = 'lista_deben.xlsx'
    ruta_archivo = os.path.join(settings.MEDIA_ROOT, nombre_archivo)
    # Validar que el archivo exista antes de descargar
    if os.path.exists(ruta_archivo):
        # Devolver una respuesta de redirección para descargar el archivo
        return redirect(settings.MEDIA_URL + nombre_archivo)
    else:
        # Manejar el caso donde el archivo no existe
        return HttpResponse("El archivo no existe")

def obtener_deudores(request, plantilla,meses):
    
    vcmtos = {3:31, 4:30, 5:31, 6:30, 7:31, 8:30, 9:30, 10:31, 11:29, 12:22}
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

        meses_debe.append(f'S/ {deuda_total}')
        return meses_debe
        

    df['MesesDebe'] = df.apply(lambda row: obtener_meses_debe(row['Mes'], row['Monto'], row['Descripcion']), axis=1)
    df = df[df['MesesDebe'].apply(len) > 1]
    meses = int(meses)
    df['MesesDebeTemp'] = df['MesesDebe']
    df['MesesDebeTemp'] = df['MesesDebeTemp'].apply(limpiar_meses)
    
    meses_nombres = {
        1: 'ENERO',
        2: 'FEBRERO',
        3: 'MARZO',
        4: 'ABRIL',
        5: 'MAYO',
        6: 'JUNIO',
        7: 'JULIO',
        8: 'AGOSTO',
        9: 'SETIEMBRE',
        10: 'OCTUBRE',
        11: 'NOVIEMBRE',
        12: 'DICIEMBRE'
    }

    if plantilla == 'notarial':
        # Filtrar los meses que comienzan desde el mes indicado en adelante
        if meses in meses_nombres:
            mes_inicio = meses_nombres[meses]  # Obtener el nombre del mes correspondiente
            
            # Filtrar filas donde MesesDebeTemp comience exactamente desde `mes_inicio`
            df = df[df['MesesDebeTemp'].apply(lambda x: x[0] == mes_inicio)]
        
    ############cierre del bloque que se repite##########333
    
        
    borrar_carpetas_media()
    generar_imagenes_cobranzas(df,plantilla,meses)

    df['Apoderado'] = df['Apoderado'].apply(reemplazar_caracteres)
    df['Direccion'] = df['Direccion'].apply(reemplazar_caracteres)
    
    # Crea un nombre de archivo único con fecha y hora
    fecha_hora = dt.now().strftime("%Y%m%d_%H%M%S")
    nombre_archivo = f'lista_deben_{fecha_hora}.xlsx'
    ruta_archivo = os.path.join(settings.MEDIA_ROOT, nombre_archivo)
    df.to_excel(ruta_archivo,index=False)

    # Construir la URL pública para descarga
    url_archivo = f"{settings.MEDIA_URL}{nombre_archivo}"

    return JsonResponse({'data': 'success', 'message': 'ok', 'file_url': url_archivo})

def limpiar_meses(meses_debe):
    # Filtra solo los meses (eliminando cualquier valor que no sea mes)
    meses_validos = ['MARZO', 'ABRIL', 'MAYO', 'JUNIO', 'JULIO', 'AGOSTO', 'SETIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE']
    meses_debe = [mes for mes in meses_debe if mes.upper() in meses_validos]
    return meses_debe

def generar_imagenes_cobranzas(df,plantilla,meses):
    imagenes_por_carpeta = {}

    fecha_actual = dt.now().strftime('%Y-%m-%d_%H-%M-%S')
    
    if not os.path.exists('media/'+str(fecha_actual)+'/PRIMARIA/1°'):
        os.makedirs('media/'+str(fecha_actual)+'/PRIMARIA/1°')
    if not os.path.exists('media/'+str(fecha_actual)+'/PRIMARIA/2°'):
        os.makedirs('media/'+str(fecha_actual)+'/PRIMARIA/2°')
    if not os.path.exists('media/'+str(fecha_actual)+'/PRIMARIA/3°'):
        os.makedirs('media/'+str(fecha_actual)+'/PRIMARIA/3°')
    if not os.path.exists('media/'+str(fecha_actual)+'/PRIMARIA/4°'):
        os.makedirs('media/'+str(fecha_actual)+'/PRIMARIA/4°')
    if not os.path.exists('media/'+str(fecha_actual)+'/PRIMARIA/5°'):
        os.makedirs('media/'+str(fecha_actual)+'/PRIMARIA/5°')
    if not os.path.exists('media/'+str(fecha_actual)+'/PRIMARIA/6°'):
        os.makedirs('media/'+str(fecha_actual)+'/PRIMARIA/6°')
    
    if not os.path.exists('media/'+str(fecha_actual)+'/SECUNDARIA/1°'):
        os.makedirs('media/'+str(fecha_actual)+'/SECUNDARIA/1°')
    if not os.path.exists('media/'+str(fecha_actual)+'/SECUNDARIA/2°'):
        os.makedirs('media/'+str(fecha_actual)+'/SECUNDARIA/2°')
    if not os.path.exists('media/'+str(fecha_actual)+'/SECUNDARIA/3°'):
        os.makedirs('media/'+str(fecha_actual)+'/SECUNDARIA/3°')
    if not os.path.exists('media/'+str(fecha_actual)+'/SECUNDARIA/4°'):
        os.makedirs('media/'+str(fecha_actual)+'/SECUNDARIA/4°')
    if not os.path.exists('media/'+str(fecha_actual)+'/SECUNDARIA/5°'):
        os.makedirs('media/'+str(fecha_actual)+'/SECUNDARIA/5°')

    font_path = os.path.join('fonts', 'DejaVuSans-Bold.ttf')
    font_path_numero = os.path.join( 'fonts', 'DejaVuSans.ttf')
    
    font = ImageFont.truetype(font_path, 20)
    font_meses_debe = ImageFont.truetype(font_path, 20)
    font_carta=ImageFont.truetype(font_path_numero, 38)

    cartasenviadas=CartasEnviadas.objects.all()

    cartasenviadas_dict={cartas.dni_alumno:cartas.numero_carta for cartas in cartasenviadas}
    
    meses_fecha={1:'Enero',2:'Febrero',3:'Marzo',4:'Abril',5:'Mayo',6:'Junio',7:'Julio',8:'Agosto',9:'Setiembre',10:'Octubre',11:'Noviembre',12:'Diciembre'}
    dia_papel=dt.now().day # Notarial
    mes_papel=meses_fecha.get(dt.now().month) # Notarial
    anhio_papel=dt.now().year # Notarial
    fecha_actual_largo=str(dia_papel)+" de "+ str(mes_papel) + " del "+ str(anhio_papel)

    if plantilla=='general':
        plantilla_cobranza=os.path.join(settings.MEDIA_ROOT, 'plantilla_cobranza_2024.jpeg')
    
    elif plantilla=='invitacion':
        plantilla_cobranza=os.path.join(settings.MEDIA_ROOT, 'plantilla_invitacion_salir_2024.jpeg')
    elif plantilla=='notarial':
        plantilla_cobranza=os.path.join(settings.MEDIA_ROOT, 'plantilla_carta_notarial_2024.jpeg')
        
        ##obtener fecha de carta Notarial de la base de datos
        fecha_notarial = settingsCartas.objects.first()
        
        if fecha_notarial and fecha_notarial.Estado == False:
            dia_papel=fecha_notarial.Dia
            mes_papel=fecha_notarial.Mes
            anhio_papel=fecha_notarial.Ano
            fecha_actual_largo=str(dia_papel)+" de "+ str(mes_papel) + " del "+ str(anhio_papel)
    
    cantidad_meses_recibido=int(meses)
    
    for index, row in df.iterrows():
        cantidad_meses_debe=int(len(row['MesesDebe'])-1)
        
        if plantilla=='invitacion':
            if cantidad_meses_debe >= cantidad_meses_recibido:
                pass
            else:
                continue
        elif plantilla=='general': 
            pass
        
        #usamos la imagen
        imagen = Image.open(plantilla_cobranza)
        d = ImageDraw.Draw(imagen)

        alumno_papel= f"{row['ApellidoPaterno']} {row['ApellidoMaterno']}, {row['Nombres']}" # Notarial|
        dni_alumno= f"{row['DNI']}"
        
        numero_carta_obtenida = cartasenviadas_dict.get(dni_alumno, 0)
         
        grado_papel=f"{row['Grado']}"
        seccion_papel =f"{row['Seccion']}"
        meses_debe_papel= f"{', '.join(row['MesesDebe'])}"
        meses_debe_papel=meses_debe_papel.replace(',', '-') # Notarial |
        direccion=f"{row['Direccion']}"
        
        padres_papel= f"{row['Apoderado']}" # Notarial|
        monto_deuda_acumulada = meses_debe_papel.split('-')[-1]
        # monto_deuda_acumulada = (cantidad_meses_debe-1)*250 # Notarial |
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


        if plantilla=='general':
            d.text((900,298), "N° "+ str(int(numero_carta_obtenida+1)), font=font_carta, fill=(0, 0, 0))
            d.text((230,425), padres_cadena_corregida, font=font, fill=(0, 0, 0))
            d.text((290,475), alumno_papel, font=font, fill=(0, 0, 0))
            d.text((430,528), grado_papel,font=font, fill=(0, 0, 0))
            d.text((520,528), "'"+seccion_papel+"'",font=font, fill=(0, 0, 0))
            d.text((330,635), meses_debe_papel,font=font, fill=(0, 0, 0))
            d.text((800,1225), fecha_actual_largo,font=font, fill=(0, 0, 0))
            d.text((305,580), direccion_cadena_corregida,font=font, fill=(0, 0, 0))
        elif plantilla=='invitacion':
            
            if 'PRIM' in grado_papel:
                nivel='PRIMARIA'
                img=os.path.join(settings.MEDIA_ROOT, 'firma_prim.jpeg')
                firma = Image.open(img)
            elif 'SEC' in grado_papel:
                nivel='SECUNDARIA'
                img=os.path.join(settings.MEDIA_ROOT, 'firma_sec.jpeg')
                firma = Image.open(img)
            
            imagen.paste(firma, (800, 1400))
            
            d.text((190,520), padres_cadena_corregida, font=font, fill=(0, 0, 0))
            d.text((190,630), alumno_papel, font=font, fill=(0, 0, 0))
            d.text((390,690), str(grado_papel[0])+str("°"),font=font, fill=(0, 0, 0))
            d.text((460,690), "'"+seccion_papel+"'",font=font, fill=(0, 0, 0))
            d.text((710,690), nivel,font=font, fill=(0, 0, 0))
            d.text((190,814), meses_debe_papel+str(".00"),font=font_meses_debe, fill=(0, 0, 0))
            d.text((855,1252), str(dia_papel),font=font, fill=(0, 0, 0))
        elif plantilla =='notarial':
            if 'PRIM' in grado_papel:
                nivel='PRIMARIA'
            if 'SEC' in grado_papel:
                nivel='SECUNDARIA'
            grado_completo = str(grado_papel[0])+str("° ") + seccion_papel + " " + nivel

            d.text((170,348), padres_cadena_corregida, font=font, fill=(0, 0, 0))
            d.text((170,577), alumno_papel+ "  "+grado_completo, font=font, fill=(0, 0, 0))
            
            #d.text((845,575), grado_completo, font=font, fill=(0, 0, 0))

            d.text((170,635), str(monto_deuda_acumulada),font=font_meses_debe, fill=(0, 0, 0))
            meses_debe_papel = '-'.join(meses_debe_papel.split('-')[:-1])
            d.text((170,664), meses_debe_papel,font=font_meses_debe, fill=(0, 0, 0))
            

            d.text((845,1075), (str(dia_papel)+" de "+ str(mes_papel) +" del "+ str(anhio_papel)),font=font, fill=(0, 0, 0))
            # d.text((890,1070), str(mes_papel),font=font, fill=(0, 0, 0))
            # d.text((1060,1070), str(anhio_papel),font=font, fill=(0, 0, 0))

        nombre_alumno=(f"{row['ApellidoPaterno']} {row['ApellidoMaterno']}, {row['Nombres']}").strip()
        grado=row['Grado'][:1]+"°"
        seccion=row['Seccion']
        
        if row['Grado'][1:5]=='PRIM':
            if not os.path.exists('media/'+str(fecha_actual)+'/PRIMARIA/'+grado+'/'+seccion):
                os.makedirs('media/'+str(fecha_actual)+'/PRIMARIA/'+grado+'/'+seccion)

            image_path = f"media/{fecha_actual}/PRIMARIA/{grado}/{seccion}/{row['DNI']}_{nombre_alumno}.jpg"

        elif row['Grado'][1:4]=='SEC':
            if not os.path.exists('media/'+str(fecha_actual)+'/SECUNDARIA/'+grado+'/'+seccion):
                os.makedirs('media/'+str(fecha_actual)+'/SECUNDARIA/'+grado+'/'+seccion)

            image_path = f"media/{fecha_actual}/SECUNDARIA/{grado}/{seccion}/{row['DNI']}_{nombre_alumno}.jpg"

        imagen.save(image_path)

        # Obtener carpeta destino (sin el nombre del archivo)
        carpeta_destino = os.path.dirname(image_path)

        # Guardar la imagen en la lista correspondiente a la carpeta
        if carpeta_destino not in imagenes_por_carpeta:
            imagenes_por_carpeta[carpeta_destino] = []

        imagenes_por_carpeta[carpeta_destino].append(image_path)


    for carpeta, imagenes in imagenes_por_carpeta.items():
        imagenes_obj = [Image.open(img).convert('RGB') for img in imagenes]
        if imagenes_obj:
            pdf_path = os.path.join(carpeta, 'cobranzas.pdf')
            imagenes_obj[0].save(pdf_path, save_all=True, append_images=imagenes_obj[1:])

        
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
        url = datos_url
        alumnos = obtener_datos_de_api(url)
        
        if alumnos is None:
            return JsonResponse({"error": "No se pudieron obtener los datos de la API."}, status=500)

        
        apoderados_dict={str(apo['Dni']).strip():apo for apo in apoderados}
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
                'Mes': [p['Mes'].upper() for p in pagos if p['Dni'] == dni],
                'Monto': [p['Monto'] for p in pagos if p['Dni'] == dni],
                'Descripcion': [p['descripcion'] for p in pagos if p['Dni'] == dni],
                # 'TipoIngreso': pago.get('TipoIngreso'),
                # 'ConceptoNumeroMes': pago.get('ConceptoNumeroMes'),
                # 'FechaVencimiento': pago.get('FechaVencimiento'),
                # 'LetraMesPago': pago.get('LetraMesPago'),
                #'Atrasado': pago.get('Atrasado'),
                'Atrasado':[p['Atrasado'] for p in pagos if p['Dni'] == dni],
                # 'DiasAtraso': pago.get('DiasAtraso'),
                # 'MesesAtraso': pago.get('MesesAtraso'),
                'Apoderado': apoderados.get('Apoderado'),
                'Direccion': direcciones.get('Direccion'),
            }

            resultados.append(combinado)
        
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
    vcmtos = {3:31, 4:30, 5:31, 6:30, 7:31, 8:30, 9:30, 10:31, 11:29, 12:22}

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

from django.views.generic import View
import zipfile
def borrar_carpetas_media():
    # Obtener la ruta de la carpeta media desde settings.py
    media_root = settings.MEDIA_ROOT
    
    # Verificar que la ruta de la carpeta media esté configurada y exista
    if os.path.exists(media_root):
        # Recorrer todos los archivos y carpetas dentro de media
        for root, dirs, files in os.walk(media_root, topdown=False):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                if not (file_name.endswith('.jpeg') or file_name.endswith('.xlsx')):
                    os.remove(file_path)  # Eliminar archivo si no es .jpeg ni .xlsx
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                shutil.rmtree(dir_path)  # Eliminar carpeta y su contenido de manera recursiva
    else:
        print(f"La carpeta {media_root} no existe o no está configurada en settings.py.")


class DescargarCarpetasView(View):
    def get(self, request):
        # Ruta de la carpeta media
        media_root = settings.MEDIA_ROOT
        
        # Nombre del archivo ZIP que se va a descargar
        zip_filename = 'cartas_cobranza.zip'
        
        # Ruta completa del archivo ZIP
        zip_filepath = os.path.join(media_root, zip_filename)
        
        # Crear un archivo ZIP temporal para almacenar los archivos
        with zipfile.ZipFile(zip_filepath, 'w') as zip_file:
            # Recorrer las carpetas dentro de MEDIA_ROOT
            for dirpath, _, filenames in os.walk(media_root):
                # Ignorar la carpeta media raíz
                if dirpath != media_root:
                    # Agregar todos los archivos de la carpeta al ZIP
                    for filename in filenames:
                        file_path = os.path.join(dirpath, filename)
                        zip_file.write(file_path, os.path.relpath(file_path, media_root))
        
        # Preparar la respuesta HTTP para descargar el archivo ZIP
        response = HttpResponse(content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename={zip_filename}'
        
        # Leer el contenido del archivo ZIP y agregarlo a la respuesta
        with open(zip_filepath, 'rb') as zip_content:
            response.write(zip_content.read())
        
        # Eliminar el archivo ZIP temporal después de descargarlo
        os.remove(zip_filepath)
        
        return response
    
class DescargarCarpetasAgradecimientoView(View):
    def get(self, request):
        # Ruta de la carpeta media
        media_root = settings.MEDIA_ROOT

        # Nombre de la carpeta que se va a descargar
        carpeta_nombre = 'AGRADECIMIENTO'
        carpeta_ruta = os.path.join(media_root, carpeta_nombre)
        
        if not os.path.exists(carpeta_ruta):
            return HttpResponse(f"La carpeta '{carpeta_nombre}' no existe.", status=404)
        
        # Nombre del archivo ZIP que se va a descargar
        zip_filename = f'{carpeta_nombre}.zip'
        
        # Ruta completa del archivo ZIP
        zip_filepath = os.path.join(media_root, zip_filename)
        
        # Crear un archivo ZIP temporal para almacenar los archivos
        with zipfile.ZipFile(zip_filepath, 'w') as zip_file:
            # Recorrer la carpeta específica dentro de MEDIA_ROOT
            for dirpath, _, filenames in os.walk(carpeta_ruta):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    zip_file.write(file_path, os.path.relpath(file_path, media_root))
        
        # Preparar la respuesta HTTP para descargar el archivo ZIP
        response = HttpResponse(content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename={zip_filename}'
        
        # Leer el contenido del archivo ZIP y agregarlo a la respuesta
        with open(zip_filepath, 'rb') as zip_content:
            response.write(zip_content.read())
        
        # Eliminar el archivo ZIP temporal después de descargarlo
        os.remove(zip_filepath)
        
        return response

def obtener_puntuales(request,plantilla):    
    puntuales=obtener_datos_pagadores()
    generar_imagenes_puntuales(puntuales, plantilla)

    return JsonResponse({'resultado':'completado'}, safe=False)

def obtener_datos_pagadores():
    puntuales = union_alumnos_pagos()
    
    # Limpiar los datos
    for item in puntuales:
        # Eliminar el primer "SI" o "NO" en 'Atrasado' si existe
        if 'Atrasado' in item and item['Atrasado']:
            item['Atrasado'].pop(0)
        
        # Eliminar todas las ocurrencias de 'MATRICULA' en 'Mes'
        if 'Mes' in item:
            while 'MATRICULA' in item['Mes']:
                item['Mes'].remove('MATRICULA')

    # Filtrar solo los que tienen "NO" en todos los subelementos de 'Atrasado', que no estén vacíos y que hayan pagado hasta JUNIO
    meses_requeridos = {'MARZO', 'ABRIL', 'MAYO', 'JUNIO'}
    puntuales_filtrados = [
        item for item in puntuales 
        if item.get('Atrasado') and all(atrasado == 'NO' for atrasado in item['Atrasado']) 
        and set(meses_requeridos).issubset(set(item.get('Mes', [])))
    ]

    # Crear un nuevo array con solo los campos deseados
    puntuales_resultado = [
        {
            'DNI': item['DNI'],
            'Nombres': item['Nombres'],
            'ApellidoPaterno': item['ApellidoPaterno'],
            'ApellidoMaterno': item['ApellidoMaterno'],
            'Atrasado': item['Atrasado'],
            'Mes': item['Mes'],
            'Apoderado': item['Apoderado'],
            'Direccion': item['Direccion'],
            'Grado': item['Grado'],
            'Seccion': item['Seccion']
        }
        for item in puntuales_filtrados
    ]

    return puntuales_resultado

def generar_imagenes_puntuales(puntuales_resultado,plantilla):
    borrar_carpetas_media()
    fecha_actual = dt.now().strftime('%Y-%m-%d_%H-%M-%S')
    
    if not os.path.exists('media/'+'AGRADECIMIENTO/'+str(fecha_actual)+'/PRIMARIA'):
        os.makedirs('media/'+'AGRADECIMIENTO/'+str(fecha_actual)+'/PRIMARIA')
    if not os.path.exists('media/'+'AGRADECIMIENTO/'+str(fecha_actual)+'/SECUNDARIA'):
        os.makedirs('media/'+'AGRADECIMIENTO/'+str(fecha_actual)+'/SECUNDARIA')
    
    font_path = os.path.join('fonts', 'DejaVuSans-Bold.ttf')
    font_path_numero = os.path.join( 'fonts', 'DejaVuSans.ttf')
    
    font = ImageFont.truetype(font_path, 20)
    font_carta=ImageFont.truetype(font_path_numero, 38)

    
    if plantilla=='agradecimiento':
        plantilla_felicitacion=os.path.join(settings.MEDIA_ROOT, 'plantilla_felicitacion.jpeg')
    
    df_puntuales = pd.DataFrame(puntuales_resultado)

    for index, row in df_puntuales.iterrows():
        
        imagen = Image.open(plantilla_felicitacion)
        d = ImageDraw.Draw(imagen)

        alumno_papel= f"{row['ApellidoPaterno']} {row['ApellidoMaterno']}, {row['Nombres']}"
        #dni_alumno= f"{row['DNI']}"
        grado_papel=f"{row['Grado']}"
        seccion_papel =f"{row['Seccion']}"
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

        dia_papel=dt.now().day

            
        if 'PRIM' in grado_papel:
            nivel='PRIMARIA'
            img=os.path.join(settings.MEDIA_ROOT, 'firma_prim.jpeg')
            firma = Image.open(img)
        elif 'SEC' in grado_papel:
            nivel='SECUNDARIA'
            img=os.path.join(settings.MEDIA_ROOT, 'firma_sec.jpeg')
            firma = Image.open(img)
        
        imagen.paste(firma, (800, 1350))

        d.text((190,495), padres_cadena_corregida, font=font, fill=(0, 0, 0))
        d.text((190,605), alumno_papel, font=font, fill=(0, 0, 0))
        d.text((390,665), str(grado_papel[0])+str("°"),font=font, fill=(0, 0, 0))
        d.text((460,665), "'"+seccion_papel+"'",font=font, fill=(0, 0, 0))
        d.text((710,665), nivel,font=font, fill=(0, 0, 0))
        d.text((855,1062), str(dia_papel),font=font, fill=(0, 0, 0))
        #d.text((305,580), direccion_cadena_corregida,font=font, fill=(0, 0, 0))

        nombre_alumno=(f"{row['ApellidoPaterno']} {row['ApellidoMaterno']}, {row['Nombres']}").strip()
        grado=row['Grado'][:1]+"°"
        seccion=row['Seccion']
        
        if row['Grado'][1:5]=='PRIM':
            if not os.path.exists('media/'+'AGRADECIMIENTO/'+str(fecha_actual)+'/PRIMARIA'):
                os.makedirs('media/'+'AGRADECIMIENTO/'+str(fecha_actual)+'/PRIMARIA')
            image_path = f"media/AGRADECIMIENTO/{fecha_actual}/PRIMARIA/{grado}_{seccion}_{row['DNI']}_{nombre_alumno}.jpg"

        elif row['Grado'][1:4]=='SEC':
            
            if not os.path.exists('media/'+ 'AGRADECIMIENTO/'+str(fecha_actual)+'/SECUNDARIA'):
                os.makedirs('media/'+'AGRADECIMIENTO/'+str(fecha_actual)+'/SECUNDARIA')

            image_path = f"media/AGRADECIMIENTO/{fecha_actual}/SECUNDARIA/{grado}_{seccion}_{row['DNI']}_{nombre_alumno}.jpg"

        imagen.save(image_path)
    
def descargar_lista_agradecimiento(request):
    lista_exportar=obtener_datos_pagadores()
    df_lista=pd.DataFrame(lista_exportar)
    df_lista.to_excel('media/lista_agradecimiento.xlsx')

    nombre_archivo = 'lista_agradecimiento.xlsx'
    ruta_archivo = os.path.join(settings.MEDIA_ROOT, nombre_archivo)
    
    if os.path.exists(ruta_archivo):
        return redirect(settings.MEDIA_URL + nombre_archivo)
    else:
        return HttpResponse("El archivo no existe")
    

