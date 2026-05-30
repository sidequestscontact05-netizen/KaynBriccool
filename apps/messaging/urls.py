from django.urls import path
from apps.messaging import views

app_name = 'messaging'

urlpatterns = [
    path('messages/', views.conversation_list, name='conversation_list'),
    path('messages/<uuid:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('messages/<uuid:conversation_id>/poll/', views.conversation_poll, name='conversation_poll'),
]
