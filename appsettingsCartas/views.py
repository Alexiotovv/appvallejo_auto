from django.shortcuts import render,redirect
from django.contrib import messages
from django.http import JsonResponse

from appsettingsCartas.models import settingsCartas, settingsDatos, SettingsVentaSincronizada
import datetime

def index(request):
    # Obtener el primer registro de la tabla settingsCartas si existe
    settings = settingsCartas.objects.first()
    settingsdatos = settingsDatos.objects.first()
    settingsventas = SettingsVentaSincronizada.objects.first()
    
    url = ""
    ano_actual = ""
    monto_pago = 0
    url_meses_no_paga = ""
    
    if settingsdatos:
        url = settingsdatos.url
        ano_actual = settingsdatos.ano_actual
        monto_pago = settingsdatos.monto_pago
        url_meses_no_paga = settingsdatos.url_meses_no_paga
    else:
        # Crear registro por defecto
        settingsdatos = settingsDatos.objects.create(
            url="https://colcoopcv.com/listar/matriculados/2025",
            ano_actual=datetime.date.today().year,
            monto_pago=270.00
        )
        # Usar el objeto creado
        url = settingsdatos.url
        ano_actual = settingsdatos.ano_actual
        monto_pago = settingsdatos.monto_pago
        url_meses_no_paga = settingsdatos.url_meses_no_paga

    # Pasar los valores al template
    context = {
        "dia": settings.Dia if settings else "",
        "mes": settings.Mes if settings else "",
        "ano": settings.Ano if settings else "",
        "estado": settings.Estado if settings else False,
        "url": url,
        "ano_actual": ano_actual,
        "monto_pago": monto_pago,
        "settingsventas": settingsventas,
        "url_meses_no_paga": url_meses_no_paga

    }
    print(context)
    return render(request, 'settings/index.html', context)

def save_setting(request):
    if request.method == "POST":
        # Obtener los datos del formulario
        estado = request.POST.get('estado_input')  # Convertir a booleano
        dia = request.POST.get('dia')
        mes = request.POST.get('mes')
        ano = request.POST.get('ano')

        if estado=='true':
            estado=True
        elif estado=='false':
            estado=False

        # Verificar si existe algún registro
        obj = settingsCartas.objects.first()

        if obj:
            # Actualizar registro existente
            obj.Dia = dia
            obj.Mes = mes
            obj.Ano = ano
            obj.Estado = estado
            obj.save()
            messages.success(request, "Registro actualizado exitosamente.")
        else:
            # Crear un nuevo registro
            settingsCartas.objects.create(Dia=dia, Mes=mes, Ano=ano, Estado=estado)
            messages.success(request, "Registro creado exitosamente.")

        # Redirigir de nuevo a la página del formulario
        return redirect('appsettingsindex')

    messages.error(request, "Método no permitido.")
    return redirect('appsettingsindex')

def save_settingdatos(request):
    if request.method == 'POST':
        # Obtener los datos enviados
        url = request.POST.get('url')
        ano_actual = request.POST.get('ano_actual')
        monto_pago = request.POST.get('monto_pago')
        url_meses_no_paga = request.POST.get('url_meses_no_paga')  # Nuevo campo
        
        # Guardar los datos
        settings = settingsDatos.objects.first()
        if settings:
            settings.url = url
            settings.ano_actual = ano_actual
            settings.monto_pago = monto_pago
            settings.url_meses_no_paga = url_meses_no_paga  # Nuevo campo
            settings.save()
        else:
            settings = settingsDatos.objects.create(
                url=url,
                ano_actual=ano_actual,
                monto_pago=monto_pago,
                url_meses_no_paga=url_meses_no_paga  # Nuevo campo
            )

        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

def guardar_configuracion_venta(request):
    if request.method == 'POST':
        url = request.POST.get('url')
        token = request.POST.get('token')

        config, _ = SettingsVentaSincronizada.objects.get_or_create(id=1)
        config.url = url
        config.token = token
        config.save()

        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)
