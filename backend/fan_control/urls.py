from django.urls import path
from . import views

urlpatterns = [
    path('', views.fan_control, name='fan_control'),
    path('video_feed/', views.video_feed, name='video_feed'),
    path('update_speed/', views.update_speed, name='update_speed'),
    path('toggle_power/', views.toggle_power, name='toggle_power'),
    
]