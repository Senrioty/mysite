from django.contrib.contenttypes.models import ContentType
from django.db.models import Sum
from django.utils import timezone
from .models import ReadNum,ReadDetail


def read_statistics_once_read(request, obj):
    ct = ContentType.objects.get_for_model(obj)
    key = "%s_%s_read" % (ct.model, obj.pk)
    if not request.COOKIES.get(key):
        '''
        #用if-else来判断对象是否存在的方法
        if ReadNum.objects.filter(content_type=ct, object_id=obj.pk).count():
            # 存在记录
            readnum = ReadNum.objects.get(content_type=ct, object_id=obj.pk)
        else:
            # 不存在记录
            readnum = ReadNum(content_type=ct, object_id=obj.pk)
       
        '''

        #用django里的方法get_or_create的方式，如果没有对象会新建
        readnum, created = ReadNum.objects.get_or_create(content_type=ct, object_id=obj.pk)

        # 计数加1
        readnum.read_num += 1
        readnum.save()

        #处理read_detail的逻辑
        date = timezone.now().date()
        #同理这里也可以用上面那种方式创建对象
        '''
        if ReadDetail.objects.filter(content_type=ct, object_id=obj.pk, date=date):
            readDetail = ReadDetail.objects.get(content_type=ct, object_id=obj.pk, date=date)
        else:
            readDetail = ReadDetail(content_type=ct, object_id=obj.pk, date=date) #实例化对象
      
        '''

        #当天阅读数+1
        readDetail, created = ReadDetail.objects.get_or_create(content_type=ct, object_id=obj.pk, date=date)
        readDetail.read_num += 1
        readDetail.save()
    return key


def get_seven_days_read_data(content_type):
    today = timezone.now().date()
    dates = []
    read_nums = []
    #range()第一个参数是开始的，第二个参数是结束，最后一个参数是步进
    for i in range(7, 0, -1):
        date = today - timezone.timedelta(i)
        dates.append(date.strftime('%m/%d'))  #strftime是时间的格式化函数
        read_detail = ReadDetail.objects.filter(content_type=content_type, date=date)
        #调用后会返回一个由名称－值配对组成的字典
        result = read_detail.aggregate(read_num_sum = Sum('read_num'))
        read_nums.append(result['read_num_sum'] or 0)
    return dates, read_nums


def get_today_hot_data(content_type):
    today = timezone.now().date()
    #-read_num中-号表示倒序
    read_details = ReadDetail.objects.filter(content_type=content_type, date=today).order_by('-read_num')
    return read_details[:7]


def get_yesterday_hot_data(content_type):
    today = timezone.now().date()
    yesterday = today - timezone.timedelta(days=1)
    read_detail = ReadDetail.objects.filter(content_type=content_type, date=yesterday).order_by('-read_num')

    #类似limit 或者写成[0:7]也ok
    return read_detail[0:7]


def get_7_days_hot_data(content_type):
    today = timezone.now().date()
    date = today - timezone.timedelta(days=7)

    #values是返回一个字典，但是我们此处没有返回，所以前端没法返回content_object,所以对应对象的属性拿不到，而annotate是类似聚合的概念
    read_detail = ReadDetail.objects\
                            .filter(content_type=content_type, date__lt=today, date__gte=date)\
                            .values('content_type', 'object_id') \
                            .annotate(read_num_sum=Sum('read_num')) \
                            .order_by('-read_num')
    return read_detail[:7]