from django.urls import path
from appsettingsCartas.views import *

urlpatterns = [
    path("settings/index", index , name="appsettingsindex"),
    path("settings/notarial/save", save_setting , name="appsettingsnotarial_save"),
    
]