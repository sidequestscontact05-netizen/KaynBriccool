from django.contrib import admin
from apps.reputation.models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('reviewer', 'reviewed', 'rating', 'review_type', 'created_at')
    list_filter = ('review_type', 'rating')
    search_fields = ('reviewer__full_name', 'reviewed__full_name', 'comment')
    date_hierarchy = 'created_at'
