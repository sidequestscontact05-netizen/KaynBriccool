from django.urls import path
from apps.reputation import views

app_name = 'reputation'

urlpatterns = [
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('client/<int:client_id>/', views.client_profile, name='client_profile'),
    path('task/<uuid:task_id>/review-client/', views.tasker_review_client, name='tasker_review_client'),
]
