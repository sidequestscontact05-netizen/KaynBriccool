from django.contrib import admin
from apps.messaging.models import Conversation, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('sender', 'content', 'created_at')
    fields = ('sender', 'content', 'created_at')


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('client', 'tasker', 'last_activity_at')
    list_filter = ('created_at',)
    search_fields = ('client__full_name', 'tasker__full_name')
    inlines = [MessageInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'sender', 'is_read', 'created_at')
    list_filter = ('is_read',)
