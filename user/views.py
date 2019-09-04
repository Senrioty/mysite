import string
import random
import time

from django.shortcuts import render,redirect
from django.contrib.contenttypes.fields import ContentType
from django.utils import timezone
from django.db.models import Sum
from django.core.cache import cache
from django.contrib import auth
from django.contrib.auth.models import User
from django.http import JsonResponse

from read_statistics.utils import get_seven_days_read_data,get_today_hot_data,get_yesterday_hot_data,get_7_days_hot_data
from blog.models import Blog
from django.urls import reverse
from django.core.mail import send_mail
from .forms import LoginForm,RegForm,ChangeNicknameForm,BindEmailForm,ChangePasswordForm,ForgetPasswordForm
from .models import Profile


def login(request):
    #这里是html处理表单的代码
    # username = request.POST.get('username')
    # password = request.POST.get('password')
    #
    # #这里使用auth.方法的原因是导入的本来是from django.contrib.auth import login,但是方法名login冲突了,所以改为导入from django.contrib import auth
    # user = auth.authenticate(request, username=username, password=password)
    #
    # #request.META这个是请求头，然后获取HTTP_REFERER这个键的值，如果没有则返回reverse('home')
    # #也就是说在评论页登录时，应该跳转到评论页而不是首页
    # #reverse('home')：是用反向解析的方式，找到对应'home'的路径，此处为'/'
    # referer = request.META.get('HTTP_REFERER', reverse('home'))
    #
    # if user is not None:
    #     auth.login(request, user)
    #     return redirect(referer)
    # else:
    #     return render(request, 'error.html', {'message':'用户名或者密码不正确'})

    #django form 表单提交代码
    #根据请求里的方法判断是提交登录的数据(POST)还是加载空页面(GET)
    if request.method == 'POST':
        login_form = LoginForm(request.POST) #获取POST提交过来的数据(字典类型)
        if login_form.is_valid():
            '''
            把这块验证放入到Form表单中做，通过clean_data[‘user’]来获取user对象
            '''
            # username = login_form.cleaned_data['username']
            # password = login_form.cleaned_data['password']
            # user = auth.authenticate(request, username=username, password=password)  #获取user对象
            # if user is not None:
            #     auth.login(request, user)
            #     #从请求里获取GET的数据，再从数据中获取from对应的数据，即为跳转过来的地址，可能from对应的数据没有，那就跳转到首页
            #     return redirect(request.GET.get('from',reverse('home')))
            # else:
            #     #添加到错误集，由于我们不知道到底是用户名还是密码错，所以填None
            #     login_form.add_error(None, '用户名或密码不正确')

            #使用Form表单优化的结果
            user = login_form.cleaned_data['user']
            auth.login(request, user)
            return redirect(request.GET.get('from',reverse('home')))


        '''
        验证不通过的话，login_form也会携带错误信息，但是代码重复了
        '''
        # else:
        #     context = {}
        #     context['login_form'] = login_form
        #     return render(request, 'login.html', context)

    else:
        login_form = LoginForm()

    context = {}
    context['login_form'] = login_form
    return  render(request, 'user/login.html', context)


def login_for_modal(request):
    login_form = LoginForm(request.POST)
    data = {}
    if login_form.is_valid():
        user = login_form.cleaned_data['user']
        auth.login(request, user)
        data['status'] = 'SUCCESS'
    else:
        data['status'] = 'ERROR'
    return JsonResponse(data)


def register(request):
    if request.method == 'POST':
        reg_form = RegForm(request.POST, request=request)
        if reg_form.is_valid():
            username = reg_form.cleaned_data['username']
            email = reg_form.cleaned_data['email']
            password = reg_form.cleaned_data['password']

            #初始化user对象方式一
            # user = User()
            # user.username = username
            # user.email = email
            # user.set_password(password)

            #初试化user对象方式二
            user = User.objects.create_user(username, email, password)

            user.save()

            #清除session
            del request.session['register_code']

            #登录用户
            user = auth.authenticate(username=username, password=password)
            auth.login(request, user)
            return redirect(request.GET.get('from'),reverse('home'))

    else:
        reg_form = RegForm()

    context = {}
    context['reg_form'] = reg_form
    return render(request, 'user/register.html', context)


def logout(request):
    auth.logout(request)
    return redirect(request.GET.get('from', reverse('home')))


def user_info(request):
    context = {}
    return render(request, 'user/user_info.html', context)


def change_nickname(request):
    redirect_to = request.GET.get('from', reverse('home'))

    if request.method == 'POST':
        form = ChangeNicknameForm(request.POST, user=request.user)
        if form.is_valid():
            nickname_new = form.cleaned_data['nickname_new']
            profile, created = Profile.objects.get_or_create(user=request.user)
            profile.nickname = nickname_new
            profile.save()
            return redirect(redirect_to)
    else:
        form = ChangeNicknameForm()

    context = {}
    context['form'] = form
    context['page_title'] = '修改昵称'
    context['form_title'] = '修改昵称'
    context['submit_text'] = '修改'
    context['return_back_url'] = redirect_to
    return render(request, 'form.html', context)


def bind_email(request):
    redirect_to = request.GET.get('from', reverse('home'))

    if request.method == 'POST':
        form = BindEmailForm(request.POST, request=request)
        if form.is_valid():
            email = form.cleaned_data['email']
            request.user.email = email
            request.user.save()

            #清除session
            del request.session['bind_email_code']

            return redirect(redirect_to)
    else:
        form = BindEmailForm()

    context = {}
    context['form'] = form
    context['page_title'] = '绑定邮箱'
    context['form_title'] = '绑定邮箱'
    context['submit_text'] = '绑定'
    context['return_back_url'] = redirect_to
    return render(request, 'user/bind_email.html', context)


def send_verification_code(request):
    email = request.GET.get('email', '')
    send_for = request.GET.get('send_for', '')
    data = {}

    if email != '':
        #生成验证码
        code = ''.join(random.sample(string.ascii_letters + string.digits,4))
        now = int(time.time())
        send_code_time = request.session.get('send_code_time', 0)
        if now - send_code_time < 30:
            data['status'] = 'ERROR'
        else:
            request.session[send_for] = code
            request.session['send_code_time'] = now

            send_mail(
                '绑定邮箱',
                '验证码:%s' % code,
                '642340273@qq.com',
                [email],
                fail_silently=False,
            )

            data['status'] = 'SUCCESS'
    else:
        data['status'] = 'ERROR'

    return JsonResponse(data)


def change_password(request):
    redirect_to = reverse('home')

    if request.method == 'POST':
        form = ChangePasswordForm(request.POST, user=request.user)
        if form.is_valid():
            user = request.user
            new_password = form.cleaned_data['new_password']
            user.set_password(new_password)  #注意设置密码不能user.password，因为要加密，要调用方法set_password
            user.save()
            auth.logout(request)  #修改完后最好退出一下
            return redirect(redirect_to)
    else:
        form = ChangePasswordForm()

    context = {}
    context['form'] = form
    context['page_title'] = '修改密码'
    context['form_title'] = '修改密码'
    context['submit_text'] = '修改'
    context['return_back_url'] = redirect_to
    return render(request, 'form.html', context)


def forget_password(request):
    redirect_to = reverse('login')

    if request.method == 'POST':
        form = ForgetPasswordForm(request.POST, request=request)
        if form.is_valid():
            email = form.cleaned_data['email']
            new_password = form.cleaned_data['new_password']
            user = User.objects.get(email=email)
            user.email = email
            user.set_password(new_password)
            user.save()

            #清除session
            del request.session['forget_password_code']

            return redirect(redirect_to)
    else:
        form = ForgetPasswordForm()

    context = {}
    context['form'] = form
    context['page_title'] = '重置密码'
    context['form_title'] = '重置密码'
    context['submit_text'] = '重置'
    context['return_back_url'] = redirect_to
    return render(request, 'user/forget_password.html', context)