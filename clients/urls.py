from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    path('', views.connexion, name='connexion'),
    path('connexion/', views.connexion, name='connexion'),
    path('deconnexion/', views.deconnexion, name='deconnexion'),
]
