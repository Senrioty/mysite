"""
Django settings for mysite project.

Generated by 'django-admin startproject' using Django 2.0.13.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import os
from .base import *

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = 'n-a^tj6m8rx2b-04&g*l@56r*t_rr+3*==+yzy8xkwppq_#0-i'

SECRET_KEY = 'n-a^tj6m8rx2b-04&g*l@56r*t_rr+3*==+yzy8xkwppq_#0-i'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['*']  #写服务器ip地址，或者偷懒点写*

# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases
DATABASE_PASSWORD = os.environ['DATABASE_PASSWORD']
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': '127.0.0.1',
        'NAME': 'mysite_db',
        'USER': 'root',
        'PASSWORD': DATABASE_PASSWORD,
        'PORT': '3306'}
}

#发送邮件设置
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.qq.com'
EMAIL_PORT = 465 #原来是25，但是很多服务器都禁用了25，阿里云改为465，还需要在阿里云服务器把465加入到安全组中
EMAIL_HOST_USER = '642340273@qq.com'
# EMAIL_HOST_PASSWORD = 'xdoclvkymuabbfhj'  #授权码
EMAIL_HOST_PASSWORD = os.environ['EMAIL_HOST_PASSWORD']  #授权码
EMAIL_SUBJECT_PREFIX = '[senrio的博客]'
# EMAIL_USE_TLS = True #与SMTP服务器通信时，是否启动TLS链接(安全链接)
EMAIL_USE_SSL = True #阿里云，需要改为SSL

# 需要配置管理员，给下面的日志发邮件用
ADMINS = (
    ('admin', '642340273@qq.com')
)

#日志文件
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/home/mysite_debug.log',
        },
        'mail_admins': {  # 有错误时发送邮件给站主
                'level': 'ERROR',
                'class': 'django.utils.log.AdminEmailHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}