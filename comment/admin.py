from django.contrib import admin
from .models import Comment

# Register your models here.
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    # 如果没有主键值，django默认会建一个主键，名为id
    list_display = ('id', 'content_object', 'text', 'comment_time', 'user', 'root', 'parent')
