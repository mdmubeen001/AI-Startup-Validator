from django.urls import path 
from . import views 

urlpatterns =  [
    path('', views.home, name='home'),
    path('idea/', views.idea_form, name='idea_form'),
    path('result/', views.result_page, name='result_page'),
    path('compare/', views.compare_view, name='compare'),
    path('history/', views.history_view, name='history'),
    path('history/<int:idea_id>/', views.history_detail, name='history_detail'),
    path('download/',views.download_pdf,name='download_pdf'),

]