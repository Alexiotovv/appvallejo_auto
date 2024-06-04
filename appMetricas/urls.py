from django.urls import path
from appMetricas.views import *
urlpatterns = [
    path("index/", index , name="appmetricas"),
    path("deudores/obtener/", obtener_deudores , name="appobtener_deudores")
]
