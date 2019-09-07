from django.shortcuts import render
from django.contrib.contenttypes.fields import ContentType
from django.utils import timezone
from django.db.models import Sum
from django.core.cache import cache

from read_statistics.utils import get_seven_days_read_data,get_today_hot_data,get_yesterday_hot_data,get_7_days_hot_data
from blog.models import Blog


#这种方式来反向获取对应blog对象，注意引用方式为 read_details__反向对象的属性
def get_7_days_hot_blogs():
    today = timezone.now().date()
    date = today - timezone.timedelta(days=7)
    blogs = Blog.objects\
                .filter(read_details__date__lt=today, read_details__date__gte=date) \
                .values('id','title') \
                .annotate(read_num_sum=Sum('read_details__read_num')) \
                .order_by('-read_num_sum')
    return blogs[:7]


def home(request):
    context = {}
    blog_content_type = ContentType.objects.get_for_model(Blog)
    dates, read_nums = get_seven_days_read_data(blog_content_type)

    #获取热门数据
    today_hot_data = get_today_hot_data(blog_content_type)
    yesterday_hot_data = get_yesterday_hot_data(blog_content_type)

    #这种方式除了id不能获取对应对象的属性
    #hot_data_for_7_days = get_7_days_hot_data(blog_content_type)

    #获取7天热门博客的缓存数据
    #cache.get(key) 如果没有数据则返回None
    #cache.set(key,value,存在的时间（秒为单位）)
    hot_blogs_for_7_days = cache.get('hot_blogs_for_7_days')
    if hot_blogs_for_7_days is None:
        hot_blogs_for_7_days = get_7_days_hot_blogs()
        cache.set('hot_blogs_for_7_days', hot_blogs_for_7_days, 3600)  #此处是3600s,一个小时
        print('calc')
    else:
        print('use cache')


    context['read_nums'] = read_nums
    context['dates'] = dates
    context['today_hot_data'] = today_hot_data
    context['yesterday_hot_data'] = yesterday_hot_data
    context['hot_blogs_for_7_days'] = get_7_days_hot_blogs()
    return render(request,'home.html', context)


def my_notifications(request):
    context = {}
    return render(request, 'my_notificaitons.html', context)
