from django.shortcuts import render_to_response,get_object_or_404,render
from django.conf import settings
from django.db.models import Count
from django.core.paginator import Paginator
from django.contrib.contenttypes.models import ContentType

from .models import BlogType,Blog
from read_statistics.utils import read_statistics_once_read
from user.forms import LoginForm
from comment.models import Comment
from comment.forms import CommentForm


# Create your views here.
def get_blog_list_common_data(request,blogs_all_list):
    paginator = Paginator(blogs_all_list, settings.EACH_PAGE_BLOGS_NUMBER)  # 每7页进行分页
    page_num = request.GET.get("page", 1)  # 获取GET请求中page的值，默认为1

    # 为了获取页面的值，并且django提供了get_page方法可以防止页面为负数或者大于总分页数的情况（因为page的值可以人为在网页中输入）
    page_of_blogs = paginator.get_page(page_num)

    current_page_num = page_of_blogs.number  # 获取当前页码

    # 获取当前页码前后各2页的页面范围
    page_range = list(range(max(current_page_num - 2, 1), current_page_num)) + \
                 list(range(current_page_num, min(current_page_num + 2, paginator.num_pages) + 1))  # 加1是因为range右区间取不到

    # 加上省略号
    if page_range[0] - 1 >= 2:
        page_range.insert(0, '...')
    if paginator.num_pages - page_range[-1] >= 2:
        page_range.append('...')

    # 加上首页和尾页
    if page_range[0] != 1:
        page_range.insert(0, 1)
    if page_range[-1] != paginator.num_pages:
        page_range.append(paginator.num_pages)

    #获取博客分类的对应博客数量
    #第一种方式,相当于临时为BlogType加了一个blog_count属性，并用一个列表保存
    #原理就是先把数据从数据库中取出来，然后给页面使用
    '''
    blog_types = BlogType.objects.all()
    blog_types_list = []
    for blog_type in blog_types:
        blog_type.blog_count = Blog.objects.filter(blog_type = blog_type).count()
        blog_types_list.append(blog_type)

    '''
    #第二种方式，永annotate关联关系，blog是关联对象的小写首字母Blog,并且用
    #blog_count参数来接收统计数量，Count是聚合函数
    #原理是当页面需要的时候才会从数据库中取数据，不事先取
    blog_types = BlogType.objects.annotate(blog_count = Count('blog'))


    #获取日期归档对应
    #方式跟归档分类第一种类似
    blog_dates = Blog.objects.dates('created_time', 'month', order="DESC")
    blog_dates_dict = {}
    for blog_date in blog_dates:
        blog_count = Blog.objects.filter(created_time__year=blog_date.year, created_time__month=blog_date.month).count()
        blog_dates_dict[blog_date] = blog_count

    context = {}
    context['blogs'] = page_of_blogs.object_list
    context['page_of_blogs'] = page_of_blogs
    context['page_range'] = page_range
    context['blog_types'] = blog_types
    context['blog_dates'] = blog_dates_dict
    return context


def blog_list(request):

    blogs_all_list = Blog.objects.all()
    context = get_blog_list_common_data(request,blogs_all_list)
    #这也是一种算出总数的方法，或者直接在前端用过滤器对象|lengh
    #context['blogs_count'] = Blog.objects.all().count()

    return render(request,'blog/blog_list.html', context)


def blogs_with_type(request, blog_type_pk):
    blog_type = get_object_or_404(BlogType, pk=blog_type_pk)
    blogs_all_list = Blog.objects.filter(blog_type=blog_type)
    context = get_blog_list_common_data(request,blogs_all_list)
    context['blog_type'] = blog_type
    return render(request,'blog/blogs_with_type.html', context)


def blogs_with_date(request, year, month):
    blogs_all_list = Blog.objects.filter(created_time__year=year,created_time__month=month)
    context = get_blog_list_common_data(request,blogs_all_list)
    context['blogs_with_date'] = '%s年%s月' % (year, month)
    return render(request,'blog/blogs_with_date.html', context)


def blog_detail(request, blog_pk):
    blog = get_object_or_404(Blog, pk=blog_pk)
    read_cookie_key = read_statistics_once_read(request, blog)

    #获取评论数据
    #因为用自定义模板标签了，可以优化掉了
    # blog_content_type = ContentType.objects.get_for_model(blog)
    # comments = Comment.objects.filter(content_type=blog_content_type, object_id=blog.pk, parent=None)


    '''
    if not request.COOKIES.get('blog_%s_readed' % blog_pk):
        #方式一：如果count为0就是false，不为0的话就是true
        
        if ReadNum.objects.filter(blog = blog).count():
            #存在记录
            readnum = ReadNum.objects.get(blog = blog)

        else:
            #不存在记录
            readnum = ReadNum(blog=blog)
        #计数加1
        readnum.read_num += 1
        readnum.save()
        

        #方式二：
        
        ct = ContentType.objects.get_for_model(Blog)
        if ReadNum.objects.filter(content_type=ct, object_id=blog.pk).count():
            #存在记录
            readnum = ReadNum.objects.get(content_type=ct, object_id=blog.pk)
        else:
            #不存在记录
            readnum = ReadNum(content_type=ct, object_id=blog.pk)
        #计数加1
        readnum.read_num +=1
        readnum.save()
    '''

    context = {}
    context['previous_blog'] = Blog.objects.filter(created_time__gt=blog.created_time).last()
    context['next_blog'] = Blog.objects.filter(created_time__lt=blog.created_time).first()
    context['blog'] = blog
    # context['login_form'] = LoginForm()  通过自定义默认模板引入了

    #同理，用自定义模板标签优化，不用传comments
    # context['comments'] = comments.order_by('-comment_time')

    #initial是对表单的字段进行初始化操作
    #blog_content_type获取的是blog对象，但是content_type在表单定义是一个字符串，所以用.model转为字符串
    #引入模板标签后可以不用通过blog去传comment_form，因为这样耦合度高，我们不想在blog中去写过多的关于comment的东西
    #context['comment_form'] = CommentForm(initial={'content_type':blog_content_type.model, 'object_id':blog_pk, 'reply_comment_id':'0'})

    #获取评论数的方式一（方式二是使用自定义模板标签）
    #context['comments_count'] = Comment.objects.filter(content_type=blog_content_type, object_id=blog.pk).count()

    #写法二：使用render,直接返回request，前端页面可以直接使用user，原理是django的机制，在setting中默认模板就已经返回了user,所以可以直接使用，推荐
    response = render(request, 'blog/blog_detail.html', context)

    # 返回系统用户的写法
    # 写法一：使用render_to_response，通过request.user来获取用户，但是会有局限性
    #context['user'] = request.user
    #response = render_to_response('blog/blog_detail.html', context)

    response.set_cookie(read_cookie_key, 'true')  #阅读cookie标记
    return response
