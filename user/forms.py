from django import forms
from django.contrib import auth
from django.contrib.auth.models import User


class LoginForm(forms.Form):
    #label是页面要显示的名字，required是前端页面生成出来的属性（可以不写），widget使用forms.PasswordInput是让input便签的type为password
    # xxxInput是获取实例，所以可以使用()来填充网页想要的属性
    username_or_email = forms.CharField(label='用户名或邮箱',
                               required=True,
                               widget=forms.TextInput(
                                            attrs={'class':'form-control', 'placeholder':'请输入用户名或邮箱'}))
    password = forms.CharField(label='密码',
                               widget=forms.PasswordInput(
                                            attrs={'class':'form-control', 'placeholder':'请输入密码'}))

    # 重写clean方法，验证用户名密码函数
    def clean(self):
        username_or_email = self.cleaned_data['username_or_email']
        password = self.cleaned_data['password']

        user = auth.authenticate(username=username_or_email, password=password)
        if user is None:
            if User.objects.filter(email=username_or_email).exists():
                username = User.objects.get(email=username_or_email).username
                user = auth.authenticate(username=username, password=password)
                if not user is None:
                    self.cleaned_data['user'] = user
                    return self.cleaned_data
            raise forms.ValidationError("用户名或密码不正确")
        else:
            self.cleaned_data['user'] = user

        #这个是这个函数所要求要返回的数据
        return self.cleaned_data


class RegForm(forms.Form):
    username = forms.CharField(label='用户名',
                               max_length=30,
                               min_length=3,
                               widget=forms.TextInput(
                                            attrs={'class':'form-control', 'placeholder':'请输入3-30位用户名'}))

    email = forms.EmailField(label='邮箱',
                            widget=forms.EmailInput(
                                        attrs={'class': 'form-control', 'placeholder': '请输入邮箱'}))

    verification_code = forms.CharField(label='验证码',
                                        required=False,
                                        widget=forms.TextInput(
                                            attrs={'class': 'form-control', 'placeholder': '请输入收到的验证码'}))

    password = forms.CharField(label='密码',
                               min_length=6,
                               widget=forms.PasswordInput(
                                            attrs={'class': 'form-control', 'placeholder': '请输入密码'}))

    password_again = forms.CharField(label='再输入一次密码',
                                     min_length=6,
                                     widget=forms.PasswordInput(
                                                  attrs={'class': 'form-control', 'placeholder': '请再输入一次密码'}))

    def __init__(self, *args, **kwargs):
        if 'request' in kwargs:
            self.request = kwargs.pop('request')
        super(RegForm, self).__init__(*args, **kwargs)


    def clean(self):
        #判断验证码,第一个是从seesion中取,另一个是页面输入的
        code = self.request.session.get('register_code', '')
        verification_code = self.cleaned_data.get('verification_code', '')
        if not (code != '' and code == verification_code):
            raise forms.ValidationError('验证码不正确')

        return self.cleaned_data


    #我们可以统一在clean中做验证，也可以分别对需要验证的字段做验证，分别做的好处就是清晰明了
    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('用户名已存在')
        return username


    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('邮箱已存在')
        return email

    def clean_password_again(self):
        password = self.cleaned_data['password']
        password_again = self.cleaned_data['password_again']
        if password != password_again:
            raise forms.ValidationError('两次输出的密码不一致')
        return password_again

    def clean_verification_code(self):
        verification_code = self.cleaned_data.get('verification_code', '').strip()
        if verification_code == '':
            raise forms.ValidationError('验证码不能为空')
        return verification_code


class ChangeNicknameForm(forms.Form):
    nickname_new = forms.CharField(label='新的昵称',
                                   max_length=20,
                                   widget=forms.TextInput(
                                                attrs={'class':'form-control', 'placeholder':'请输入新的昵称'}))


    def __init__(self, *args, **kwargs):
        if 'user' in kwargs:
            self.user = kwargs.pop('user')
        super(ChangeNicknameForm, self).__init__(*args, **kwargs)


    def clean(self):
        if self.user.is_authenticated:
            self.cleaned_data['user'] = self.user
        else:
            raise forms.ValidationError('用户尚未登录')
        return self.cleaned_data


    def clean_nickname_new(self):
        nickname_new = self.cleaned_data.get('nickname_new', '').strip()
        if nickname_new == '':
            raise forms.ValidationError('新的昵称不能为空')
        return nickname_new


class BindEmailForm(forms.Form):
    email = forms.EmailField(label='绑定邮箱',
                             widget=forms.EmailInput(
                                          attrs={'class': 'form-control', 'placeholder': '请输入邮箱地址'}))

    verification_code = forms.CharField(label='验证码',
                                        required=False,
                                        widget=forms.TextInput(
                                                     attrs={'class':'form-control', 'placeholder':'请输入收到的验证码'}))


    def __init__(self, *args, **kwargs):
        if 'request' in kwargs:
            self.request = kwargs.pop('request')
        super(BindEmailForm, self).__init__(*args, **kwargs)


    def clean(self):
        if self.request.user.is_authenticated:
            self.cleaned_data['user'] = self.request.user
        else:
            raise forms.ValidationError('用户尚未登录')

        #判断用户是否已绑定邮箱
        if self.request.user.email != '':
            raise forms.ValidationError('你已经绑定邮箱')

        #判断验证码,第一个是从seesion中取,另一个是页面输入的
        code = self.request.session.get('bind_email_code', '')
        verification_code = self.cleaned_data.get('verification_code', '')
        if not (code != '' and code == verification_code):
            raise forms.ValidationError('验证码不正确')

        return self.cleaned_data


    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('邮箱已被绑定')
        return email


    def clean_verification_code(self):
        verification_code = self.cleaned_data.get('verification_code', '').strip()
        if verification_code == '':
            raise forms.ValidationError('验证码不能为空')
        return verification_code


class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(
        label='旧的密码',
        widget=forms.PasswordInput(
            attrs={'class': 'form-control', 'placeholder': '请输入旧的密码'}
        )
    )

    new_password = forms.CharField(
        label='新的密码',
        widget=forms.PasswordInput(
            attrs={'class': 'form-control', 'placeholder': '请输入新的密码'}
        )
    )

    new_password_again = forms.CharField(
        label='请输出新的密码',
        widget=forms.PasswordInput(
            attrs={'class': 'form-control', 'placeholder': '请再次输入新密码'}
        )
    )

    def __init__(self, *args, **kwargs):
        if 'user' in kwargs:
            self.user = kwargs.pop('user')
        super(ChangePasswordForm, self).__init__(*args, **kwargs)

    def clean(self):
        #验证两次输出的新密码是否一致
        new_password = self.cleaned_data.get('new_password', '')
        new_password_again = self.cleaned_data.get('new_password_again', '')
        if new_password != new_password_again or new_password == '':
            raise forms.ValidationError('两次输入的密码不一致')
        return self.cleaned_data

    def clean_old_password(self):
        #验证旧密码有没有输对
        old_password = self.cleaned_data.get('old_password', '')
        if not self.user.check_password(old_password):
            raise forms.ValidationError('旧的密码错误')
        return old_password


class ForgetPasswordForm(forms.Form):
    email = forms.EmailField(
        label='已绑定的邮箱',
        widget=forms.EmailInput(
            attrs={'class': 'form-control', 'placeholder': '请输入邮箱地址'}
        )
    )

    verification_code = forms.CharField(label='验证码',
                                        required=False,
                                        widget=forms.TextInput(
                                            attrs={'class': 'form-control', 'placeholder': '请输入收到的验证码'}))

    new_password = forms.CharField(
        label='新的密码',
        widget=forms.PasswordInput(
            attrs={'class': 'form-control', 'placeholder': '请输入新的密码'}
        )
    )

    def __init__(self, *args, **kwargs):
        if 'request' in kwargs:
            self.request = kwargs.pop('request')
        super(ForgetPasswordForm, self).__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError('邮箱不存在')
        return email

    def clean_verification_code(self):
        #判断验证码是否为空
        verification_code = self.cleaned_data.get('verification_code', '').strip()
        if verification_code == '':
            raise forms.ValidationError('验证码不能为空')

        # 判断验证码是否相等
        code = self.request.session.get('forget_password_code', '')
        verification_code = self.cleaned_data.get('verification_code', '')
        if not (code != '' and code == verification_code):
            raise forms.ValidationError('验证码不正确')

        return verification_code

