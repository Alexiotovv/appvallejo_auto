from django.urls import path
from appMetricas.views import *
urlpatterns = [
    path("index/", index , name="appmetricas"),
    path("deudores/obtener/<plantilla>/<meses>", obtener_deudores , name="appobtener_deudores"),
    path("numeros/cartas/", guardar_numeros_cartas , name="appguardarnumeros_cartas"),
    path('descargar/lista_deben', descargar_lista_deben, name='appdescargar_lista_deben'),
    path('descargar_carpetas/', DescargarCarpetasView.as_view(), name='appdescargar_cartascobranza'),


]
