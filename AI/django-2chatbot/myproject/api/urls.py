from django.contrib import admin
from django.urls import path, include
from api import views
from .views import *
from rest_framework import routers

router = routers.DefaultRouter()
# router.register(r'chat', chatAPIViews, basename='chat')

urlpatterns = [
    # path('', views.query_view, name='query_view'),
    path('', include(router.urls)),
    path('coverletter/', coverletterAPI.as_view(), name='coverletter'),
    path('chat/', chatAPI.as_view(), name='chat'),
    path('chatbot/', chatbotAPI.as_view(), name='chatbot'),
]