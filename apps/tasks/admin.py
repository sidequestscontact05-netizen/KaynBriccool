from django.contrib import admin
from apps.tasks.models import Category, SubCategory, Task, TaskProof


class SubCategoryInline(admin.TabularInline):
    model = SubCategory
    extra = 1
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [SubCategoryInline]


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'slug', 'is_active')
    list_filter = ('is_active', 'category')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'client', 'status', 'reward', 'published_at', 'created_at')
    list_filter = ('status', 'category', 'subcategory')
    search_fields = ('title', 'description')
    date_hierarchy = 'created_at'


@admin.register(TaskProof)
class TaskProofAdmin(admin.ModelAdmin):
    list_display = ('task', 'tasker', 'client_review', 'submitted_at')
    list_filter = ('client_review',)
