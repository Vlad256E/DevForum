from django.contrib import admin
from .models import Category, Topic, Message, Complaint
from django.contrib import admin
from .models import AuditLog

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'created_at')
    list_filter = ('category',)

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'moderator', 'action_type', 'content_type', 'object_id')
    list_filter = ('action_type', 'timestamp', 'moderator')
    readonly_fields = ('timestamp', 'action_details')

# Сообщения и жалобы регистрируем простым способом
admin.site.register(Message)
admin.site.register(Complaint)