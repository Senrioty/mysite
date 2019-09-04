import threading
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string


# Create your models here.

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


# 因为评论的内容可能涉及多种，比如评论博客、动态、公告等等，所以还是使用ContentType
class Comment(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    text = models.TextField()
    comment_time = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, related_name='comments', on_delete=models.CASCADE)

    #让外键指向自己，并且当不是子评论时，内容可以为空
    parent = models.ForeignKey('self', related_name='parent_comment', null=True, on_delete=models.CASCADE)

    #这个字段是为了存储该评论下的所有评论，方便查找，同理跟parent字段冲突，所以也要加related_name属性
    root = models.ForeignKey('self', related_name='root_comment', null=True, on_delete=models.CASCADE)

    #存放被回复的对象，方便前端获取，如果不是子评论，内容可以为空
    reply_to = models.ForeignKey(User, related_name='replies', null=True, on_delete=models.CASCADE)

    def send_email(self):
        if self.parent is None:
            subject = '有人评论了你的博客'
            email = self.content_object.get_email()
        else:
            subject = '有人回复了你的评论'
            email = self.reply_to.email

        if email != '':
            # text = self.text + '\n' + self.content_object.get_url()

            # 把html的标签去掉，方式一，只适用于简单的html内容，如果html内容复杂的话，那我们格式化字符串就很复杂
            #text = '%s\n<a href="%s">%s</a>' % (self.text, self.content_object.get_url(), '点击查看')

            # 方式二，如果有个文件，已经填写好html代码，而我们只需要根据key传值就可以填充html代码，那就很方便
            context = {}
            context['comment_text'] = self.text
            context['url'] = self.content_object.get_url()
            text = render_to_string('comment/send_email.html', context)
            send_email = SendEmail(subject, text, email )
            send_email.start() #通过start方法来启动多线程


    def __str__(self):
        return self.text

    #倒序排序
    class Meta:
        ordering = ['comment_time']