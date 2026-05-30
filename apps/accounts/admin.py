from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from apps.accounts.models import CustomUser, VerificationRecord, UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    readonly_fields = ('tasker_rating_avg', 'tasker_rating_count', 'client_rating_avg', 'client_rating_count', 'tasks_completed', 'tasks_published', 'tasks_cancelled')


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'full_name', 'role', 'is_verified', 'phone_verified', 'is_staff', 'date_joined')
    list_filter = ('role', 'is_verified', 'is_staff')
    search_fields = ('email', 'full_name', 'phone_number')
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informations', {'fields': ('full_name', 'phone_number', 'phone_verified', 'avatar', 'role', 'active_role', 'is_verified')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'phone_number', 'password1', 'password2', 'role'),
        }),
    )
    readonly_fields = ('last_login', 'date_joined')

    inlines = [UserProfileInline]


@admin.register(VerificationRecord)
class VerificationRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'face_status', 'is_used', 'created_at')
    list_filter = ('type', 'face_status', 'is_used')
    search_fields = ('user__full_name', 'user__email')
    date_hierarchy = 'created_at'
