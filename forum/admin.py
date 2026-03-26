from django.contrib import admin
from .models import Category, Topic, Message, Complaint

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'created_at')
    list_filter = ('category',)

# Сообщения и жалобы регистрируем простым способом
admin.site.register(Message)
admin.site.register(Complaint)