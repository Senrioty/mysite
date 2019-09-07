from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.html import strip_tags
from notifications.signals import notify
from .models import LikeRecord


#sender发送者是LikeRecord,触发方法是save是
@receiver(post_save, sender=LikeRecord)
def send_notification(sender, instance, **kwargs):
    if instance.content_type.model == 'blog':
        blog = instance.content_object
        verb = '{0}点赞了你的{1}'.format(instance.user.get_nickname_or_username(), blog.title)
    elif instance.content_type.model == 'comment':
        comment = instance.content_object
        verb = '{0}点赞了你的评论“{1}”'.format(instance.user.get_nickname_or_username(), strip_tags(comment.text))

    recipient = instance.content_object.get_user()

    # 参数分别表示的意思是：通知者，接收者，接受内容，这个消息是从哪个地方出发的
    notify.send(instance.user, recipient=recipient, verb=verb, action_object=instance)