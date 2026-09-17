from django.urls import path
from .views import teste_api

urlpatterns = [
    path('teste/', teste_api, name='teste_api'),
]