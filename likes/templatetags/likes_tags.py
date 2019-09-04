from django import template
from django.contrib.contenttypes.models import ContentType
from ..models import LikeCount,LikeRecord

register = template.Library()

@register.simple_tag
def get_like_count(obj):
    content_type = ContentType.objects.get_for_model(obj)
    like_count,created =  LikeCount.objects.get_or_create(content_type=content_type, object_id=obj.pk)
    return like_count.liked_num


#(takes_context=True)和context是为了获取user信息的，这个跟setting设置模板有关，有些导入的默认模板就带有user信息，比如之前说过的auth。当然，我们也可以通过前端传过来user信息
@register.simple_tag(takes_context=True)
def get_like_status(context, obj):
    content_type = ContentType.objects.get_for_model(obj)
    user = context['user']

    #如果用户没登录，那点赞的红色就不要激活
    if not user.is_authenticated:
        return ''

    #如果获取到用户已经点赞过，那就返回给前端active,让前端去改变点赞的样式
    if LikeRecord.objects.filter(content_type=content_type, object_id=obj.pk, user=context['user']).exists():
        return 'active'
    else:
        return ''


@register.simple_tag
def get_content_type(obj):
    content_type = ContentType.objects.get_for_model(obj)
    return content_type