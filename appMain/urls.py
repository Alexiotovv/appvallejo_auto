from django.contrib import admin
from django.urls import path
from .views import *
from django.contrib.auth.decorators import login_required

from appMain.views import matriculados_index, matriculados_filtro, reset_numero_cartas

urlpatterns = [
    path('', index,name='home'),
    path("refrescar/datos/", refrescar_datos, name="apprefrescar.datos"),
    path("grafico/cantpagosnivel/", cant_pagos_nivel, name="appcantpagosnivel"),
    path("grafico/cantpagosmes/", cant_pagos_mes, name="appcantpagosmes"),
    path("lista/deudores/", descargar_deudores, name="appdescargardeudores"),
    path("cartas/enviadas/index", index_cartas_enviadas, name="appcartasenviadas"),
    path('cartasenviadas/actualizar/', actualizar_cartas_enviadas, name='appactualizar_carta'),    
    # path('salir/', salir,name='salir')
    #Matriculados
    path("matriculados/index", matriculados_index, name="appmatriculadosindex"),
    path("matriculados/filtro/<fecha1>/<fecha2>", matriculados_filtro, name="appmatriculadosfiltro"),
    path("settings/reset/cartas", reset_numero_cartas , name="appsettingsreset_cartas"),

]