from django.urls import path
from apps.accounts.admin_views import (
    admin_dashboard,
    admin_users,
    admin_user_detail,
    admin_ban_user,
    admin_delete_user,
    admin_verifications,
    admin_verify_face,
    admin_delete_face_photo,
    admin_delete_verification,
)
from apps.tasks.admin_views import (
    admin_categories,
    admin_create_category,
    admin_edit_category,
    admin_delete_category,
    admin_subcategories,
    admin_create_subcategory,
)
from apps.badges.admin_views import (
    admin_badges,
    admin_create_badge,
    admin_edit_badge,
)

app_name = 'admin_KaynBricool'

urlpatterns = [
    path('', admin_dashboard, name='dashboard'),
    path('users/', admin_users, name='users'),
    path('users/<int:user_id>/', admin_user_detail, name='user_detail'),
    path('users/<int:user_id>/ban/', admin_ban_user, name='ban_user'),
    path('users/<int:user_id>/delete/', admin_delete_user, name='delete_user'),
    path('verifications/', admin_verifications, name='verifications'),
    path('verifications/<uuid:verification_id>/', admin_verify_face, name='verify_face'),
    path('verifications/<uuid:verification_id>/delete-photo/<str:photo_name>/', admin_delete_face_photo, name='delete_face_photo'),
    path('verifications/<uuid:verification_id>/delete/', admin_delete_verification, name='delete_verification'),

    path('categories/', admin_categories, name='categories'),
    path('categories/create/', admin_create_category, name='create_category'),
    path('categories/<uuid:cat_id>/edit/', admin_edit_category, name='edit_category'),
    path('categories/<uuid:cat_id>/delete/', admin_delete_category, name='delete_category'),

    path('subcategories/', admin_subcategories, name='subcategories'),
    path('subcategories/create/', admin_create_subcategory, name='create_subcategory'),

    path('badges/', admin_badges, name='badges'),
    path('badges/create/', admin_create_badge, name='create_badge'),
    path('badges/<uuid:badge_id>/edit/', admin_edit_badge, name='edit_badge'),
]
