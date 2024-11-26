from django.urls import path
from appMetricas.views import *
urlpatterns = [
    path("index/", index , name="appmetricas"),
    path("deudores/obtener/<plantilla>/<meses>", obtener_deudores , name="appobtener_deudores"),
    path("puntuales/obtener/<plantilla>", obtener_puntuales , name="appobtener_puntuales"),
    path("numeros/cartas/", guardar_numeros_cartas , name="appguardarnumeros_cartas"),
    path('descargar/lista_deben', descargar_lista_deben, name='appdescargar_lista_deben'),
    path('descargar/lista_agradecimiento', descargar_lista_agradecimiento, name='appdescargar_lista_agradecimiento'),
    path('descargar_carpetas/', DescargarCarpetasView.as_view(), name='appdescargar_cartascobranza'),
    path('descargar_carpetas/', DescargarCarpetasView.as_view(), name='appdescargar_cartasnotariales'), 
    path('descargar_carpetas_agradecimiento/', DescargarCarpetasAgradecimientoView.as_view(), name='appdescargar_agradecimiento'),


]
