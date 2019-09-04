from django import template
from django.contrib.contenttypes.models import ContentType
from ..models import Comment  #一个.代表当前目录，两个.代表上一级目录 相当于from comment.models import Comment
from ..forms import CommentForm


register = template.Library()

@register.simple_tag
def get_comment_count(obj):
    content_type = ContentType.objects.get_for_model(obj)
    comment_count = Comment.objects.filter(content_type=content_type, object_id=obj.pk).count()
    return comment_count


@register.simple_tag
def get_comment_form(obj):
    content_type = ContentType.objects.get_for_model(obj)
    #content_type.model 这个是获取字符串'blog'
    form = CommentForm(initial={'content_type': content_type.model, 'object_id': obj.pk, 'reply_comment_id': '0'})
    return form


@register.simple_tag
def get_comment_list(obj):
    content_type = ContentType.objects.get_for_model(obj)
    comments = Comment.objects.filter(content_type=content_type, object_id=obj.pk, parent=None)
    return comments.order_by('-comment_time')