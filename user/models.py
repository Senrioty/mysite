from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE) #因为是一对一的关系
    nickname = models.CharField(max_length=20, default='', verbose_name='昵称')

    def __str__(self):
        return '<Profile: %s for %s>' % (self.nickname, self.user.username)


#动态绑定方法,绑定到user,所以这个self就是user
def get_nickname(self):
    if Profile.objects.filter(user=self).exists():
        proflie = Profile.objects.get(user=self)
        return proflie.nickname
    else:
        return ''


def has_nickname(self):
    return Profile.objects.filter(user=self).exists()


def get_nickname_or_username(self):
    if Profile.objects.filter(user=self).exists():
        proflie = Profile.objects.get(user=self)
        return proflie.nickname
    else:
        return self.username


User.get_nickname = get_nickname
User.has_nickname = has_nickname
User.get_nickname_or_username = get_nickname_or_username