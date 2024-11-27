from django.shortcuts import render,redirect
from django.contrib import messages
from django.http import JsonResponse

from appsettingsCartas.models import settingsCartas

def index(request):
    # Obtener el primer registro de la tabla settingsCartas si existe
    settings = settingsCartas.objects.first()

    # Pasar los valores al template
    context = {
        "dia": settings.Dia if settings else "",
        "mes": settings.Mes if settings else "",
        "ano": settings.Ano if settings else "",
        "estado": settings.Estado if settings else False,
    }
    print("mostrando datos")
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