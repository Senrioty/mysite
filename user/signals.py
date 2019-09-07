from django.db.models.signals import post_save
from django.dispatch import receiver
from notifications.signals import notify
from .models import User


#sender发送者是LikeRecord,触发方法是save是
@receiver(post_save, sender=User)
def send_notification(sender, instance, **kwargs):
    # 这个if语句是为了判断是第一次新建触发的user save，而不是诸如修改密码或者绑定邮箱的user save
    if kwargs['created'] == True:
        verb = '注册成功，更多精彩等你发现'
        notify.send(instance.user, recipient=instance, verb=verb, action_object=instance)

