import threading
from django.db.models.signals import post_save
from django.dispatch import receiver
from notifications.signals import notify
from django.utils.html import strip_tags
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .models import Comment


#sender发送者是Comment,触发方法是save是
@receiver(post_save, sender=Comment)
def send_notification(sender, instance, **kwargs):
    # 发送站内消息
    if instance.reply_to is None:
        # 评论
        recipient = instance.content_object.get_user()
        if instance.content_type.model == 'blog':
            blog = instance.content_object
            verb = '{0}评论了你的博客《{1}》'.format(instance.user.get_nickname_or_username(), blog.title)
            # url = blog.get_url() #发现与下面else里的get_url一样，都是博客，所以可以提取公共
        else:
            raise Exception('unkown comment object type')
    else:
        # 回复,其中strip_tags是为了去除html标签
        recipient = instance.reply_to
        verb = '{0}回复了你的评论“{1}”'.format(instance.user.get_nickname_or_username(), strip_tags(instance.parent.text))
        # url = instance.content_object.get_url() #因为回复也是要跳转到相应的博客

    # 需要拼接url，因为要跳转到相应的位置，需要注意的是，instance.pk这个是数值类型，而我们拼接是string类型，不能自动转换，所以要str()
    url = instance.content_object.get_url() + '#comment_' + str(instance.pk)

    # 参数分别表示的意思是：通知者，接收者，接受内容，这个消息是从哪个地方出发的
    # 最后一个url是自定义的，因为这个send支持传**kward,然后会保存到一个data的字段中，这个字段是json类型
    notify.send(instance.user, recipient=recipient, verb=verb, action_object=instance, url=url)


# 创建发送邮件的多线程
class SendEmail(threading.Thread):
    def __init__(self, subject, text, email, fail_silently=False):
        self.subject = subject
        self.text = text
        self.email = email
        self.fail_silently = fail_silently
        threading.Thread.__init__(self)

    def run(self):
        # 把耗时操作放到多线程中
        send_mail(
            self.subject,
            '',
            settings.EMAIL_HOST_USER,
            [self.email],
            fail_silently=self.fail_silently,
            html_message=self.text
        )

#把邮箱的发送也从Comment的models里分离处理
@receiver(post_save, sender=Comment)
def send_email(sender, instance, **kwargs):
    if instance.parent is None:
        subject = '有人评论了你的博客'
        email = instance.content_object.get_email()
    else:
        subject = '有人回复了你的评论'
        email = instance.reply_to.email

    if email != '':
        # text = self.text + '\n' + self.content_object.get_url()

        # 把html的标签去掉，方式一，只适用于简单的html内容，如果html内容复杂的话，那我们格式化字符串就很复杂
        # text = '%s\n<a href="%s">%s</a>' % (self.text, self.content_object.get_url(), '点击查看')

        # 方式二，如果有个文件，已经填写好html代码，而我们只需要根据key传值就可以填充html代码，那就很方便
        context = {}
        context['comment_text'] = instance.text
        context['url'] = instance.content_object.get_url()
        text = render_to_string('comment/send_email.html', context)
        send_email = SendEmail(subject, text, email)
        send_email.start()  # 通过start方法来启动多线程

    # # 方式二:使用异步来发送邮件
    # instance.send_email()