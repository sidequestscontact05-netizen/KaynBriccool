from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from apps.accounts.models import CustomUser, VerificationRecord, UserProfile, Skill, DeletionRequest


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    readonly_fields = ('tasker_rating_avg', 'tasker_rating_count', 'client_rating_avg', 'client_rating_count', 'tasks_completed', 'tasks_published', 'tasks_cancelled')
    filter_horizontal = ('skills',)
    fieldsets = (
        ('Zone', {'fields': ('city', 'service_radius')}),
        ('Compétences', {'fields': ('skills',)}),
        ('Statistiques', {'fields': ('xp', 'level', 'tasks_completed', 'tasks_published', 'tasks_cancelled')}),
        ('Notation', {'fields': ('tasker_rating_avg', 'tasker_rating_count', 'client_rating_avg', 'client_rating_count')}),
    )


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


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user_full_name', 'city', 'service_radius', 'skills_list', 'xp', 'level', 'tasks_completed')
    list_filter = ('city', 'skills', 'level')
    search_fields = ('user__full_name', 'user__email', 'city')
    list_select_related = ('user',)

    def user_full_name(self, obj):
        return obj.user.full_name
    user_full_name.short_description = 'Utilisateur'
    user_full_name.admin_order_field = 'user__full_name'

    def skills_list(self, obj):
        skills = obj.skills.all()
        if not skills:
            return '-'
        return ', '.join(s.name for s in skills)
    skills_list.short_description = 'Compétences'

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('skills')

    fieldsets = (
        ('Zone', {'fields': ('city', 'service_radius', 'latitude', 'longitude')}),
        ('Compétences', {'fields': ('skills',)}),
        ('XP & Niveau', {'fields': ('xp', 'level')}),
        ('Statistiques', {'fields': ('tasks_completed', 'tasks_published', 'tasks_cancelled')}),
        ('Notation', {'fields': ('tasker_rating_avg', 'tasker_rating_count', 'client_rating_avg', 'client_rating_count')}),
    )


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'icon', 'user_count')
    list_filter = ('category',)
    search_fields = ('name',)

    def user_count(self, obj):
        return obj.userprofile_set.count()
    user_count.short_description = 'Utilisateurs'


@admin.register(DeletionRequest)
class DeletionRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'reasons_summary', 'created_at')
    list_filter = ('role', 'created_at')
    readonly_fields = ('user', 'role', 'reasons', 'other_text', 'created_at')

    def reasons_summary(self, obj):
        return ', '.join(obj.reasons[:3]) + ('...' if len(obj.reasons) > 3 else '')
    reasons_summary.short_description = 'Raisons'
