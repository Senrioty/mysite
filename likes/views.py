from django.shortcuts import render
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from django.db.models import ObjectDoesNotExist
from .models import LikeCount,LikeRecord


#封装点赞/取消点赞成功信息
def SuccessResponse(liked_num):
    data = {}
    data['status'] = 'SUCCESS'
    data['liked_num'] = liked_num
    return JsonResponse(data)


#封装错误信息
def ErrorResponse(code, message):
    data = {}
    data['status'] = 'ERROR'
    data['code'] = code
    data['message'] = message
    return JsonResponse(data)


def like_change(request):

    #获取用户数据并检验
    user = request.user
    if not user.is_authenticated:
        return ErrorResponse(400, 'you were not login')


    #获取GET请求中的数据
    content_type = request.GET.get('content_type')  #这里获取的是字符串类型
    content_type = ContentType.objects.get(model=content_type) #这里才转为ContentType对象
    object_id = int(request.GET.get('object_id')) #要转为int数值类型

    #检验model_obj是否存在
    try:
        model_class = content_type.model_class()  #这是获取到大写的那个类，如Blog
        model_obj = model_class.objects.get(pk=object_id) #获取实例
    except ObjectDoesNotExist:
        return ErrorResponse(401, 'object not exist')

    is_like = request.GET.get('is_like')

    #处理数据
    if is_like == 'true':
        #要点赞
        #get_or_created()方法:返回一个由(object, created)组成的元组，元组中的object 是一个查询到的或者是被创建的对象， created 是一个表示是否创建了新的对象的布尔值
        like_record, created = LikeRecord.objects.get_or_create(content_type=content_type, object_id=object_id, user=user)
        if created:
            #未点过赞，进行点赞，并保存数据
            like_count, created = LikeCount.objects.get_or_create(content_type=content_type,object_id=object_id)
            like_count.liked_num += 1
            like_count.save()
            return SuccessResponse(like_count.liked_num)
        else:
            #已点过赞，不能重复点赞（有可能是前端页面连点2下），这个错误情况，但是我们不能再前端页面进行处理，后端都要进行逻辑处理
            return ErrorResponse(402, 'you were liked')
    else:
        #要取消点赞
        if LikeRecord.objects.filter(content_type=content_type, object_id=object_id, user=user).exists():
            #有点赞过，取消点赞
            like_record = LikeRecord.objects.get(content_type=content_type, object_id=object_id, user=user)
            like_record.delete()

            #点赞总数减1
            like_count, created = LikeCount.objects.get_or_create(content_type=content_type, object_id=object_id)
            if not created:
                like_count.liked_num -= 1
                like_count.save()
                return SuccessResponse(like_count.liked_num)
            else:
                #这种就是数据错误情况，你要取消点赞，有关系数据，但是没有点赞数据，那肯定是数据有问题
                return ErrorResponse(404, 'data error')
        else:
            #没有点赞过，不能取消，这里同样可能是连点2次取消点赞的情况引发的逻辑
            return ErrorResponse(402, 'you were liked')