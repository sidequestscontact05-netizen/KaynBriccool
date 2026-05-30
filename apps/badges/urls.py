from django.urls import path
from apps.badges import views

app_name = 'badges'

urlpatterns = [
    path('', views.badge_list, name='badge_list'),
    path('my-badges/', views.my_badges, name='my_badges'),
    path('<slug:badge_slug>/', views.badge_detail, name='badge_detail'),
]
