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
        # url = blog.get_url() #可以公共抽取出来

    elif instance.content_type.model == 'comment':
        comment = instance.content_object
        verb = '{0}点赞了你的评论“{1}”'.format(instance.user.get_nickname_or_username(), strip_tags(comment.text))
        # url = comment.get_url() #在comment中新增get_url，其实也是获取这个博客的地址

    url = instance.content_object.get_url()  #但是这个url就没必要拼接做跳转，因为在消息中心就可以清晰看到是谁点赞了
    recipient = instance.content_object.get_user()

    # 参数分别表示的意思是：通知者，接收者，接受内容，这个消息是从哪个地方出发的
    notify.send(instance.user, recipient=recipient, verb=verb, action_object=instance, url=url)