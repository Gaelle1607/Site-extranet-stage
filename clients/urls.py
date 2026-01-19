from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    path('', views.connexion, name='connexion'),
    path('connexion/', views.connexion, name='connexion'),
    path('deconnexion/', views.deconnexion, name='deconnexion'),
    path('contact/', views.contact, name='contact'),
    path('profil/', views.profil, name='profil'),
    path('profil/mot-de-passe/', views.modifier_mot_de_passe, name='modifier_mot_de_passe'),
]
