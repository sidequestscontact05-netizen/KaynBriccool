from django.urls import path
from apps.tasks import views

app_name = 'tasks'

urlpatterns = [
    path('tasks/', views.task_list, name='task_list'),
    path('tasks/create/', views.task_create, name='task_create'),
    path('tasks/<uuid:task_id>/', views.task_detail, name='task_detail'),
    path('tasks/<uuid:task_id>/edit/', views.task_edit, name='task_edit'),
    path('tasks/<uuid:task_id>/publish/', views.task_publish, name='task_publish'),
    path('tasks/<uuid:task_id>/apply/', views.task_apply, name='task_apply'),
    path('tasks/<uuid:task_id>/cancel/', views.task_cancel, name='task_cancel'),
    path('tasks/<uuid:task_id>/delete/', views.task_delete, name='task_delete'),
    path('tasks/<uuid:task_id>/workspace/', views.task_workspace, name='task_workspace'),
    path('tasks/<uuid:task_id>/start/', views.task_start, name='task_start'),
    path('tasks/<uuid:task_id>/review/', views.task_review_proof, name='task_review_proof'),
    path('tasks/<uuid:task_id>/evaluate/', views.task_evaluate, name='task_evaluate'),
    path('tasks/<uuid:task_id>/close/', views.task_close, name='task_close'),
    path('tasks/<uuid:task_id>/litige/resolve/', views.task_resolve_litige, name='task_resolve_litige'),
    path('tasks/<uuid:task_id>/choose/<uuid:application_id>/', views.task_choose_tasker, name='task_choose_tasker'),
    path('tasks/<uuid:task_id>/reject/<uuid:application_id>/', views.task_reject_application, name='task_reject_application'),
    path('tasks/<uuid:task_id>/application/<uuid:application_id>/cancel/', views.task_cancel_application, name='task_cancel_application'),
    path('client/dashboard/', views.client_dashboard, name='client_dashboard'),
    path('client/quests/', views.client_quests, name='client_quests'),
    path('tasker/dashboard/', views.tasker_dashboard, name='tasker_dashboard'),
    path('tasker/missions/', views.tasker_missions, name='tasker_missions'),
    path('tasks/<uuid:task_id>/save/', views.task_toggle_save, name='task_toggle_save'),
    path('tasker/profile/', views.tasker_profile, name='tasker_profile'),
    path('tasker/leaderboard/', views.tasker_leaderboard, name='tasker_leaderboard'),
    path('api/subcategories/<uuid:cat_id>/', views.get_subcategories, name='get_subcategories'),
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('notifications/<uuid:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
]
