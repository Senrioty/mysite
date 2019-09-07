from django.shortcuts import render,redirect
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.utils.html import strip_tags
from notifications.signals import notify
from .models import Comment
from comment.forms import CommentForm

# Create your views here.
def update_comment(request):
    '''
    #这是使用html表单验证的代码
    # 重定向操作，也就是说提交评论后应该还是在此评论页，但是数据做了更新
    referer = request.META.get('HTTP_REFERER', reverse('home'))

    #数据检查
    user = request.user
    if not user.is_authenticated:
        #redirect_to 是让错误页面可以有个返回的链接
        return render(request, 'error.html', {'message':'用户未登录', 'redirect_to':referer})

    text = request.POST.get('text', '').strip()   #去空格
    #要在后端做评论内容的判断，因为前端不论再怎么保障，都不可信
    if text == '':
        return render(request, 'error.html', {'message':'评论内容不能为空', 'redirect_to':referer})

    #用异常处理来判断评论对象到底有没有
    try:
        content_type = request.POST.get('content_type', '')
        object_id = int(request.POST.get('object_id', ''))  #因为从POST请求中获取的都是字符串类型，所以要通过int()转为数值类型

        #通过get方法获取到类型，但我们需要获取到大写的类名，所以再引用.model_class()
        #models_class 在此处可以认为是 BLog
        model_class = ContentType.objects.get(model=content_type).model_class()

        # 等价于blog = Blog.objects.get(pk=object_id)，只不过我们写得更加通用，万一不是blog类型也可以使用
        model_obj = model_class.objects.get(pk=object_id)
    except Exception as e:
        return render(request, 'error.html', {'message':'评论对象不存在', 'redirect_to':referer})


    #检查通过，保存数据
    comment = Comment()
    comment.user = user
    comment.text = text
    comment.content_object = model_obj
    comment.save()

    return redirect(referer)
    '''

    '''
    这是使用django form表单的代码
    '''
    referer = request.META.get('HTTP_REFERER', reverse('home'))

    #由于CommentForm没有request，所以要通过实例化表单对象的时候，使用关键字传参把user对象传递给表单
    comment_form = CommentForm(request.POST, user=request.user)

    data = {}
    if comment_form.is_valid():
        comment = Comment()

        #虽然可以像html表单一样对user对验证，但是我们使用form后，应该在表单里做验证，而不是在views里
        comment.user = comment_form.cleaned_data['user']
        comment.text = comment_form.cleaned_data['text'] #从cleaned_data获取
        comment.content_object = comment_form.cleaned_data['content_object']

        #表单字段的数据检查在forms中完成，这里新增判断是否是属于子评论还是主评论,因为保存的数据不一样
        parent = comment_form.cleaned_data['parent']

        #如果parent有数据
        #看下面逻辑前，先解释下parent和root的区别
        #parent就是字面意思评论的直接父节点，没有没有父节点，parent为None，有父节点，那parent就是指向直接父节点
        #root是该评论的根节点，如果是主评论，那root为None,只要是这个根节点下所有评论，这个root都指向这个根节点，如1-2，1-3,1-2-1,1-3-1,1-3-2 的root都是1
        if not parent is None:

            comment.root = parent.root if not parent.root is None else parent
            comment.parent = parent
            comment.reply_to = parent.user

        comment.save()

        # 发送邮件给被评论或者被回复的用户
        # 方式一:使用同步的方式，等邮件发送完后才执行后续的ajax
        if comment.parent is None:
            subject = '有人评论了你的博客'
            email = comment.content_object.get_email()

            # 因为我们要返回给一个链接，点开后是博客详情页，我们可以直接写地址，但是用reverse来反查地址更好
            # 由于blog_detail的url需要传一个参数

            # 第一种做法是传一个args，是一个list
            # text = comment.text + '\n' + reverse('blog_detail', args=[comment.content_object.pk])

            #第二种做法是，关键字传参，是个dict,其中key是url中写的
            # text = comment.text + '\n' + reverse('blog_detail', kwargs={'blog_pk':comment.content_object.pk})

            #第三种做法是,这个链接应该是由content_object来得到，所以要在Blog模型中新增一个get_url的方法，符合封装
            #由于是公共部分，所以都提出去了
            text = comment.text + '\n' + comment.content_object.get_url()

        else:
            subject = '有人回复了你的评论'
            email = comment.reply_to.email

        if email != '':
            text = comment.text + '\n' + comment.content_object.get_url()
            # send_mail(subject, text, settings.EMAIL_HOST_USER, [email], fail_silently=False)

        # # 方式二:使用异步来发送邮件  同样可以放到signals中
        # comment.send_email()


        # # 发送站内消息 (第一种方式) # 第二种方式是用signals
        # if comment.reply_to is None:
        #     # 评论
        #     recipient = comment.content_object.get_user()
        #     if comment.content_type.model == 'blog':
        #         blog = comment.content_object
        #         verb = '{0}评论了你的博客《{1}》'.format(comment.user.get_nickname_or_username(), blog.title)
        #     else:
        #         raise Exception('unkown comment object type')
        # else:
        #     # 回复,其中strip_tags是为了去除html标签
        #     recipient = comment.reply_to
        #     verb = '{0}回复了你的评论“{1}”'.format(comment.user.get_nickname_or_username(), strip_tags(comment.parent.text))
        #
        # # 参数分别表示的意思是：通知者，接收者，接受内容，这个消息是从哪个地方出发的
        # notify.send(comment.user, recipient=recipient, verb=verb, action_object=comment)


        # 未使用ajax提交的代码
        # return redirect(referer)

        # 使用ajax提交的代码
        data['status'] = 'SUCCESS'
        data['username'] = comment.user.get_nickname_or_username()
        # 如果使用下面这个方式，那setting文件中要修改 USE_TZ = False ，然后前端不用拼html时不要调用 时间函数
        data['comment_time'] = comment.comment_time.strftime('%Y-%m-%d %H:%M:%S')
        # data['comment_time'] = comment.comment_time.timestamp()
        data['text'] = comment.text
        data['content_type'] = ContentType.objects.get_for_model(comment).model

        #返回数据也要新增数据
        if not parent is None:
            data['reply_to'] = comment.reply_to.get_nickname_or_username()
        else:
            data['reply_to'] = ''

        data['pk'] = comment.pk
        data['root_pk'] = comment.root.pk if not comment.root is None else ''


    else:
        # 未使用ajax提交的代码
        # return render(request, 'error.html', {'message':comment_form.errors, 'redirect_to':referer}) #返回表单的错误信息errors

        # 使用ajax提交的代码
        data['status'] = 'ERROR'

        # dict.values()是返回字典中所有的值，因为comment_form.errors是个字典，然后我们转为列表，只取第一个错误信息,第二次取[0]是因为还是个数组，再从数组中取出真正的错误信息
        data['message'] = list(comment_form.errors.values())[0][0]
    return JsonResponse(data)
