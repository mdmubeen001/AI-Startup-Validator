from django.urls import path 
from . import views 

urlpatterns =  [
    path('', views.home, name='home'),
    path('idea/', views.idea_form, name='idea_form'),
    path('result/', views.result_page, name='result_page'),
    path('download/',views.download_pdf,name='download_pdf'),

]