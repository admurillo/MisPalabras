from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('help', views.help_info, name='help'),
    path('mypage', views.my_page, name='my_page'),
    path('<str:name>', views.get_word, name='get_word'),
]
