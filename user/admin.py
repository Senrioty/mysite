from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False


class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline, )
    #覆盖user要显示的列，其中nickname是自定义的，因为profile中与User做了一对一的关系，所以是可以通过user找到的
    list_display = ('username', 'nickname', 'email', 'is_staff', 'is_active', 'is_superuser')

    #自定义nickname，obj指代的是user对象
    def nickname(self, obj):
        return obj.profile.nickname
    nickname.short_description = '昵称' #在User的列显示中文


#重新注册User
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'nickname')